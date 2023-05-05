'use strict'

const $glossaryContexts = Symbol('$glossaryContexts')
const { posix: path } = require('path')

module.exports.register = function (registry, config = {}) {

  const vfs = adaptVfs()

  function adaptVfs () {
    function getKey (src) {
      return `${src.version}@${src.component}`
    }

    if (config.vfs && typeof config.vfs.getConfig === 'function') {
      return config.vfs
    } else if (config.file && config.contentCatalog && typeof config.contentCatalog.resolveResource === 'function') {
      //Antora support
      const contentCatalog = config.contentCatalog
      if (!contentCatalog[$glossaryContexts]) contentCatalog[$glossaryContexts] = {}
      const glossaryContexts = contentCatalog[$glossaryContexts]
      const key = getKey(config.file.src)
      if (!glossaryContexts[key]) {
        glossaryContexts[key] = {
          gloss: [],
          self: undefined,
          dlist: undefined,
        }
      }
      const context = glossaryContexts[key]
      return {
        getContext: () => context,
      }
    } else {
      const context = {
        gloss: [],
        self: undefined,
        dlist: undefined,
      }
      return {
        getContext: () => context,
      }
    }
  }
  //characters to replace by '_' in generated idprefix
  const IDRX = /[/ _.-]+/g

  function termId (term) {
    return '_glossterm_' + term.toLowerCase().replace(IDRX, '_')
  }

  function dlistItem (context, term, def) {
    const id = termId(term)
    term = `anchor:${id}[${term}]${term}`
    const termItem = context.self.createListItem(context.dlist, term)
    const defItem = context.self.createListItem(context.dlist, def)
    return [[termItem], defItem]
  }

  function glossaryBlockMacro () {
    return function () {
      const self = this
      self.named('glossary')
      self.$option('format', 'short') //no target between glossary:: and [params]
      // self.positionalAttributes(['name', 'parameters'])
      self.process(function (parent, target, attributes) {
        const context = vfs.getContext()
        const dlist = self.createList(parent, 'dlist')
        context.self = self
        context.dlist = dlist
        context.gloss
          .forEach(({ term, def }) => {
            dlist.blocks.push(dlistItem(context, term, def))
          })
        return dlist
      })
    }
  }

  const TRX = /(<[a-z]+)([^>]*>.*)/

  function glossaryInlineMacro () {
    return function () {
      const self = this
      self.named('glossterm')
      //Specifying the regexp allows spaces in the term.
      self.$option('regexp', /glossterm:([^[]+)\[(|.*?[^\\])\]/)
      self.positionalAttributes(['definition'])
      self.process(function (parent, target, attributes) {
        const term = attributes.term || target
        const document = parent.document
        const context = vfs.getContext()
        // See if a predefined list of terms is available
        const termsList = document.getAttribute("terms")
        const termData = termsList.find((t) => t.term === term) || {};
        const customLink = termData.link;
        var tooltip = document.getAttribute('glossary-tooltip')
        if (tooltip === 'true') tooltip = 'data-glossary-tooltip'
        if (tooltip && tooltip !== 'title' && !tooltip.startsWith('data-')) {
          console.log(`glossary-tooltip attribute '${tooltip}' must be 'true', 'title', or start with 'data-`)
          tooltip = undefined
        }
        const logTerms = document.hasAttribute('glossary-log-terms')
        var definition = termData.definition || attributes.definition
        if (definition) {
          logTerms && console.log(`${term}::  ${definition}`)
          addItem(context, term, definition)
        } else if (tooltip) {
          const index = context.gloss.findIndex((candidate) => candidate.term === term)
          definition = ~index ? context.gloss[index].def : `${term} not yet defined`
        }
        const links = document.getAttribute('glossary-links', 'true') === 'true'
        var glossaryPage = document.getAttribute('glossary-page', '')
        if (glossaryPage.endsWith('.adoc')) {
          const page = config.contentCatalog.resolvePage(glossaryPage, config.file.src)
          const relativizedPath = path.relative(path.dirname(config.file.pub.url), page.pub.url)
          const prefix = attributes.prefix
          glossaryPage = prefix ? [prefix, relativizedPath].join('/') : relativizedPath
        }
        const glossaryTermRole = document.getAttribute('glossary-term-role', 'glossary-term')
        const attrs = glossaryTermRole ? { role: glossaryTermRole } : {}
        const inline = links
          ? customLink
            ? self.createInline(parent, 'anchor', target, { type: 'link', target: customLink, attributes: attrs })
            : self.createInline(parent, 'anchor', target, { type: 'xref', target: `${glossaryPage}#${termId(term)}`, reftext: target, attributes: attrs })
          : self.createInline(parent, 'quoted', target, { attributes: attrs })
        if (tooltip) {
          const a = inline.convert()
          const matches = a.match(TRX)
          if (matches) {
            return self.createInline(parent, 'quoted', `${matches[1]} ${tooltip}="${definition}"${matches[2]}`)
          } else {
            return self.createInline(parent, 'quoted', `<span ${tooltip}="${definition}">${a}</span>`)
          }
        }
        return inline
      })
    }
  }

  function addItem (context, term, def) {
    let i = 0
    let comp = -1
    for (; i < context.gloss.length && ((comp = term.localeCompare(context.gloss[i].term)) > 0); i++) {
    }
    if (comp < 0) {
      context.gloss.splice(i, 0, { term, def })
      if (context.self && context.dlist) {
        context.dlist.blocks.splice(i, 0, dlistItem(context, term, def))
      }
    } else {
      console.log(`duplicate glossary term ${term}`)
    }
  }

  function doRegister (registry) {
    if (typeof registry.blockMacro === 'function') {
      registry.blockMacro(glossaryBlockMacro())
    } else {
      console.warn('no \'blockMacro\' method on alleged registry')
    }
    if (typeof registry.inlineMacro === 'function') {
      registry.inlineMacro(glossaryInlineMacro())
    } else {
      console.warn('no \'inlineMacro\' method on alleged registry')
    }
  }

  if (typeof registry.register === 'function') {
    registry.register(function () {
      //Capture the global registry so processors can register more extensions.
      registry = this
      doRegister(registry)
    })
  } else {
    doRegister(registry)
  }
  return registry
}
