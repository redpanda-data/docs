'use strict'

module.exports.register = function () {
  this.on('documentsConverted', ({ contentCatalog }) => {
    const targets = [
      '/connect/components/inputs/postgres_cdc/',
      '/connect/components/inputs/kafka/',
    ]
    contentCatalog.getPages((p) => p.pub && targets.includes(p.pub.url)).forEach((page) => {
      const attrs = page.asciidoc?.attributes || {}
      const pageAttrs = Object.keys(attrs).filter((k) => k.startsWith('page-'))
      console.log(`[debug-page-attrs] ${page.pub.url}`)
      console.log(`  page-* keys: ${JSON.stringify(pageAttrs)}`)
      console.log(`  page-context-switcher: ${attrs['page-context-switcher']}`)
      console.log(`  page-cloud-available: ${attrs['page-cloud-available']}`)
    })
  })
}
