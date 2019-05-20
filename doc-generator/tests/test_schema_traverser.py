# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

import unittest
import schema_traverser
from .simple_schema import simple_schema

class TestSchemaTraverser(unittest.TestCase):

    def setUp(self):
        """Build a SchemaTraverser with a limited schema"""
        self.schemaTraverser = schema_traverser.SchemaTraverser(simple_schema, {})

    def test_find_ref_data(self):
        ref_data = self.schemaTraverser.find_ref_data('Resource#/definitions/Oem')
        expected_vals = {
            '_from_schema_ref': 'Resource',
            "type": "object",
            "description": "Oem extension object.",
            "longDescription": "This object represents the Oem properties.  All values for resources described by this schema shall comply to the requirements as described in the Redfish specification.",
            }
        for key in expected_vals.keys():
            self.assertEqual(ref_data[key], expected_vals[key])


    def test_find_bad_ref_returns_None(self):
        ref_data = self.schemaTraverser.find_ref_data('Resource#/definitions/NoSuchThing')
        self.assertIsNone(ref_data)


    def test_parse_relative_ref(self):
        self.assertEqual(self.schemaTraverser.parse_ref('#/definitions/Fan', 'Thermal'),
                         'Thermal#/definitions/Fan')


    def test_parse_absolute_ref(self):
        self.assertEqual(self.schemaTraverser.parse_ref(
            'http://redfish.dmtf.org/schemas/v1/Resource.json#/definitions/Oem', 'Thermal'),
                         'Resource#/definitions/Oem')


if __name__ == '__main__':
    unittest.main()
