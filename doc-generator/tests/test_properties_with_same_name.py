# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_combine_properties_with_same_name.py

Brief: Verify that properties with the same name, within different objects in the same schema,
       and defined as references to distinct definitions, are properly identified, with
       both properties expanded in the Property details section.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'properties_with_same_name')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'excluded_pattern_props': [r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'],
    'schema_link_replacements': {},
    'wants_common_objects': True,
    'profile': {},
    'escape_chars': [],
    'output_format': 'slate',
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_properties_with_same_name_md(mockRequest):
    """ Tests an example schema with two properties with the same name """
    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'manager'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    prop_details = docGen.generator.this_section.get('property_details', {})
    # Property details should have been collected for the following (and only these):
    expected_prop_details = ['ConnectTypesSupported', 'ManagerType', 'PowerState', 'ResetType']
    found_prop_details = [x for x in prop_details.keys()]
    found_prop_details.sort()
    assert found_prop_details == expected_prop_details

    # The following number of definitions should be captured for each:
    assert len(prop_details['ResetType'].keys()) == 2
    assert len(prop_details['ConnectTypesSupported'].keys()) == 3
    assert len(prop_details['ManagerType'].keys()) == 1
    assert len(prop_details['PowerState'].keys()) == 1

    # Spot-check the output as well. These are the headings that should appear for ConnectTypesSupported:
    assert "### ConnectTypesSupported" in output
    assert "In CommandShell:" in output
    assert "In GraphicalConsole:" in output
    assert "In SerialConsole:" in output
