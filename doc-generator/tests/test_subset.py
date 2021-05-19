# Copyright Notice:
# Copyright 2020-2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_subset.py

Brief: test(s) for subset mode.
"""

import os
import copy
from unittest.mock import patch
import pytest
import warnings
from doc_generator import DocGenerator
from .discrepancy_list import DiscrepancyList

testcase_path = os.path.join('tests', 'samples')

base_config = {
    'output_format': 'markdown',
	"actions_in_property_table": False,
	"excluded_properties": [
		"@odata.context",
		"@odata.type",
		"@odata.id",
		"@odata.etag",
		"Oem",
		"HealthRollup"

	],
	"excluded_annotations": [
		"*@odata.count",
		"*@odata.navigationLink"
	],
	"excluded_schemas": [
		"*Collection",
		"HostedStorageServices",
		"StorageService",
		"StorageSystem",
		"StorageServiceCollection",
		"StorageSystemCollection",
		"idRef"
	],
	"excluded_pattern_properties": [
		"^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\.[a-zA-Z_][a-zA-Z0-9_]*$"
	],
    "excluded_by_match": [],
	"units_translation": {
		"s": "seconds",
		"Mb/s": "Mbits/second",
		"By": "bytes",
		"Cel": "Celsius",
		"MiBy": "mebibytes",
		"W": "Watts",
		"V": "Volts",
		"mW": "milliWatts",
		"m": "meters"
	}
}

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_subset_mode_issue_271_expected_content_included_markdown(mockRequest):
    """ Generate subset documentation, testing mainly for problems identified in github issue 271. Markdown output """

    config = copy.deepcopy(base_config)

    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'json-schema'))
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    subset_config = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'subset_spec.json'))
    config['subset_mode'] = True
    config['subset_doc'] = subset_config

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # IntegerTest schema is in schema data, but should not appear in output.
    unexpected_heading = 'IntegerTest'
    assert unexpected_heading not in output

    # Verify $ref are expanded-in-place where mentioned in profile.
    # Status is an example of an object property; it is used in two places with different requirements in this example:
    expected_status_snippet1 = '''
| **Status** { | object |  | This property describes the status and health of the resource and its children. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Health** | string<br>(enum) | *read-only<br>(null)* | This represents the health state of this resource in the absence of its dependent resources. *For the possible property values, see Health in Property details.* |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**State** | string<br>(enum) | *read-only<br>(null)* | This indicates the known state of the resource, such as if it is enabled. *For the possible property values, see State in Property details.* |
'''
    expected_status_snippet2 = '''
| **Status** { | object |  | The status and health of the resource and its subordinate or dependent resources. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**State** | string<br>(enum) | *read-only<br>(null)* | This indicates the known state of the resource, such as if it is enabled. *For the possible property values, see State in Property details.* |
'''
    assert expected_status_snippet1 in output
    assert expected_status_snippet2 in output

    # IPv4Address is an "items" property. The code path for this is a bit different.
    expected_ipv4address_snippet = '''
| **IPv4Addresses** [ { | array |  | The IPv4 addresses currently in use by this interface. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Address** | string | *read-write<br>(null)* | This is the IPv4 Address. |
'''
    assert expected_ipv4address_snippet in output



@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.d
def test_subset_mode_issue_271_expected_content_included_html(mockRequest):
    """ Generate subset documentation, testing mainly for problems identified in github issue 271. HTML output """

    config = copy.deepcopy(base_config)

    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'json-schema'))
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    subset_config = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'subset_spec.json'))
    config['subset_mode'] = True
    config['subset_doc'] = subset_config

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # IntegerTest schema is in schema data, but should not appear in output.
    unexpected_heading = 'IntegerTest'
    assert unexpected_heading not in output

    # Verify $ref are expanded-in-place where mentioned in profile.
    # Status is an example of an object property; it is used in two places with different requirements in this example:
    expected_status_snippet1 = '''
<tr><td><nobr><b>Status</b> {</nobr></td><td>object</td><td></td><td>This property describes the status and health of the resource and its children.</td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>Health</b></nobr></td><td>string<br>(enum)</td><td><nobr>read-only</nobr> (null)</td><td>This represents the health state of this resource in the absence of its dependent resources.<br><i>For the possible property values, see <a href="#redfish.dmtf.org/schemas/v1/Chassis.json|details|Health">Health</a> in Property details.</i></td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>State</b></nobr><br>}</td><td>string<br>(enum)</td><td><nobr>read-only</nobr> (null)</td><td>This indicates the known state of the resource, such as if it is enabled.<br><i>For the possible property values, see <a href="#redfish.dmtf.org/schemas/v1/Chassis.json|details|State">State</a> in Property details.</i></td></tr>
'''
    expected_status_snippet2 = '''
<tr><td><nobr><b>Status</b> {</nobr></td><td>object</td><td></td><td>The status and health of the resource and its subordinate or dependent resources.</td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>State</b></nobr><br>}</td><td>string<br>(enum)</td><td><nobr>read-only</nobr> (null)</td><td>This indicates the known state of the resource, such as if it is enabled.<br><i>For the possible property values, see <a href="#redfish.dmtf.org/schemas/v1/EthernetInterface.json|details|State">State</a> in Property details.</i></td></tr>
'''

    assert expected_status_snippet1 in output
    assert expected_status_snippet2 in output

    # IPv4Address is an "items" property. The code path for this is a bit different.
    expected_ipv4address_snippet = '''
<tr><td><nobr><b>IPv4Addresses</b> [ {</nobr></td><td>array</td><td></td><td>The IPv4 addresses currently in use by this interface.</td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>Address</b></nobr><br>} ]</td><td>string</td><td><nobr>read-write</nobr> (null)</td><td>This is the IPv4 Address.</td></tr>
'''
    assert expected_ipv4address_snippet in output



@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_subset_mode_issue_271_warn_on_inappropriate_spec(mockRequest):
    """ Warn when a profile specifies requirements directly on the Resource, IPAddress, Redundancy, or Settings schemas """

    config = copy.deepcopy(base_config)

    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'json-schema'))
    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    subset_config = os.path.abspath(os.path.join(testcase_path, 'subset_mode', 'bad_spec.json'))
    config['subset_mode'] = True
    config['subset_doc'] = subset_config

    with pytest.warns(UserWarning) as record:
        docGen = DocGenerator([ input_dir ], '/dev/null', config)
        output = docGen.generate_docs()

    warning_msgs = [x.message.args[0] for x in record]
    expected_msgs = [
        'Subsets should not specify requirements directly on the "Resource" schema.',
        'Subsets should not specify requirements directly on the "IPAddresses" schema.',
        'Subsets should not specify requirements directly on the "Redundancy" schema.',
        'Subsets should not specify requirements directly on the "Settings" schema.',
        ]
    for m in expected_msgs:
        assert m in warning_msgs
