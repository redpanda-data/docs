/* Example use in a page
*
* helm_ref:myConfigValue[]
*
* Example use in playbook
*
* asciidoc:
    extensions:
    - './macros/helm-ref.js'
*/

const buildConfigReference = ({ helmRef }) => {
  let ref = '';
  ref = helmRef ? `For default values and documentation for configuration options, see the https://artifacthub.io/packages/helm/redpanda-data/redpanda?modal=values&path=${helmRef}[values.yaml] file.` : `For default values and documentation for configuration options, see the https://artifacthub.io/packages/helm/redpanda-data/redpanda?modal=values[values.yaml] file.`;
  return ref;
}

function inlineConfigMacro(context) {
  return function () {
    this.process((parent, target, attrs) => {
      const [helmRef] = target.split(',');
      const content = buildConfigReference({ helmRef });
      return this.createInline(parent, 'quoted', content);
    });
  }
}

function register (registry, context) {
  registry.inlineMacro('helm_ref', inlineConfigMacro(context));
}

module.exports.register = register;


