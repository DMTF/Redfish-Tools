# Copyright Notice:
# Copyright 2019 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_excerpt.py

Brief: Tests for correct treatment of Excerpts.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'excerpt')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'excluded_pattern_props': [r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'],
    'uri_replacements': {},
    'profile': {},
    'escape_chars': [],
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_excerpt_circuit(mockRequest):
    """ The Circuit schema contains many references to excerpts """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'circuit'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Looking for the generated description line is an easy way to check that excerpts were detected:
    description1 = "This object is an excerpt of the *Sensor* resource located at the URI shown in DataSourceUri."

    # Verify one of the expanded excerpts was output.
    expected_excerpt = """| **Current** *(v0.9+)* { | object<br>(excerpt) | The current sensor for this circuit. This object is an excerpt of the *Sensor* resource located at the URI shown in DataSourceUri. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**DataSourceUri** | string<br><br>*read-only<br>(null)* | A link to the resource that provides the data for this object. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Name** | string<br><br>*read-only required* | The name of the resource or array element. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PeakReading** | number<br><br>*read-only<br>(null)* | The peak reading value for this sensor. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PhysicalContext** | string<br>(enum)<br><br>*read-only<br>(null)* | Describes the area or device to which this sensor measurement applies. *See PhysicalContext in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PhysicalSubContext** | string<br>(enum)<br><br>*read-only<br>(null)* | Describes the usage or location within a device to which this sensor measurement applies. *See PhysicalSubContext in Property Details, below, for the possible values of this property.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Reading** | number<br><br>*read-only<br>(null)* | The present value for this Sensor. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ReadingUnits** | string<br><br>*read-only<br>(null)* | Units in which the reading and thresholds are measured. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object | This property describes the status and health of the resource and its children. See the *Resource* schema for details on this property. |
| } |   |   |"""

    expected_excerpt = """| **Current** *(v0.9+)* { | object<br>(excerpt) | The current sensor for this circuit. This object is an excerpt of the *Sensor* resource located at the URI shown in DataSourceUri. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**DataSourceUri** | string<br><br>*read-only<br>(null)* | A link to the resource that provides the data for this object. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Name** | string<br><br>*read-only required* | The name of the resource or array element. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PeakReading** | number<br><br>*read-only<br>(null)* | The peak reading value for this sensor. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PhysicalContext** | string<br>(enum)<br><br>*read-only<br>(null)* | Describes the area or device to which this sensor measurement applies. *For the possible property values, see PhysicalContext in Property Details.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**PhysicalSubContext** | string<br>(enum)<br><br>*read-only<br>(null)* | Describes the usage or location within a device to which this sensor measurement applies. *For the possible property values, see PhysicalSubContext in Property Details.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Reading** | number<br><br>*read-only<br>(null)* | The present value for this Sensor. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**ReadingUnits** | string<br><br>*read-only<br>(null)* | Units in which the reading and thresholds are measured. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Status** {} | object | This property describes the status and health of the resource and its children. See the *Resource* schema for details on this property. |
| } |   |   |"""

    assert output.count(description1) == 56
    assert expected_excerpt in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_excerpt_html_links(mockRequest):
    """ Markdown doesn't include links to the excerpted schema, so we need to test this in HTML """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'circuit'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Looking for the generated description line is an easy way to check that excerpts were detected:
    description1 = 'This object is an excerpt of the <a href="#Sensor">Sensor</a> resource located at the URI shown in DataSourceUri.'

    assert output.count(description1) == 56


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_excerpt_pdm(mockRequest):
    """ The Power Distribution Metrics schema includes arrays of excerpts
    (which the initial implementation missed).
    """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'power_distribution_metrics'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Looking for the generated description line is an easy way to check that excerpts were detected:
    description1 = 'Contains the humidity sensors. This object is an excerpt of the *Sensor* resource located at the URI shown in DataSourceUri.'
    description2 = 'Contains the array of 1 or more temperature sensors. This object is an excerpt of the *Sensor* resource located at the URI shown in DataSourceUri.'

    assert description1 in output
    assert description2 in output
