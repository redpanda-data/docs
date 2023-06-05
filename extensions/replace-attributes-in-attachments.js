module.exports.register = function ({ config }) {
  const { family = 'attachment' } = config
  const logger = this.getLogger('attributes-in-attachments-extension')
  this
    .on('documentsConverted', ({contentCatalog}) => {
      contentCatalog.getComponents().forEach(({ versions }) => {
        versions.forEach(({ name: component, version}) => {
          const attachments = contentCatalog
            .findBy({ component, version, family: family })
            if (component === 'ROOT') {
              attachments.filter((attachment) => {
                let string = String.fromCharCode.apply(null, attachment['_contents'])
                const attributes = attachment.src.origin.descriptor.asciidoc.attributes
                for (let key in attributes) {
                  let placeholder = "{" + key + "}";
                  string = string.replace(new RegExp(placeholder, 'g'), attributes[key]);
                }
                let newBuffer = Buffer.from(string, "utf-8");
                attachment['_contents'] = newBuffer;
              })
            }
        })
      })
    })
}