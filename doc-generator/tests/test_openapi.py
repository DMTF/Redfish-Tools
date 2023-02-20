# Copyright Notice:
# Copyright 2018-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_openapi.py

Brief: Tests for correct handling of OpenAPI features (URIs)
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'openapi')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'schema_link_replacements': {},
    'wants_common_objects': False,
    'profile': {},
    'escape_chars': [],
    'output_format': 'html'
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_uri_capture(mockRequest):

    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    event_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/Event.json')
    logentry_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntry.json')
    logentrycollection_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntryCollection.json')

    assert event_properties['uris'] == []
    assert sorted(logentry_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/Entries/{LogEntryId}"
        ])
    assert sorted(logentrycollection_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/STUBCollection",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/STUBCollection",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/STUBCollection"
        ])


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_collection_uris_captured_when_collections_excluded (mockRequest):

    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    logentrycollection_properties = docGen.property_data.get('redfish.dmtf.org/schemas/v1/LogEntryCollection.json')

    assert sorted(logentrycollection_properties['uris']) == sorted([
        "/redfish/v1/Managers/{ManagerId}/LogServices/{LogServiceId}/STUBCollection",
        "/redfish/v1/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/STUBCollection",
        "/redfish/v1/CompositionService/ResourceBlocks/{ResourceBlockId}/Systems/{ComputerSystemId}/LogServices/{LogServiceId}/STUBCollection"
        ])


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_uris_in_regular_schema_slate_output (mockRequest):

    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'slate'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Links should appear with asterisks around {} path parts to highlight them.
    expected_strings = [
        "/&#8203;redfish/&#8203;v1/&#8203;Managers/&#8203;*{ManagerId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;Entries/&#8203;*{LogEntryId}*",
        "/&#8203;redfish/&#8203;v1/&#8203;Systems/&#8203;*{ComputerSystemId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;Entries/&#8203;*{LogEntryId}*",
        "/&#8203;redfish/&#8203;v1/&#8203;CompositionService/&#8203;ResourceBlocks/&#8203;*{ResourceBlockId}*/&#8203;Systems/&#8203;*{ComputerSystemId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;Entries/&#8203;*{LogEntryId}*"
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_uris_in_collection_schema_slate_output (mockRequest):

    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'slate'
    config['intro_content'] = "# Redfish Collections\n\n[insert_collections]\n"

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    expected_strings = [
        "/&#8203;redfish/&#8203;v1/&#8203;Managers/&#8203;*{ManagerId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;STUBCollection",
        "/&#8203;redfish/&#8203;v1/&#8203;Systems/&#8203;*{ComputerSystemId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;STUBCollection",
        "/&#8203;redfish/&#8203;v1/&#8203;CompositionService/&#8203;ResourceBlocks/&#8203;*{ResourceBlockId}*/&#8203;Systems/&#8203;*{ComputerSystemId}*/&#8203;LogServices/&#8203;*{LogServiceId}*/&#8203;STUBCollection"
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_uris_in_regular_schema_html_output (mockRequest):
    """ HTML output is more complex and subject to change.

    In addition to highlighting Id placeholders, they are linked to schema documentation. For this test, several schemas
    are not documented, so the link will go to the schema file itself. """

    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Links should appear with asterisks around {} path parts to highlight them.
    expected_strings = [
        '/?redfish/?v1/?Managers/?<i>{ManagerId}</i>/?LogServices/?<i>{LogServiceId}</i>/?Entries/?<i><a href="#LogEntry">{LogEntryId}</a></i>',
        '/?redfish/?v1/?Systems/?<i>{ComputerSystemId}</i>/?LogServices/?<i>{LogServiceId}</i>/?Entries/?<i><a href="#LogEntry">{LogEntryId}</a></i>',
        '/?redfish/?v1/?CompositionService/?ResourceBlocks/?<i>{ResourceBlockId}</i>/?Systems/?<i>{ComputerSystemId}</i>/?LogServices/?<i>{LogServiceId}</i>/?Entries/?<i><a href="#LogEntry">{LogEntryId}</a></i>'
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_action_uris (mockRequest):
    """ Action URIs are based on URIs and action names,
    and should be output as part of the Actions section in HTML and markdown output.
    """
    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'slate'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'actions'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This used to be more interesting.
    expected_strings = [
        "*{Base URI of target resource}*/Actions/Bios.ChangePassword",
        "*{Base URI of target resource}*/Actions/Bios.ResetBios",
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_actions_not_suppressed (mockRequest):
    """ By default, "Actions" appear in property tables. """
    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'slate'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'actions'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This is what the start of an "Actions" object looks like in a markdown table.
    assert "| **Actions** { | object |" in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_actions_suppressed (mockRequest):
    """ The "actions_in_property_table" config setting, if false, should suppress
    "Actions" from appearing in property tables.
    """
    config = copy.deepcopy(base_config)
    config['excluded_schemas_by_match'] = [ 'Collection' ]
    config['output_format'] = 'slate'
    config['actions_in_property_table'] = False

    input_dir = os.path.abspath(os.path.join(testcase_path, 'actions'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This is what the start of an "Actions" object looks like in a markdown table.
    assert "| **Actions** { | object |" not in output
