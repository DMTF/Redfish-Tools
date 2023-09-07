# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_schema_deprecated.py

Brief: test(s) for correct output for a schema with deprecation annotations at top-level
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from .discrepancy_list import DiscrepancyList

testcase_path = os.path.join('tests', 'samples', 'deprecated_schema')

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

    'output_format': 'markdown',
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_schema_deprecated_latest_output_markdown(mockRequest):
    """ Verify markdown output contains expected deprecation info. Deprecation is at latest (current) version."""

    input_dir = os.path.abspath(os.path.join(testcase_path, 'latest_deprecated', 'input'))

    config = copy.deepcopy(base_config)
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['output_format'] = 'markdown'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    discrepancies = DiscrepancyList()

    expected_strings = [
        'Power 1.6.0 (deprecated)',
        'v1.6 Deprecated',
        'This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.',
        'This schema has been deprecated because absolute power corrupts absolutely.',
        ]

    for expected in expected_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_schema_deprecated_latest_output_html(mockRequest):
    """ Verify HTML output contains expected deprecation info. Deprecation is at latest (current) version."""

    input_dir = os.path.abspath(os.path.join(testcase_path, 'latest_deprecated', 'input'))

    config = copy.deepcopy(base_config)
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['output_format'] = 'html'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    discrepancies = DiscrepancyList()

    expected_strings = [
        'Power 1.6.0 (deprecated)',
        'v1.6 Deprecated',
        'This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.',
        'This schema has been deprecated because absolute power corrupts absolutely.',
        ]

    for expected in expected_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_schema_deprecated_earlier_output_markdown(mockRequest):
    """ Verify markdown output contains expected deprecation info. Deprecation starts at previous version."""

    input_dir = os.path.abspath(os.path.join(testcase_path, 'earlier_deprecated', 'input'))

    config = copy.deepcopy(base_config)
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['output_format'] = 'markdown'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    discrepancies = DiscrepancyList()

    expected_strings = [
        'Power 1.6.0 (deprecated)',
        'v1.6 Deprecated',
        'v1.5 Deprecated',
        'This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.',
        'This schema has been deprecated because absolute power corrupts absolutely.',
        ]

    for expected in expected_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_schema_deprecated_earlier_output_html(mockRequest):
    """ Verify HTML output contains expected deprecation info. Deprecation starts at previous version."""

    input_dir = os.path.abspath(os.path.join(testcase_path, 'earlier_deprecated', 'input'))

    config = copy.deepcopy(base_config)
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['output_format'] = 'html'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    discrepancies = DiscrepancyList()

    expected_strings = [
        'Power 1.6.0 (deprecated)',
        'v1.6 Deprecated',
        'v1.5 Deprecated',
        'This schema has been deprecated and use in new implementations is discouraged except to retain compatibility with existing products.',
        'This schema has been deprecated because absolute power corrupts absolutely.',
        ]

    for expected in expected_strings:
        if expected not in output:
            discrepancies.append('"' + expected + '" not found')

    assert [] == discrepancies
