// The 'module.exports' is used to export this module, so it can be processed by Antora.
module.exports.register = function (registry) {
  // The 'registry.blockMacro' function is used to register a new custom macro.
  // A macro is a special syntax in AsciiDoc that can trigger a block of custom behavior.
  // In this case, we're creating a macro called 'hello'.
  registry.blockMacro('hello', function () {
    // The 'this.process' function defines what happens when the 'hello' macro is used.
    // It takes a 'parent', 'target', and 'attrs' as arguments.
    // - 'parent' is the parent block that contains this macro.
    // - 'target' is the value or argument that the user passes after the 'hello' macro.
    // - 'attrs' is an object containing any attributes the user passes to the macro (though we're not using this here).
    this.process(function (parent, target, attrs) {
      // The 'this.createBlock' method is used to create a new block of content.
      // - 'parent' is the block parent block where this new block will be inserted. Parent is the block where the macro appears in the document.
      // - 'paragraph' specifies that the new block is a paragraph block.
      // - 'Hello, ' + target + '!' creates the content of the paragraph.
      // The final result is a paragraph that says "Hello, [target]!" where [target] is the user-provided value.
      return this.createBlock(parent, 'paragraph', 'Hello, ' + target + '!');
    });
  });
};
