# Copyright Notice:
# Copyright 2018-2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_supplement_output.py

Test(s) to verify that supplemental information appears in the correct places in output.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'supplement_tests')

schema_supplement = {
    # Status is an example of a Referenced Object.
    'Status': {
    'description': "SUPPLEMENT-SUPPLIED DESCRIPTION for Status",
    'intro': "SUPPLEMENT-SUPPLIED INTRO for Status",
    'jsonpayload': "SUPPLEMENT-SUPPLIED JSON for Status",
    },
    # Endpoint is a documented schema
    'Endpoint': {
    'description': "SUPPLEMENT-SUPPLIED DESCRIPTION for Endpoint",
    'intro': "SUPPLEMENT-SUPPLIED INTRO for Endpoint",
    'jsonpayload': "SUPPLEMENT-SUPPLIED JSON for Endpoint",
    }
    }

property_description_overrides = {
    "Oem": "This is a description override for the Oem object."
    }

property_description_full_overrides = {
    "EndpointProtocol": "This is a full description override for the Oem object."
    }

base_config = {
    'excluded_by_match': ['@odata.count', '@odata.navigationLink'],
    'profile_resources': {},
    'units_translation': {},
    'excluded_annotations_by_match': ['@odata.count', '@odata.navigationLink'],
    'excluded_schemas': [],
    'excluded_properties': ['@odata.id', '@odata.context', '@odata.type'],
    'schema_link_replacements': {},
    'wants_common_objects': True,
    'profile': {},
    'escape_chars': [],
    'property_description_overrides': property_description_overrides,
    'intro_content': "# Common Objects\n\n[insert_common_objects]\n\ntext1\n~pagebreak~\ntext2\n",
    }


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_output_html (mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    config['schema_supplement'] = schema_supplement

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Chop up the HTML into rough sections.
    output_parts = output.split('<h2')
    status_section = [x for x in output_parts if 'id="common-properties-Status"' in x]
    endpoint_section = [x for x in output_parts if 'id="Endpoint"' in x]

    # Chop into rows. We just want to find the Oem rows.
    output_rows = output.split('<tr')
    oem_rows = [x for x in output_rows if "<b>Oem</b>" in x]

    # These assertions target strings the supplement provided:
    assert len(status_section) == 1 and 'SUPPLEMENT-SUPPLIED DESCRIPTION for Status' in status_section[0], "Referenced Object (Status) output is missing supplement-supplied description"
    assert len(status_section) == 1 and 'SUPPLEMENT-SUPPLIED INTRO for Status' in status_section[0], "Referenced Object (Status) output is missing supplement-supplied intro"
    # strip tags from output sections for json payload tests; code highlighting is decorating the
    # plain-text strings in a way I don't want to rely on.
    assert len(status_section) == 1 and 'SUPPLEMENT-SUPPLIED JSON for Status' in simple_strip_tags(status_section[0]), "Referenced Object (Status) output is missing supplement-supplied json payload"

    assert len(endpoint_section) == 1 and 'SUPPLEMENT-SUPPLIED DESCRIPTION for Endpoint' in endpoint_section[0], "Schema Object (Endpoint) output is missing supplement-supplied description"
    assert len(endpoint_section) == 1 and 'SUPPLEMENT-SUPPLIED INTRO for Endpoint' in endpoint_section[0], "Schema Object (Endpoint) output is missing supplement-supplied intro"
    # strip tags from output sections for json payload tests; code highlighting is decorating the
    # plain-text strings in a way I don't want to rely on.
    assert len(endpoint_section) == 1 and 'SUPPLEMENT-SUPPLIED JSON for Endpoint' in simple_strip_tags(endpoint_section[0]), "Schema Object (Endpoint) output is missing supplement-supplied json payload"


    oem_failed_overrides = [x for x in oem_rows if "This is a description override for the Oem object." not in x]
    assert len(oem_failed_overrides) == 0, "Property description override failed for " + str(len(oem_failed_overrides)) + " mentions of Oem"

    # Check for ~pagebreak~ converted to <p style="page-break-before: always">
    pbrk_location = output[output.find('text1') : output.find('text2')]
    assert '<p style="page-break-before: always"></p>' in pbrk_location, "HTML output lacked expected page break markup"


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_output_action_details_in_html (mockRequest):
    """ Test of action_details in supplement config. We happen to exercise HTML output here. """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'certificate_service'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    config['schema_supplement'] = {
        'CertificateService': {
            'action_details': {
                'ReplaceCertificate': "ACTION DETAILS for ReplaceCertificate",
                "GenerateCSR": "ACTION DETAILS for GenerateCSR",
                }
            }
        }

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This test verifies the text was picked up, but not that it was placed correctly.
    expected_strings = [
        '<p>ACTION DETAILS for GenerateCSR</p>',
        '<p>ACTION DETAILS for ReplaceCertificate</p>',
        ]
    for es in expected_strings:
        assert es in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_description_vs_full_html (mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'html'
    config['schema_supplement'] = schema_supplement

    config['property_description_overrides'] = {
        "IPv4Address": "This is a description override for the IPv4Address object.",
        "DeviceId": "This is a description override for DeviceId, which is not a top-level property.",
    }

    config['property_fulldescription_overrides'] = {
        "IPv6Address": "This is a full description override for the IPv6Address object.",
        "SubsystemId": "This is a description override for SubsystemId, which is not a top-level property.",
    }

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Chop into rows. We just want to find the IPv4Address and IPv6Address rows.
    output_rows = output.split('<tr')
    ipv4_rows = [x for x in output_rows if "<b>IPv4Address</b>" in x]
    ipv6_rows = [x for x in output_rows if "<b>IPv6Address</b>" in x]
    deviceId_rows = [x for x in output_rows if "<b>DeviceId</b>" in x]
    subsystemId_rows = [x for x in output_rows if "<b>SubsystemId</b>" in x]

    # Verify that the overrides were used:
    ipv4_failed_overrides = [x for x in ipv4_rows if "This is a description override for the IPv4Address object." not in x]
    assert len(ipv4_failed_overrides) == 0, "Property description override failed for " + str(len(ipv4_failed_overrides)) + " mentions of Ipv4Address"

    ipv6_failed_overrides = [x for x in ipv6_rows if "This is a full description override for the IPv6Address object." not in x]
    assert len(ipv6_failed_overrides) == 0, "Property full description override failed for " + str(len(ipv6_failed_overrides)) + " mentions of Ipv6Address"

    deviceId_failed_overrides = [x for x in deviceId_rows if "This is a description override for DeviceId" not in x]
    assert len(deviceId_failed_overrides) == 0, "Property description override failed for " + str(len(deviceId_failed_overrides)) + " mentions of DeviceId"

    subsystemId_failed_overrides = [x for x in subsystemId_rows if "This is a description override for SubsystemId" not in x]
    assert len(subsystemId_failed_overrides) == 0, "Property description override failed for " + str(len(subsystemId_failed_overrides)) + " mentions of SubsystemId"

    # Verify that the description overrides retained the reference to the common property:
    ipv4_failed_overrides = [x for x in ipv4_rows if "For property details" not in x]
    assert len(ipv4_failed_overrides) == 0, "Property description override failed to include reference to common property for " + str(len(ipv4_failed_overrides)) + " mentions of Ipv4Address"

    # Verify that the full description overrides DID NOT retain the reference to the common property:
    ipv6_failed_overrides = [x for x in ipv6_rows if "For property details" in x]
    assert len(ipv6_failed_overrides) == 0, "Property full description override incorrectly included reference to common property " + str(len(ipv6_failed_overrides)) + " mentions of Ipv6Address"


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_output_slate (mockRequest):

    config = copy.deepcopy(base_config)
    config['output_format'] = 'slate'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    config['schema_supplement'] = schema_supplement

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # Check for ~pagebreak~ converted to <p style="page-break-before: always">
    pbrk_location = output[output.find('text1') : output.find('text2')]
    assert '<p style="page-break-before: always"></p>' in pbrk_location, "HTML output lacked expected page break markup"


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_file_parsing (mockRequest):
    """ Parse supplementary blocks from a markdown file """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))
    supplement_md_dir = os.path.abspath(os.path.join(testcase_path, 'md_supplements'))

    config['supplement_md_dir'] = supplement_md_dir

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert docGen.config['md_supplements'] ==  {
        "Endpoint": {
            "description": "INTRO FOR Endpoint schema.\n\nThis one happens to be multiple lines.",
            "jsonpayload": '''```json
{ "payload": "A chunk of JSON from the md supplement" }
```''',
            "property_details": {
                "HostReservationMemoryBytes": "PROPERTY DETAILS for HostReservationMemoryBytes"
                }
            },
            "CertificateService": {
                "action_details": {
                    "ReplaceCertificate": "ACTION DETAILS for ReplaceCertificate",
                    "GenerateCSR": "ACTION DETAILS for GenerateCSR"
                    }
                }
        }


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_output_from_files (mockRequest):
    """ Test of supplementary blocks pulled in from markdown file(s) rather than schema_supplement """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'ipaddresses'))
    supplement_md_dir = os.path.abspath(os.path.join(testcase_path, 'md_supplements'))

    config['supplement_md_dir'] = supplement_md_dir

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This test verifies the text was picked up, but not that it was placed correctly.
    expected_strings = [
        "INTRO FOR Endpoint schema.\n\nThis one happens to be multiple lines.",
        '```json\n{ "payload": "A chunk of JSON from the md supplement" }\n```',
        "PROPERTY DETAILS for HostReservationMemoryBytes",
        '#### HostReservationMemoryBytes', # This is a Property Details heading
        ]
    for es in expected_strings:
        assert es in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_supplement_output_from_files_with_action_details (mockRequest):
    """ Test of supplementary blocks for Action Details pulled in from markdown file(s) """

    config = copy.deepcopy(base_config)
    config['output_format'] = 'markdown'

    input_dir = os.path.abspath(os.path.join(testcase_path, 'certificate_service'))
    supplement_md_dir = os.path.abspath(os.path.join(testcase_path, 'md_supplements'))

    config['supplement_md_dir'] = supplement_md_dir

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    # This test verifies the text was picked up, but not that it was placed correctly.
    expected_strings = [
        'ACTION DETAILS for GenerateCSR',
        'ACTION DETAILS for ReplaceCertificate',
        ]
    for es in expected_strings:
        assert es in output


def simple_strip_tags(s):
    """ Quick solution to my need to strip tags from output in a couple of the tests.
    cf. https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python """
    tag = False
    quote = False
    out = ""

    for c in s:
        if c == '<' and not quote:
            tag = True
        elif c == '>' and not quote:
            tag = False
        elif (c == '"' or c == "'") and tag:
            quote = not quote
        elif not tag:
            out = out + c

    return out
