# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_version_added.py

Brief: test(s) for correct detection of "Version Added".
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from .discrepancy_list import DiscrepancyList

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

    'output_format': 'markdown',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_added_output_AccountService(mockRequest):
    """ Verify markdown output contains expected version_added info. """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_added', 'AccountService'))

    expected_version_strings = [ '**LDAP** *(v1.3+)*', '**LDAPService** {',
                                 '**LocalAccountAuth** *(v1.3+)*',
                                 '**PrivilegeMap** *(v1.1+)*', '**Actions** *(v1.2+)*'
                                 ]


    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    discrepancies = DiscrepancyList()

    for expected in expected_version_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_version_added_output_Chassis(mockRequest):
    """ Verify markdown output contains expected version_added info.

    The Chassis example gave us some distinct scenarios.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'version_added', 'Chassis'))

    expected_version_strings = ['| **Actions** { |', '| **Links** { |',  # string to match property without version
                                '**PowerState** *(v1.1+)*']


    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    discrepancies = DiscrepancyList()

    for expected in expected_version_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies
