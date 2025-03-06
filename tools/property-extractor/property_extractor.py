#!/usr/bin/env python3
import logging
import sys
import os
import json
import re

from pathlib import Path
from file_pair import FilePair
from tree_sitter import Language, Parser

from parser import build_treesitter_cpp_library, extract_properties_from_file_pair
from property_bag import PropertyBag
from transformers import *

logger = logging.getLogger("viewer")


def validate_paths(options):
    path = options.path

    if not os.path.exists(path):
        logger.error(f'Path does not exist: "{path}".')
        sys.exit(1)

    if options.definitions and not os.path.exists(options.definitions):
        logger.error(
            f'File with the type definitions not found: "{options.definitions}".'
        )
        sys.exit(1)


def get_file_pairs(options):
    path = Path(options.path)

    file_iter = path.rglob("*.h") if options.recursive else path.rglob("*.h")

    file_pairs = []

    for i in file_iter:
        if os.path.exists(i.with_suffix(".cc")):
            file_pairs.append(FilePair(i.resolve(), i.with_suffix(".cc").resolve()))

    return file_pairs


def get_treesitter_cpp_parser_and_language(treesitter_dir, destination_path):
    if not os.path.exists(destination_path):
        build_treesitter_cpp_library(treesitter_dir, destination_path)

    cpp = Language(destination_path, "cpp")

    parser = Parser()
    parser.set_language(cpp)

    return parser, cpp


def get_files_with_properties(file_pairs, treesitter_parser, cpp_language):
    files_with_properties = []

    for fp in file_pairs:
        properties = extract_properties_from_file_pair(
            treesitter_parser, cpp_language, fp
        )
        implementation_value = str(fp.implementation)

        # List of file paths to check
        file_paths = [
            "src/v/config/configuration.cc",
            "src/v/config/node_config.cc",
            "src/v/kafka/client/configuration.cc",
            "src/v/pandaproxy/rest/configuration.cc",
            "src/v/pandaproxy/schema_registry/configuration.cc"
        ]

        # Check if any of the paths are in fp.implementation
        if any(path in implementation_value for path in file_paths):
            if len(properties) > 0:
                files_with_properties.append((fp, properties))
                logging.info(f"Properties found in '{fp.implementation}'.")

    

    return files_with_properties


def transform_files_with_properties(files_with_properties):
    type_transformer = TypeTransformer()
    transformers = [
        EnterpriseTransformer(), ## this must be the first, as it modifies current data
        MetaParamTransformer(),
        BasicInfoTransformer(),
        type_transformer,
        IsNullableTransformer(),
        IsArrayTransformer(type_transformer),
        NeedsRestartTransformer(),
        VisibilityTransformer(),
        DeprecatedTransformer(),
        IsSecretTransformer(),
        NumericBoundsTransformer(type_transformer),
        DurationBoundsTransformer(type_transformer),
        SimpleDefaultValuesTransformer(),
        FriendlyDefaultTransformer(),
        ExperimentalTransformer(),
        AliasTransformer(),
    ]

    all_properties = PropertyBag()

    for fp, properties in files_with_properties:
        for name in properties:
            # ignore private properties
            if re.match(r"^_", name):
                continue

            property_definition = PropertyBag()

            for transformer in transformers:
                if transformer.accepts(properties[name], fp):
                    transformer.parse(property_definition, properties[name], fp)

            if len(property_definition) > 0:
                all_properties[name] = property_definition

    return all_properties


# The definitions.json file contains type definitions that the extractor uses to standardize and centralize type information. After extracting and transforming the properties from the source code, the function merge_properties_and_definitions looks up each property's type in the definitions. If a property's type (or the type of its items, in the case of arrays) matches one of the definitions, the transformer replaces that type with a JSON pointer ( such as #/definitions/<type>) to the corresponding entry in definitions.json. The final JSON output then includes both a properties section (with types now referencing the definitions) and a definitions section, so that consumers of the output can easily resolve the full type information.
def merge_properties_and_definitions(properties, definitions):
    for name in properties:
        property = properties[name]

        if property["type"] in definitions:
            properties[name]["type"] = "#/definitions/" + property["type"]
        elif property["type"] == "array" and property["items"]["type"] in definitions:
            properties[name]["items"]["type"] = (
                "#/definitions/" + property["items"]["type"]
            )

    return dict(properties=properties, definitions=definitions)


def main():
    import argparse

    def generate_options():
        arg_parser = argparse.ArgumentParser(
            description="Extract all properties from the Redpanda's source code and generate a JSON output with their definitions"
        )
        arg_parser.add_argument(
            "--path",
            type=str,
            required=True,
            help="Path to the Redpanda's source dir to extract the properties",
        )

        arg_parser.add_argument(
            "--recursive", action="store_true", help="Scan the path recursively"
        )

        arg_parser.add_argument(
            "--output",
            type=str,
            required=False,
            help="File to store the JSON output. If no file is provided, the JSON will be printed to the standard output",
        )

        arg_parser.add_argument(
            "--definitions",
            type=str,
            required=False,
            default=os.path.dirname(os.path.realpath(__file__)) + "/definitions.json",
            help='JSON file with the type definitions. This file will be merged in the output under the "definitions" field',
        )

        arg_parser.add_argument("-v", "--verbose", action="store_true")

        return arg_parser

    arg_parser = generate_options()
    options, _ = arg_parser.parse_known_args()

    if options.verbose:
        logging.basicConfig(level="DEBUG")
    else:
        logging.basicConfig(level="INFO")

    validate_paths(options)

    file_pairs = get_file_pairs(options)

    if not file_pairs:
        logging.error("No h/cc file pairs were found")
        sys.exit(-1)

    definitions = None

    if options.definitions:
        with open(options.definitions) as json_file:
            definitions = json.load(json_file)

    treesitter_dir = os.path.join(os.getcwd(), "tree-sitter/tree-sitter-cpp")
    destination_path = os.path.join(treesitter_dir, "tree-sitter-cpp.so")

    if not os.path.exists(os.path.join(treesitter_dir, "src/parser.c")):
        logging.error("Missing parser.c. Ensure Tree-sitter submodules are initialized.")
        sys.exit(1)

    treesitter_parser, cpp_language = get_treesitter_cpp_parser_and_language(
        treesitter_dir, destination_path
    )

    files_with_properties = get_files_with_properties(
        file_pairs, treesitter_parser, cpp_language
    )
    properties = transform_files_with_properties(files_with_properties)
    properties_and_definitions = merge_properties_and_definitions(
        properties, definitions
    )

    json_output = json.dumps(properties_and_definitions, indent=4, sort_keys=True)

    if options.output:
        with open(options.output, "w+") as json_file:
            json_file.write(json_output)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
