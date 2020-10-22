# Copyright Notice:
# Copyright 2018-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_version_order.py

Brief: test(s) for correct order of versions detected from "unversioned" json.

Usually an unversioned file lists versions in incremental order (in an anyOf list), but
this order is not required. In the version_order example, an errata version 1_0_2 is listed
after the latest version, 1_1_1. 1_1_1 should still be detected as the latest version.
"""

import os
import os.path
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'uri_replacements': {},

    'profile': {},
    'escape_chars': [],

    'output_format': 'slate',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_order(mockRequest):
    """ Verify correct order is determined from the unversioned json data, which provides
    versions out of order.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_order'));

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    grouped_files, schema_data = docGen.group_files(files_to_process)

    # Check order of grouped_files. (We don't care about the order of files_to_process.)
    cos_group = grouped_files['redfish.dmtf.org/schemas/v1/ClassOfService.json']
    cos_filenames = [x['filename'] for x in cos_group]
    assert cos_filenames == ['ClassOfService.v1_0_0.json', 'ClassOfService.v1_0_1.json',
                             'ClassOfService.v1_0_2.json', 'ClassOfService.v1_1_0.json', 'ClassOfService.v1_1_1.json']
