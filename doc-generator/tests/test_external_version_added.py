# Copyright Notice:
# Copyright 2026 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_external_version_added.py

Brief: test(s) for the "external_version_annotations" config setting.

When an object is expanded in place from another schema -- as an excerpt, via the "include"
reference disposition, or because it met the combine_multiple_refs threshold -- its properties and
enumeration values carry the versions of the schema that defines them, not versions of the schema
being documented. The sample here mirrors the real PowerSupplyMetrics case: "SpeedRPM" and
"DeviceName" arrive from a Sensor excerpt and were added in Sensor v1.2, and the "Headroom"
enumeration value arrives from the same excerpt and was added in Sensor v1.2 as well.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

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

    'output_format': 'markdown',
}


def generate_output(mode=None, output_format='markdown'):
    """ Generate documentation for the external_version_added sample. """

    config = copy.deepcopy(base_config)
    config['output_format'] = output_format
    if mode is not None:
        config['external_version_annotations'] = mode

    input_dir = os.path.abspath(os.path.join(testcase_path, 'external_version_added'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    return docGen.generate_docs()


def schema_section(output, schema_name):
    """ Isolate one schema's section, so another schema's rows can't satisfy an assertion.

    Schema sections are level-two markdown headings, which the doc generator emits in alphabetical
    order; the next such heading ends the section.
    """

    _before, marker, section = output.partition('## ' + schema_name + '\n')
    assert marker, '%s section not found in output' % schema_name
    section, _marker, _after = section.partition('\n## ')
    return section


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_external_versions_suppressed_by_default(mockRequest):
    """ With no setting in config, versions from another schema are left out. """

    section = schema_section(generate_output(), 'PowerSupplyMetrics 1.1.0')

    assert '**SpeedRPM** |' in section
    assert '**DeviceName** |' in section
    assert '(v1.2+)' not in section

    # The enum value's version comes from Sensor too, so it is left out as well.
    assert '| Headroom | ' in section

    # A property added to PowerSupplyMetrics itself keeps its version, including one whose $ref
    # crosses into another schema.
    assert '**FanSpeedsPercent** *(v1.1+)*' in section
    assert '**PrimarySensor** *(v1.1+)*' in section


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_external_versions_qualified(mockRequest):
    """ In "qualify" mode, the version is reported along with the schema that defines it. """

    section = schema_section(generate_output('qualify'), 'PowerSupplyMetrics 1.1.0')

    assert '**SpeedRPM** *(Sensor v1.2+)*' in section
    assert '**DeviceName** *(Sensor v1.2+)*' in section
    assert 'Headroom *(Sensor v1.2+)*' in section

    assert '**FanSpeedsPercent** *(v1.1+)*' in section
    assert '**PrimarySensor** *(v1.1+)*' in section


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_external_versions_as_is(mockRequest):
    """ The "as_is" setting retains the behavior of releases prior to this setting. """

    section = schema_section(generate_output('as_is'), 'PowerSupplyMetrics 1.1.0')

    assert '**SpeedRPM** *(v1.2+)*' in section
    assert '**DeviceName** *(v1.2+)*' in section
    assert 'Headroom *(v1.2+)*' in section


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_local_versions_are_unaffected(mockRequest):
    """ Within the Sensor section, these same properties and values are local and keep their versions. """

    for mode in (None, 'suppress', 'qualify', 'as_is'):
        section = schema_section(generate_output(mode), 'Sensor 1.2.0')

        assert '**SpeedRPM** *(v1.2+)*' in section, 'mode: %s' % mode
        assert '**DeviceName** *(v1.2+)*' in section, 'mode: %s' % mode
        assert 'Headroom *(v1.2+)*' in section, 'mode: %s' % mode


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_external_versions_qualified_html(mockRequest):
    """ The HTML output goes through separate enum formatting, so check it too. """

    output = generate_output('qualify', output_format='html')

    assert 'SpeedRPM' in output
    assert '(Sensor v1.2+)' in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
# The test sample is incomplete, so we will be warned of unavailable resources (odata, Resource, and more).
@pytest.mark.filterwarnings("ignore:Unable to find data")
@pytest.mark.filterwarnings("ignore:Unable to read")
@pytest.mark.filterwarnings("ignore:Unable to retrieve")
@pytest.mark.filterwarnings("ignore:[0-9]+ referenced files were missing")
def test_local_version_on_link_to_other_schema(mockRequest):
    """ A link property carries its own schema's version even though its $ref leaves that schema.

    PhysicalPortAssignment is declared in NetworkDeviceFunction v1.3 and refs NetworkPort, so
    suppressing versions for anything that refs another schema would lose a correct annotation.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(os.path.join(testcase_path, 'generate_docs_cases', 'general', 'input'))

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = { input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)
    output = docGen.generate_docs()

    assert '**PhysicalPortAssignment** *(v1.3+)*' in output
