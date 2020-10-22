# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_action_response.py

Brief: Test for correct output of Response Payload when an actionResponse is defined.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'action_response')

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'excluded_pattern_props': [r'^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\.[a-zA-Z_][a-zA-Z0-9_.]+$'],
    'uri_replacements': {},
    'wants_common_objects': False,
    'profile': {},
    'escape_chars': [],
    'output_format': 'slate',
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_action_for_rekey_markdown(mockRequest):
    """ This is the initial example, from the Certificate schema """
    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'certificate'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    expected_output = '''
**Response Payload**

|     |     |     |     |
| --- | --- | --- | --- |
| { |  |  |  |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Certificate** *(v1.1+)* { | object<br><br>* required* | The link to the certificate being rekeyed. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**@odata.id** | string<br><br>*read-only* | Link to another Certificate resource. |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;} |   |   |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**CSRString** *(v1.1+)* | string<br><br>*read-only required* | The string for the certificate signing request. |
| } |  |  |  |
'''

    assert expected_output in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_action_for_rekey_html(mockRequest):
    """ This is the initial example, from the Certificate schema """
    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'certificate'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    config['output_format'] = 'html'
    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    expected_output = '''
</tbody></table><p><b>Response Payload</b></p>
<table>
<tbody>
<tr><td>{</td><td></td><td></td><td></td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>Certificate</b> <i>(v1.1+)</i> {</nobr></td><td>object</td><td> <nobr>required</nobr></td><td>The link to the certificate being rekeyed.</td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>@odata.id</b></nobr><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}</td><td>string</td><td><nobr>read-only</nobr></td><td><i>Link to another Certificate resource.</i></td></tr>
<tr><td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<nobr><b>CSRString</b> <i>(v1.1+)</i></nobr><br>}</td><td>string</td><td><nobr>read-only</nobr> <nobr>required</nobr></td><td>The string for the certificate signing request.</td></tr>
</tbody></table>
'''

    assert expected_output in output
