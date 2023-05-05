'use strict'

/**
 * Create a JSON file called cloud.json with a summary of the pages
 *
 * Example use in the playbook
 * antora:
     extensions:
  *    - require: ./extensions/cloud-docs.js
        tags:
          - Favorites
          - Videos
          - Get Started
          - Whitepapers
          - Use cases
          - Case studies
          - Documentation
          - Develop Applications
          - Manage Accounts
          - Manage Clusters
        data:
          - title:
            url: https://www.youtube.com/
            type: video
            order: 7
            tags: Videos, Get Started
 */


module.exports.register = function ({config}) {
    let content = []
    const addEntity = ({title, url, tags, type, order}) => {
        const arr = tags.split(',').map(cat => cat.trim())
        if (config.tags && !arr.some(name => (config.tags ?? []).includes(name))) {
            throw Error(`Wrong cloud tag '${name}'`)
        }
        content.push({
            title: title && title.trim(),
            url: url && url.trim(),
            tags: arr,
            type: type && type.trim(),
            order: order ? parseInt(order) : 0
        })
    }
    (config.data ?? []).forEach(item => addEntity(item))
    this.on('documentsConverted', ({contentCatalog}) => {
        contentCatalog.findBy({family: 'page'}).forEach((item) => {
            const urlVideo = item.asciidoc.attributes['cloud-url-video']
            const type = urlVideo ? 'video' : 'article'
            const url = urlVideo ?? item.pub.url
            const tags = item.asciidoc.attributes['cloud-tags']
            const title = item.asciidoc.attributes['cloud-title'] ?? item.title
            const order = item.asciidoc.attributes['cloud-order']
            if (tags) {
                if (title.includes('|')) {
                    title.split('|').forEach((title_multi, index) => {
                        const tags_multi = item.asciidoc.attributes['cloud-tags'].split('|')[index]
                        const order_multi = item.asciidoc.attributes['cloud-order'] ? item.asciidoc.attributes['cloud-order'].split('|')[index] : ''
                        const anchor_multi = item.asciidoc.attributes['cloud-anchor'] ? item.asciidoc.attributes['cloud-anchor'].split('|')[index] : ''
                        const url_multi = item.asciidoc.attributes['cloud-url-video'] ? item.asciidoc.attributes['cloud-url-video'].split('|')[index] : item.pub.url
                        addEntity({
                            title: title_multi ?? item.title,
                            url: url_multi + (!!anchor_multi ? `#${anchor_multi.trim()}` : ''),
                            tags: tags_multi,
                            type,
                            order: order_multi ?? 0
                        })
                    })
                } else {
                    addEntity({
                        title,
                        url,
                        tags,
                        type,
                        order
                    })
                }
            }
        })
    })
        .on('beforePublish', ({siteCatalog}) => {
            siteCatalog.addFile({
                contents: Buffer.from(JSON.stringify({
                    tags: config.tags ?? [],
                    links: content.sort((a, b) => a.order - b.order)
                })),
                out: {path: config.path ?? 'api/cloud.json'}
            })
        })
}