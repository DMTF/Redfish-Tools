# Copyright Notice:
# Copyright 2019-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_required_attributes.py

Brief: test(s) for correct generation of "required" indication.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from doc_formatter import DocFormatter

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'schema_link_replacements': {},

    'profile': {},
    'escape_chars': [],

    'output_format': 'slate',
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_required_attribute_collection(mockRequest):
    """ Check for presence of correct prop_required in property data. """
    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'required_attributes', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Check a couple of properties that are directly included in property_data.
    # Note: when we follow a $ref, we apply "required" annotations on the fly, so the only way to
    # inspect them is by looking at formatted output, unfortunately.
    eventData = docGen.property_data['redfish.dmtf.org/schemas/v1/Event.json']
    eventProperties = eventData['properties']
    assert eventProperties['Events']['prop_required'] is True
    assert eventProperties['Id']['prop_required'] is True
    assert eventProperties['Context']['prop_required'] is False


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_required_attribute_output_markdown(mockRequest):
    """ Check for correct "required" output in markdown. Includes some properties expanded by $ref. """
    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'required_attributes', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    lines = output.split(os.linesep)

    # Check a couple of properties that are directly included in property_data.
    context_lines = [ x for x in lines if '**Context**' in x ]
    for x in context_lines:
        assert 'required' not in x
    events_lines = [ x for x in lines if '**Events**' in x ]
    for x in events_lines:
        assert 'required' in x

    # And some properties of an object from the "definitions" section.
    eventtype_lines = [ x for x in lines if '**EventType**' in x ]
    for x in eventtype_lines:
        assert 'required' in x
    messageid_lines = [ x for x in lines if '**MessageId**' in x ]
    for x in messageid_lines:
        assert 'required' in x
    severity_lines = [ x for x in lines if '**Severity**' in x ]
    for x in severity_lines:
        assert 'required' not in x

    # Make sure we actually found the lines to test:
    assert len(context_lines) and len(events_lines) and len(eventtype_lines) and len(messageid_lines) and len(severity_lines)
