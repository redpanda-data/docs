import unittest
from property_bag import PropertyBag
from file_pair import FilePair
from transformers import *


def create_property_info(
    name,
    description,
    declaration=None,
    metadata=None,
    default_value="{}",
    default_value_type="initializer_list",
):
    info = PropertyBag()
    info["name_in_file"] = name
    info["declaration"] = declaration
    info["params"] = []
    info["params"].append(PropertyBag(value=name, type="string_literal"))
    info["params"].append(PropertyBag(value=description, type="string_literal"))
    info["params"].append(PropertyBag(value=metadata, type="initializer_list"))
    info["params"].append(PropertyBag(value=default_value, type="initializer_list"))

    return info


class BasicInfoTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = BasicInfoTransformer()

    def test_accepts_everything(self):
        self.assertTrue(self.transformer.accepts(None, None))

    def test_adds_name_description_and_defined_in(self):
        property = PropertyBag()
        info = create_property_info("test_property", "test description")
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertEqual("test_property", property["name"])
        self.assertEqual("test description", property["description"])
        self.assertEqual("testfile.cc", property["defined_in"])


class IsArrayTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = IsArrayTransformer(TypeTransformer())

    def test_accepts_vector(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property", "test description", "std::vector<int>"
                ),
                None,
            )
        )

    def test_rejects_other_properties(self):
        for t in [
            "int",
            "std::optional",
            "config::endpoint_tls_config",
            "deprecated_property",
        ]:
            with self.subTest(t):
                self.assertFalse(
                    self.transformer.accepts(
                        create_property_info("test_property", "test description", t),
                        None,
                    )
                )

    def test_adds_array_field(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property", "test description", "std::vector<int>"
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertEqual("array", property["type"])
        self.assertEqual("integer", property["items"]["type"])


class NeedsRestartTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = NeedsRestartTransformer()

    def test_accepts_needs_restart_metadata(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(needs_restart="needs_restart::no"),
                ),
                None,
            )
        )
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(needs_restart="needs_restart::yes"),
                ),
                None,
            )
        )

    def test_rejects_without_needs_restart(self):
        self.assertFalse(
            self.transformer.accepts(
                create_property_info(
                    "test_property", "test description", "bool", PropertyBag()
                ),
                None,
            )
        )

    def test_adds_needs_restart_true(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "std::vector<int>",
            PropertyBag(needs_restart="needs_restart::yes"),
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertTrue(property["needs_restart"])

    def test_adds_needs_restart_false(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "std::vector<int>",
            PropertyBag(needs_restart="needs_restart::no"),
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertFalse(property["needs_restart"])


class VisibilityTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = VisibilityTransformer()

    def test_accepts_visibility_metadata(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(visibility="visibility::user"),
                ),
                None,
            )
        )

    def test_rejects_without_visibility(self):
        self.assertFalse(
            self.transformer.accepts(
                create_property_info(
                    "test_property", "test description", "bool", PropertyBag()
                ),
                None,
            )
        )

    def test_adds_visibility(self):
        for p in [
            ("user", "visibility::user"),
            ("tunable", "visibility::tunable"),
            ("deprecated", "visibility::deprecated"),
        ]:
            with self.subTest(p[0]):
                property = PropertyBag()
                info = create_property_info(
                    "test_property",
                    "test description",
                    "std::vector<int>",
                    PropertyBag(visibility=p[1]),
                )
                self.transformer.parse(
                    property, info, FilePair("testfile.h", "testfile.cc")
                )

                self.assertEqual(p[0], property["visibility"])


class TypeTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = TypeTransformer()

    def test_accepts_everything(self):
        self.assertTrue(self.transformer.accepts(None, None))

    def test_parse_simple_types(self):
        types = [
            ("int", "integer"),
            ("int32_t", "integer"),
            ("int16_t", "integer"),
            ("int64_t", "integer"),
            ("double", "number"),
            ("bool", "boolean"),
            ("std::chrono::milliseconds", "integer"),
            ("std::chrono::seconds", "integer"),
            ("std::filesystem::path", "string"),
        ]

        for t in types:
            with self.subTest(t[0]):
                property = PropertyBag()
                info = create_property_info(
                    "test_property",
                    "test description",
                    "property<" + t[0] + ">" + " test_property;",
                )
                self.transformer.parse(
                    property, info, FilePair("testfile.h", "testfile.cc")
                )

                self.assertEqual(t[1], property["type"])

    def test_parse_bounded_property(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "bounded_property<double, numeric_bounds> disk_reservation_percent;",
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertEqual("number", property["type"])

    def test_parse_deprecated_property(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property", "test description", "deprecated_property test_property;"
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertEqual("deprecated_property", property["type"])


class DeprecatedTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = DeprecatedTransformer()

    def test_accepts_deprecated_visibility(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(visibility="visibility::deprecated"),
                ),
                None,
            )
        )

    def test_accepts_deprecated_property_type(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "deprecated_property",
                    PropertyBag(),
                ),
                None,
            )
        )

    def test_rejects_without_deprecated_visibility_type(self):
        self.assertFalse(
            self.transformer.accepts(
                create_property_info(
                    "test_property", "test description", "bool", PropertyBag()
                ),
                None,
            )
        )

    def test_adds_deprecated_field_from_deprecated_visibility(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "std::vector<int>",
            PropertyBag(visibility="visibility::deprecated"),
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertTrue(property["is_deprecated"])
        self.assertFalse(property["type"])

    def test_adds_deprecated_field_from_deprecated_property_type(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property", "test description", "deprecated_property", PropertyBag()
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))

        self.assertTrue(property["is_deprecated"])
        self.assertFalse(property["type"])


class IsSecretTransformerTestCase(unittest.TestCase):
    def setUp(self):
        self.transformer = IsSecretTransformer()

    def test_accepts_with_secret(self):
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(secret="is_secret::yes"),
                ),
                None,
            )
        )
        self.assertTrue(
            self.transformer.accepts(
                create_property_info(
                    "test_property",
                    "test description",
                    "bool",
                    PropertyBag(secret="is_secret::no"),
                ),
                None,
            )
        )

    def test_rejects_without_secret(self):
        self.assertFalse(
            self.transformer.accepts(
                create_property_info(
                    "test_property", "test description", "bool", PropertyBag()
                ),
                None,
            )
        )

    def test_adds_is_secret_true(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "std::vector<int>",
            PropertyBag(secret="is_secret::yes"),
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))
        self.assertTrue(property["is_secret"])

    def test_adds_is_secret_false(self):
        property = PropertyBag()
        info = create_property_info(
            "test_property",
            "test description",
            "std::vector<int>",
            PropertyBag(secret="is_secret::no"),
        )
        self.transformer.parse(property, info, FilePair("testfile.h", "testfile.cc"))
        self.assertFalse(property["is_secret"])


if __name__ == "__main__":
    unittest.main()
