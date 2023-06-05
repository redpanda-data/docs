/* Example use in a page
*
* config_ref:myConfigValue,true,tunable-properties[]
*
* Example use in playbook
*
* asciidoc:
    extensions:
    - './macros/config-ref.js'
*/

const buildConfigReference = ({ configRef, isKubernetes, isLink, path }) => {
  let ref = '';
  if (isLink) {
    if (isKubernetes) {
      ref = `xref:reference:${path}.adoc#${configRef}[storage.tieredConfig.${configRef}]`;
    } else {
      ref = `xref:reference:${path}.adoc#${configRef}[${configRef}]`;
    }
  } else {
    ref = isKubernetes ? `storage.tieredConfig.${configRef}` : `${configRef}`;
  }
  return ref;
}

function inlineConfigMacro(context) {
  return function () {
    this.process((parent, target, attrs) => {
      const [configRef, isLink, path] = target.split(',');
      const isKubernetes = parent.getDocument().getAttributes()['env-kubernetes'] !== undefined;
      const content = buildConfigReference({ configRef, isKubernetes, isLink: isLink === 'true', path });
      return this.createInline(parent, 'quoted', content);
    });
  }
}

function register (registry, context) {
  registry.inlineMacro('config_ref', inlineConfigMacro(context));
}

module.exports.register = register;


