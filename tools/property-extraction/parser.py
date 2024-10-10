from file_pair import FilePair
from tree_sitter import Language
from property_bag import PropertyBag
from copy import deepcopy
import itertools as it
import re

# Temp
import sys

HEADER_QUERY = """
(field_declaration
    type: (_) @type
    (#match? @type ".*property.*")
    declarator: (_) @name
) @declaration
"""

SOURCE_QUERY = """
(field_initializer_list
    (field_initializer
        (field_identifier) @field
        (argument_list (_) @argument)? @arguments
    ) @field
)
"""

INITIALIZER_LIST_QUERY = """
(initializer_list
  (initializer_pair
    designator: (_
      (field_identifier) @name)
    value: (_) @value
))
"""

MAX_INITIALIZER_LIST_DEPTH = 10


def get_file_contents(path):
    contents = ""

    with open(path, "rb") as f:
        contents = f.read()

    return contents


def parse_cpp_header(treesitter_parser, cpp_language, source_code):
    query = cpp_language.query(HEADER_QUERY)
    tree = treesitter_parser.parse(source_code)

    captures = query.captures(tree.root_node)
    properties = PropertyBag()

    current_declaration = None
    current_type = None

    for i in captures:
        node = i[0]
        if node.type == "field_identifier":
            property_name = node.text.decode("utf-8")

            properties[property_name]["name_in_file"] = property_name
            properties[property_name]["type"] = current_type
            properties[property_name]["declaration"] = current_declaration

            current_declaration = None
            current_type = None
        elif node.type == "template_type":
            current_type = node.text.decode("utf-8")
        elif node.type == "field_declaration":
            current_declaration = node.text.decode("utf-8")

    return properties


def __unquote_string(value):
    # placeholder to keep escaped double quotes (e.g. \"name\")
    escaped_quotes_placeholder = "$$$___quote___$$$"
    return re.sub(
        r'^R?"([^"]*)"\s*$',
        "\\1",
        re.sub(
            '\\\\"',
            escaped_quotes_placeholder,
            value.strip().replace('\\\\"', escaped_quotes_placeholder),
        ),
    ).replace(escaped_quotes_placeholder, '"')


def normalize_string(value):
    return __unquote_string(value)


def __normalize_concatenated_string(value):
    return "".join(
        __unquote_string(s)
        for s in it.filterfalse(lambda r: re.search("^//", r), value.split("\n"))
    )


def __normalize_initializer_list(
    value, node, treesitter_parser, cpp_language, source_code
):
    query = cpp_language.query(INITIALIZER_LIST_QUERY)
    tree = treesitter_parser.parse(source_code)

    captures = query.captures(
        tree.root_node, start_point=node.start_point, end_point=node.end_point
    )

    if len(captures) == 0:
        return value.replace("\n", "")

    current_field = None
    fields = PropertyBag()
    for c in captures:
        list_node = c[0]
        capture_label = c[1]

        if capture_label == "name":
            current_field = list_node.text.decode("utf-8")
        else:
            param = dict(value=list_node.text.decode("utf-8"), type=list_node.type)
            fields[current_field] = (
                __normalize_param(
                    param, list_node, treesitter_parser, cpp_language, source_code
                )["value"]
                if current_field
                else node.text.decode("utf-8")
            )
            current_field = None

    return fields


def __normalize_param(param, node, treesitter_parser, cpp_language, source_code):
    if param["type"] == "comment":
        return

    if param["type"] == "string_literal" or param["type"] == "raw_string_literal":
        param["value"] = normalize_string(param["value"])
    elif param["type"] == "concatenated_string":
        param["value"] = __normalize_concatenated_string(param["value"])
        param["type"] = "string_literal"
    elif param["type"] == "initializer_list":
        param["value"] = __normalize_initializer_list(
            param["value"], node, treesitter_parser, cpp_language, source_code
        )
    else:
        param["value"] = param["value"].replace("\n", "")

    return param


def parse_cpp_source(treesitter_parser, cpp_language, source_code):
    query = cpp_language.query(SOURCE_QUERY)
    tree = treesitter_parser.parse(source_code)

    captures = query.captures(tree.root_node)

    current_parameter = None
    state = "read_field"

    parameters = PropertyBag()

    for i in captures:
        node = i[0]
        if node.type == "field_initializer":
            state = "read_field"

        if state == "read_field" or node.type == "field_identifier":
            if node.type != "field_identifier":
                continue
            current_parameter = node.text.decode("utf-8")
            parameters[current_parameter] = PropertyBag()
            parameters[current_parameter]["params"] = []
            state = "skip_until_pointer"
        elif state == "skip_until_pointer":
            if node.type != "pointer_expression":
                continue
            state = "read_parameters"
        elif state == "read_parameters":
            param = dict(value=node.text.decode("utf-8"), type=node.type)
            normalized_param = __normalize_param(
                param, node, treesitter_parser, cpp_language, source_code
            )

            if normalized_param:
                parameters[current_parameter]["params"].append(normalized_param)

    return parameters


def __merge_header_and_source_properties(header_properties, source_properties):
    properties = deepcopy(header_properties)

    for key in header_properties.keys():
        if key in source_properties:
            properties[key].update(source_properties[key])
        else:
            return PropertyBag()

    return properties


def extract_properties_from_file_pair(
    treesitter_parser, cpp_language, file_pair: FilePair
):
    header_properties = parse_cpp_header(
        treesitter_parser, cpp_language, get_file_contents(file_pair.header)
    )

    if len(header_properties) == 0:
        return PropertyBag()

    source_properties = parse_cpp_source(
        treesitter_parser, cpp_language, get_file_contents(file_pair.implementation)
    )

    if len(source_properties) == 0:
        return PropertyBag()

    return __merge_header_and_source_properties(header_properties, source_properties)


def build_treesitter_cpp_library(src_dir, destination_path):
    Language.build_library(destination_path, [src_dir])
