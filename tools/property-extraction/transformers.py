import re
from property_bag import PropertyBag
from parser import normalize_string


class BasicInfoTransformer:
    def accepts(self, info, file_pair):
        return True

    def parse(self, property, info, file_pair):
        property["name"] = info["params"][0]["value"]
        property["defined_in"] = re.sub(
            r"^.*src/", "src/", str(file_pair.implementation)
        )
        property["description"] = (
            info["params"][1]["value"] if len(info["params"]) > 1 else None
        )


class IsNullableTransformer:
    def accepts(self, info, file_pair):
        return True

    def parse(self, property, info, file_pair):
        if len(info["params"]) > 2 and "required" in info["params"][2]["value"]:
            is_required = (
                re.sub(r"^.*::", "", info["params"][2]["value"]["required"]) == "yes"
            )
            property["nullable"] = not is_required
        elif "std::optional" in info["declaration"]:
            property["nullable"] = True
        else:
            property["nullable"] = False

        return property


class IsArrayTransformer:
    def __init__(self, type_transformer):
        self.type_transformer = type_transformer

    def accepts(self, info, file_pair):
        return "std::vector" in info["declaration"]

    def parse(self, property, info, file_pair):
        property["type"] = "array"
        property["items"] = PropertyBag()
        property["items"]["type"] = self.type_transformer.get_type_from_declaration(
            info["declaration"]
        )


class NeedsRestartTransformer:
    def accepts(self, info, file_pair):
        return (
            True
            if len(info["params"]) > 2 and "needs_restart" in info["params"][2]["value"]
            else False
        )

    def parse(self, property, info, file_pair):
        needs_restart = re.sub(
            r"^.*::", "", info["params"][2]["value"]["needs_restart"]
        )
        property["needs_restart"] = needs_restart == "yes"


class VisibilityTransformer:
    def accepts(self, info, file_pair):
        return (
            True
            if len(info["params"]) > 2 and "visibility" in info["params"][2]["value"]
            else False
        )

    def parse(self, property, info, file_pair):
        property["visibility"] = re.sub(
            r"^.*::", "", info["params"][2]["value"]["visibility"]
        )


class TypeTransformer:
    def accepts(self, info, file_pair):
        return True

    def get_cpp_type_from_declaration(self, declaration):
        one_line_declaration = declaration.replace("\n", "").strip()
        raw_type = (
            re.sub(r"^.*property<(.+)>.*", "\\1", one_line_declaration)
            .split()[0]
            .replace(",", "")
        )

        if "std::optional" in raw_type:
            raw_type = re.sub(".*std::optional<(.+)>.*", "\\1", raw_type)

        if "std::vector" in raw_type:
            raw_type = re.sub(".*std::vector<(.+)>.*", "\\1", raw_type)

        return raw_type

    def get_type_from_declaration(self, declaration):
        raw_type = self.get_cpp_type_from_declaration(declaration)
        type_mapping = [  # (regex, type)
            ("^u(nsigned|int)", "integer"),
            ("^(int|(std::)?size_t)", "integer"),
            ("data_directory_path", "string"),
            ("filesystem::path", "string"),
            ("(double|float)", "number"),
            ("string", "string"),
            ("bool", "boolean"),
            ("vector<[^>]+string>", "string[]"),
            ("std::chrono", "integer"),
        ]

        for m in type_mapping:
            if re.search(m[0], raw_type):
                return m[1]

        return raw_type

    def parse(self, property, info, file_pair):
        property["type"] = self.get_type_from_declaration(info["declaration"])
        return property


class DeprecatedTransformer:
    def accepts(self, info, file_pair):
        return "deprecated_property" in info["declaration"] or (
            len(info["params"]) > 2
            and "visibility" in info["params"][2]["value"]
            and "deprecated" in info["params"][2]["value"]["visibility"]
        )

    def parse(self, property, info, file_pair):
        property["is_deprecated"] = True
        property["type"] = None


class IsSecretTransformer:
    def accepts(self, info, file_pair):
        return (
            True
            if len(info["params"]) > 2 and "secret" in info["params"][2]["value"]
            else False
        )

    def parse(self, property, info, file_pair):
        is_secret = re.sub(r"^.*::", "", info["params"][2]["value"]["secret"])

        property["is_secret"] = is_secret == "yes"


