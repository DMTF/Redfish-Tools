# Copyright Notice:
# Copyright 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_release_history.py

Brief: test(s) for correct generation of "Release History" information from "release" annotations.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from doc_formatter import DocFormatter

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'expand_defs_from_non_output_schemas': False,
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

expected_release_history = [
    {
    "version": "1.0.6",
    "release": "2016.1"
    },
    {
    "version": "1.1.5",
    "release": "2016.2"
    },
    {
    "version": "1.2.3",
    "release": "2017.1"
    },
    {
    "version": "1.3.3",
    "release": "2017.2"
    },
    {
    "version": "1.4.2",
    "release": "2017.3"
    },
    {
    "version": "1.5.1",
    "release": "2018.2"
    },
    {
    "version": "1.6.0",
    "release": "2018.3"
    }
]


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_release_history_data_collection(mockRequest):
    """ Verify that the correct release data is collected in the DocGenerator property_data.

    This data includes full versions (including errata).
    """

    config = copy.deepcopy(base_config)

    input_dir = os.path.abspath(os.path.join(testcase_path, 'release_history', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert docGen.property_data['redfish.dmtf.org/schemas/v1/Storage.json'].get('release_history') == expected_release_history


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_release_history_summary_data(mockRequest):
    """ Verify that we summarize our sample data correctly:

    * last 6 entries
    * versions to major/minor only
    * ordered latest-to-earliest
    """

    # Insert a few additional version entries, as we can expect future schemas to include
    # release data from day 1 -- meaning we will see the same release repeated a few times.
    release_history = copy.deepcopy(expected_release_history)
    release_history.insert(4, {"version": "1.4.1", "release": "2017.3"})
    release_history.insert(4, {"version": "1.4.0", "release": "2017.3"})
    release_history.insert(3, {"version": "1.3.2", "release": "2017.2"})
    release_history.insert(3, {"version": "1.3.1", "release": "2017.2"})
    release_history.insert(3, {"version": "1.3.0", "release": "2017.2"})

    summary = DocFormatter.summarize_release_history(release_history)

    expected_summary = [
        {
        "version": "v1.6",
        "release": "2018.3",
        },
        {
        "version": "v1.5",
        "release": "2018.2"
        },
        {
        "version": "v1.4",
        "release": "2017.3"
        },
        {
        "version": "v1.3",
        "release": "2017.2"
        },
        {
        "version": "v1.2",
        "release": "2017.1"
        },
        {
        "version": "v1.1",
        "release": "2016.2"
        },
        {
        "version": "v1.0",
        "release": "2016.1"
        },
        ]
    assert summary == expected_summary


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_release_history_output_markdown(mockRequest):
    """ Verify that the release history output is correct.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'release_history', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()
    expected_output = """|     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
| *v1.6* | *v1.5* | *v1.4* | *v1.3* | *v1.2* | *v1.1* | *v1.0* |
| 2018.3 | 2018.2 | 2017.3 | 2017.2 | 2017.1 | 2016.2 | 2016.1 |"""

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
def test_release_history_output_html(mockRequest):
    """ Verify that the release history output is correct.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'release_history', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['output_format'] = 'html'

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    expected_output = "<table><tbody><tr><td><i>v1.6</i></td><td><i>v1.5</i></td><td><i>v1.4</i></td><td><i>v1.3</i></td><td><i>v1.2</i></td><td><i>v1.1</i></td><td><i>v1.0</i></td></tr><tr><td>2018.3</td><td>2018.2</td><td>2017.3</td><td>2017.2</td><td>2017.1</td><td>2016.2</td><td>2016.1</td></tr></tbody></table>"

    output = output.replace('\n', '')

    assert expected_output in output
