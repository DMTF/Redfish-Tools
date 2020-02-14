# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_combine_multiple_refs.py

Brief: Tests for the "combine multiple refs" setting. This setting specifies that multiple objects within
       a schema, that are defined by reference to the same definition, should have their definitions
       moved into the Property Details section, with a single-line (row) listing for each object in the
       main table. combine_multiple_refs is an integer threshhold at which this behavior kicks in. If it is
       absent or 0, no combining occurs. If it is 2 or greater, combining occurs at that number of references
       to the same object. A setting of 1 does not make sense and should be prevented.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'combine_multiple')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'excluded_pattern_props': [r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'],
    'uri_replacements': {},
    'wants_common_objects': True,
    'profile': {},
    'escape_chars': [],
    'output_format': 'markdown',
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_combine_not_set(mockRequest):
    """ The non-combine case; multiple refs to the same object appear multiple times. """
    config = copy.deepcopy(base_config)
    # config['combine_multiple_refs'] = 0

    input_dir = os.path.abspath(os.path.join(testcase_path, 'sensor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # The "Threshold" object is referred to six times, and is the only thing with a DwellTime attribute.
    assert output.count('DwellTime') == 6


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_combine_at_3(mockRequest):
    """ Threshhold is set at 3. This is a likely choice; our example is a sextuple of references. """

    config = copy.deepcopy(base_config)
    config['combine_multiple_refs'] = 3

    input_dir = os.path.abspath(os.path.join(testcase_path, 'sensor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # The "Threshold" object is referred to six times, and is the only thing with a DwellTime attribute.
    assert output.count('DwellTime') == 1


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_combine_at_6(mockRequest):
    """ Threshhold is set at 6. Our example with six references should trigger here too (fencepost check). """

    config = copy.deepcopy(base_config)
    config['combine_multiple_refs'] = 3

    input_dir = os.path.abspath(os.path.join(testcase_path, 'sensor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # The "Threshold" object is referred to six times, and is the only thing with a DwellTime attribute.
    assert output.count('DwellTime') == 1


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_combine_at_7(mockRequest):
    """ Threshhold is set at 7. Our example with six references should NOT trigger here. """

    config = copy.deepcopy(base_config)
    config['combine_multiple_refs'] = 3

    input_dir = os.path.abspath(os.path.join(testcase_path, 'sensor'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # The "Threshold" object is referred to six times, and is the only thing with a DwellTime attribute.
    assert output.count('DwellTime') == 6
