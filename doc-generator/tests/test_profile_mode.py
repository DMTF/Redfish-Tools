# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_profile_mode.py

Brief: Tests for profile mode.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'profile_mode')

base_config = {
    'expand_defs_from_non_output_schemas': False,
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},
    'escape_chars': [],
    'profile_mode': 'terse',
    'output_format': 'markdown',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_profile_basic_full (mockRequest):

    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'basic', 'NetworkPort'))
    profile_dir = os.path.abspath(os.path.join(testcase_path, 'basic', 'profiles'))
    profile_json = os.path.abspath(os.path.join(profile_dir, 'BasicInstanceProfile.v1_0_0.json'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['profile_doc'] = profile_json
    config['profile_uri_to_local'] = { 'redfish.dmtf.org/profiles': profile_dir }

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # We'll split the doc by the level 5 (?) headings, which are the headings for conditional reqs.
    # Then we'll check for the expected rows of markdown by property.
    header_marker = '\n##### '
    chunks = output.split(header_marker)
    expected_props = {
        'Description': '| "Name" is Equal to "Fred" | Mandatory (Read), must be AnyOf "A very good dog", "A good cat" |',
        'Ethernet': '| "FibreChannel" is Absent | Mandatory (Read) | If no FibreChannel, Ethernet must be implemented. |',
        'FibreChannel': '| "Name" is Equal to "Fred" | Mandatory (Read/Write) | Show that FibreChannel must be readable and writeable if the device\'s name is Fred. |',
                      }
    condreq_output = {}
    for x in expected_props.keys():
        chunk = [c for c in chunks if c.startswith(x + '\n')]
        assert len(chunk) > 0, "Conditional Requirements not output for " + x
        assert len(chunk) < 2, "Conditional Requirements has multiple headings for " + x
        if len(chunk) == 1:
            condreq_output[x] = chunk[0]

    for name, expected_description in expected_props.items():
        assert expected_description in  condreq_output.get(name, '')
