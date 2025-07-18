'use strict'

const connect = require('gulp-connect')
const fs = require('fs')
const path = require('path')
const generator = require('@antora/site-generator')
const { reload: livereload } = process.env.LIVERELOAD === 'true' ? require('gulp-connect') : {}
const { series, src, watch } = require('gulp')
const yaml = require('js-yaml')

// Ultra-fast dev mode setup
const isDev = true  // Always dev mode in this file
const playbookFilename = 'local-dev-playbook.yml'

// Aggressive console suppression for maximum speed
const originalConsole = { log: console.log, warn: console.warn, error: console.error }
let buildInProgress = false

// Download and cache UI bundle once
async function ensureUIBundle() {
  const uiBundlePath = path.resolve('./ui-bundle.zip')
  
  // Check if file exists and is valid (more than 1KB)
  const isValidBundle = () => {
    try {
      if (!fs.existsSync(uiBundlePath)) return false
      const stats = fs.statSync(uiBundlePath)
      return stats.size > 1024 // Must be larger than 1KB
    } catch {
      return false
    }
  }
  
  if (!isValidBundle()) {
    // Remove any corrupted file
    try {
      if (fs.existsSync(uiBundlePath)) {
        fs.unlinkSync(uiBundlePath)
      }
    } catch {}
    
    // Only show download message if not in build progress (first time only)
    if (!buildInProgress) {
      originalConsole.log('📦 Downloading UI bundle for caching...')
    }
    
    try {
      const https = require('https')
      const file = fs.createWriteStream(uiBundlePath)
      
      await new Promise((resolve, reject) => {
        const request = https.get('https://github.com/redpanda-data/docs-ui/releases/latest/download/ui-bundle.zip', (response) => {
          // Handle redirects
          if (response.statusCode === 302 || response.statusCode === 301) {
            https.get(response.headers.location, (redirectResponse) => {
              redirectResponse.pipe(file)
              file.on('finish', () => {
                file.close()
                // Validate the downloaded file
                if (isValidBundle()) {
                  if (!buildInProgress) {
                    originalConsole.log('✅ UI bundle downloaded and cached')
                  }
                  resolve()
                } else {
                  // Delete invalid file
                  fs.unlink(uiBundlePath, () => {})
                  reject(new Error('Downloaded bundle is invalid'))
                }
              })
            }).on('error', reject)
          } else {
            response.pipe(file)
            file.on('finish', () => {
              file.close()
              // Validate the downloaded file
              if (isValidBundle()) {
                if (!buildInProgress) {
                  originalConsole.log('✅ UI bundle downloaded and cached')
                }
                resolve()
              } else {
                // Delete invalid file
                fs.unlink(uiBundlePath, () => {})
                reject(new Error('Downloaded bundle is invalid'))
              }
            })
          }
        })
        
        request.on('error', reject)
        
        request.setTimeout(30000, () => {
          request.destroy()
          fs.unlink(uiBundlePath, () => {})
          reject(new Error('Download timeout'))
        })
      })
    } catch (err) {
      // Download failed, we'll use remote URL
      if (!buildInProgress) {
        originalConsole.log('⚠️ UI bundle download failed, using remote URL')
      }
    }
  }
}

// Completely suppress console output during builds for maximum speed
function suppressConsole() {
  console.log = console.warn = console.error = () => {}
}

function restoreConsole() {
  console.log = originalConsole.log
  console.warn = originalConsole.warn  
  console.error = originalConsole.error
}

const outputDir = './build/dev-site'
const serverConfig = { 
  name: 'Preview Site (Dev Mode)', 
  livereload, 
  port: 5002, 
  root: outputDir 
}

// Watch only critical files (based on what's actually in the playbook)
const watchPatterns = [
  './modules/**/*.adoc',  // Only watch get-started module
  './antora.yml',
  './local-dev-playbook.yml'
]

// Create cache directories
function ensureCacheDirectories() {
  const dirs = ['./.antora-cache', './.temp-cache', './.ui-cache', './build/dev-site']
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true })
    }
  })
}

async function generate(done) {
  const startTime = Date.now()
  
  try {
    // Suppress ALL console output during build
    buildInProgress = true
    suppressConsole()
    
    // Ensure cache directories exist (silently)
    ensureCacheDirectories()
    
    // Ensure UI bundle is cached (silently)
    await ensureUIBundle()
    
    const uiBundlePath = path.resolve('./ui-bundle.zip')
    
    // Check if we have a valid local bundle
    const hasValidBundle = () => {
      try {
        if (!fs.existsSync(uiBundlePath)) return false
        const stats = fs.statSync(uiBundlePath)
        return stats.size > 1024 // Must be larger than 1KB
      } catch {
        return false
      }
    }
    
    // Use the existing local-dev-playbook.yml and just modify the UI bundle URL
    const originalPlaybook = yaml.load(fs.readFileSync(playbookFilename, 'utf8'))
    const tempPlaybook = { ...originalPlaybook }
    
    // Update UI bundle URL if we have a valid local copy
    if (hasValidBundle()) {
      tempPlaybook.ui.bundle.url = uiBundlePath
    }
    
    // Write temporary playbook
    const tempPlaybookPath = './temp-dev-playbook.yml'
    fs.writeFileSync(tempPlaybookPath, yaml.dump(tempPlaybook))
    
    // Generate with ultra-aggressive settings
    const tempAntoraArgs = [
      '--playbook', tempPlaybookPath,
      '--log-level', 'silent',
      '--cache-dir', './.antora-cache',
      '--url', 'http://localhost:5002',
      '--to-dir', './build/dev-site'
      // Don't use --fetch to avoid external downloads
    ]
    
    await generator(tempAntoraArgs, {
      ...process.env,
      NODE_ENV: 'development',
      SKIP_EXTENSIONS: 'true',
      SKIP_VALIDATION: 'true',
      ANTORA_LOG_LEVEL: 'silent'
    })
    
    // Clean up temp playbook
    try {
      fs.unlinkSync(tempPlaybookPath)
    } catch {}
    
    buildInProgress = false
    restoreConsole()
    
    const buildTime = ((Date.now() - startTime) / 1000).toFixed(2)
    originalConsole.log(`⚡ Build complete in ${buildTime}s`)
    
    if (livereload) connect.reload()
    if (done && typeof done === 'function') done()
    
  } catch (err) {
    buildInProgress = false
    restoreConsole()
    originalConsole.error('❌ Build failed:', err.message)
    if (done && typeof done === 'function') done()
  }
}

let isFirstRun = true

async function serve(done) {
  connect.server(serverConfig, function () {
    this.server.on('close', done)
    
    // Direct watch without debouncing for immediate response
    watch(watchPatterns, (cb) => {
      generate(cb)
    })
    
    if (livereload) {
      watch(this.root).on('change', (filepath) => {
        src(filepath, { read: false }).pipe(livereload())
      })
    }
    
    if (isFirstRun) {
      import('open').then(open => {
        open.default(`http://localhost:${serverConfig.port}/`)
      })
      isFirstRun = false
    }
  })
}

module.exports = { serve, generate, default: series(generate, serve) }