class NumericBoundsTransformer:
    def __init__(self, type_transformer):
        self.type_transformer = type_transformer

    def accepts(self, info, file_pair):
        type = self.type_transformer.get_cpp_type_from_declaration(info["declaration"])
        return re.search("^(unsigned|u?int(8|16|32|64)?(_t)?)", type)

    def parse(self, property, info, file_pair):
        type_mapping = dict(
            unsigned=(0, 2**32 - 1),
            uint8_t=(0, 2**8 - 1),
            uint16_t=(0, 2**16 - 1),
            uint32_t=(0, 2**32 - 1),
            uint64_t=(0, 2**64 - 1),
            int=(-(2**31), 2**31 - 1),
            int8_t=(-(2**7), 2**7 - 1),
            int16_t=(-(2**15), 2**15 - 1),
            int32_t=(-(2**31), 2**31 - 1),
            int64_t=(-(2**63), 2**63 - 1),
        )
        type = self.type_transformer.get_cpp_type_from_declaration(info["declaration"])

        if type in type_mapping:
            property["minimum"] = type_mapping[type][0]
            property["maximum"] = type_mapping[type][1]


class DurationBoundsTransformer:
    def __init__(self, type_transformer):
        self.type_transformer = type_transformer

    def accepts(self, info, file_pair):
        return re.search("std::chrono::", info["declaration"])

    def parse(self, property, info, file_pair):
        # sizes are based in the documentation: https://en.cppreference.com/w/cpp/chrono/duration
        type_mapping = dict(
            nanoseconds=(-(2**63), 2**63 - 1),  # int 64
            microseconds=(-(2**54), 2**54 - 1),  # int 55
            milliseconds=(-(2**44), 2**44 - 1),  # int 45
            seconds=(-(2**34), 2**34 - 1),  # int 35
            minutes=(-(2**28), 2**28 - 1),  # int 29
            hours=(-(2**22), 2**22 - 1),  # int 23
            days=(-(2**24), 2**24 - 1),  # int 25
            weeks=(-(2**21), 2**21 - 1),  # int 22
            months=(-(2**19), 2**19 - 1),  # int 20
            years=(-(2**16), 2**16 - 1),  # int 17
        )
        type = self.type_transformer.get_cpp_type_from_declaration(info["declaration"])
        duration_type = type.replace("std::chrono::", "")

        if duration_type in type_mapping:
            property["minimum"] = type_mapping[duration_type][0]
            property["maximum"] = type_mapping[duration_type][1]


class SimpleDefaultValuesTransformer:
    def accepts(self, info, file_pair):
        # the default value is the 4th param
        return info["params"] and len(info["params"]) > 3

    def parse(self, property, info, file_pair):
        default = info["params"][3]["value"]

        # handle simple cases
        if default == "std::nullopt":
            property["default"] = None
        elif default == "{}":
            pass
        elif isinstance(default, PropertyBag):
            property["default"] = default
        elif re.search("^-?[0-9][0-9']*$", default):  # integers
            property["default"] = int(default.replace("[^0-9-]", ""))
        elif re.search("^-?[0-9]+(\.[0-9]+)$", default):  # floats
            property["default"] = float(default.replace("[^0-9]", ""))
        elif re.search("^(true|false)$", default):  # booleans
            property["default"] = True if default == "true" else False
        elif re.search("^{[^:]+$", default):  # string lists
            property["default"] = [
                normalize_string(s)
                for s in re.sub("{([^}]+)}", "\\1", default).split(",")
            ]
        else:
            # file sizes
            matches = re.search("^([0-9]+)_(.)iB$", default)
            if matches:
                size = int(matches.group(1))
                unit = matches.group(2)
                if unit == "K":
                    size = size * 1024
                elif unit == "M":
                    size = size * 1024**2
                elif unit == "G":
                    size = size * 1024**3
                elif unit == "T":
                    size = size * 1024**4
                elif unit == "P":
                    size = size * 1024**5

                property["default"] = size
            elif re.search("^(https|/[^/])", default):  # urls and paths
                property["default"] = default
            else:
                # ignoring numbers (they are durations if they reached here), enums (::), or default initializations (e.g. tls_config())
                if not re.search("([0-9]|::|\\()", default):
                    property["default"] = default
                else:
                    # unhandled cases
                    property["default"] = default
