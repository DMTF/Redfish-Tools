# Copyright Notice:
# Copyright 2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_localized_schemas.py

Brief: test(s) for detection and use of localized schemas.
"""

import os
import os.path
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator

testcase_path = os.path.join('tests', 'samples', 'localized_schemas', 'general', 'input')

base_config = {
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

@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_default(mockRequest):
    """ Verify a few expected strings are output in the default way when no locale is specified.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # Descriptions
        'The ComputerSystem schema represents a computer or system instance',
        'The BootOptionReference of the Boot Option to perform a one-time boot from when BootSourceOverrideTarget is `UefiBootNext`.',
        'The name of the boot order property that the system uses for the persistent boot order. *For the possible property values, see BootOrderPropertySelection in Property details.*',
        '| AliasBootOrder | The system uses the AliasBootOrder property to specify the persistent boot order. |',
        # enum that is annotated in the TEST locale (but not here):
        '| Continuous |',
        # property name that is annotated in the TEST locale (but not here):
        '| **AssetTag** |',
        # Action parameter that is annotated in the TEST locale (but not here):
        '**ResetType** |',
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_normative_default(mockRequest):
    """ Verify a few expected strings are output in the default way when no locale is specified.
    Same as test_localized_schemas_default, but with normative output.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['normative'] = True

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # Descriptions
        'This resource shall represent a computing system in the Redfish Specification.',
        'This property shall contain the BootOptionReference of the UEFI boot option for one time boot, as defined by the UEFI Specification.  The valid values for this property are specified in the values of the BootOrder array.',
        'This property shall indicate which boot order property the system uses for the persistent boot order. *For the possible property values, see BootOrderPropertySelection in Property details.*',
        '| AliasBootOrder | The system uses the AliasBootOrder property to specify the persistent boot order. |',
        # enum that is annotated in the TEST locale (but not here):
        '| Continuous |',
        # property name that is annotated in the TEST locale (but not here):
        '| **AssetTag** |',
        # Action parameter that is annotated in the TEST locale (but not here):
        '**ResetType** |',
        ]

    for x in expected_strings:
        assert x in output



@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_TEST(mockRequest):
    """ Verify that the test strings are output correctly when TEST is specified for the locale.
    """

    config = copy.deepcopy(base_config)
    config['locale'] = 'TEST'
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # Examples of descriptions:
        'THE COMPUTERSYSTEM SCHEMA REPRESENTS A COMPUTER OR SYSTEM INSTANCE',
        'THE BOOTOPTIONREFERENCE OF THE BOOT OPTION TO PERFORM A ONE-TIME BOOT FROM WHEN BOOTSOURCEOVERRIDETARGET IS `UEFIBOOTNEXT`.',
        'THE NAME OF THE BOOT ORDER PROPERTY THAT THE SYSTEM USES FOR THE PERSISTENT BOOT ORDER. *FOR THE POSSIBLE PROPERTY VALUES, SEE BootOrderPropertySelection IN PROPERTY DETAILS.*',
        '| AliasBootOrder | THE SYSTEM USES THE ALIASBOOTORDER PROPERTY TO SPECIFY THE PERSISTENT BOOT ORDER. |',
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_normative_TEST(mockRequest):
    """ Verify a few expected strings are output translated when TEST locale is specified.
    Same as test_localized_schemas_TEST, but with normative output.
    """

    config = copy.deepcopy(base_config)
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}
    config['locale'] = 'TEST'
    config['normative'] = True

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # Descriptions
        'THIS RESOURCE SHALL REPRESENT A COMPUTING SYSTEM IN THE REDFISH SPECIFICATION.',
        'THIS PROPERTY SHALL CONTAIN THE BOOTOPTIONREFERENCE OF THE UEFI BOOT OPTION FOR ONE TIME BOOT, AS DEFINED BY THE UEFI SPECIFICATION.  THE VALID VALUES FOR THIS PROPERTY ARE SPECIFIED IN THE VALUES OF THE BOOTORDER ARRAY.',
        'THIS PROPERTY SHALL INDICATE WHICH BOOT ORDER PROPERTY THE SYSTEM USES FOR THE PERSISTENT BOOT ORDER. *FOR THE POSSIBLE PROPERTY VALUES, SEE BootOrderPropertySelection IN PROPERTY DETAILS.*',
        '| AliasBootOrder | THE SYSTEM USES THE ALIASBOOTORDER PROPERTY TO SPECIFY THE PERSISTENT BOOT ORDER. |',
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_en(mockRequest):
    """ Verify that our same test strings are output the same way when "en" is specified explicitly.
    """

    config = copy.deepcopy(base_config)
    config['locale'] = 'en'
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # descriptions
        'The ComputerSystem schema represents a computer or system instance',
        'The BootOptionReference of the Boot Option to perform a one-time boot from when BootSourceOverrideTarget is `UefiBootNext`.',
        'The name of the boot order property that the system uses for the persistent boot order. *For the possible property values, see BootOrderPropertySelection in Property details.*',
        '| AliasBootOrder | The system uses the AliasBootOrder property to specify the persistent boot order. |',
        # enum that is annotated in the TEST locale (but not here):
        '| Continuous |',
        # property name that is annotated in the TEST locale (but not here):
        '| **AssetTag** |',
        # Action parameter that is annotated in the TEST locale (but not here):
        '**ResetType** |',
        ]

    for x in expected_strings:
        assert x in output


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_localized_schemas_TEST_htmlmode(mockRequest):
    """ Verify that the test strings are output correctly when TEST is specified for the locale, in HTML output mode.
    """

    config = copy.deepcopy(base_config)
    config['locale'] = 'TEST'
    config['output_format'] = 'html'
    input_dir = os.path.abspath(testcase_path)

    config['uri_to_local'] = {'redfish.dmtf.org/schemas/v1': input_dir}
    config['local_to_uri'] = {input_dir : 'redfish.dmtf.org/schemas/v1'}

    docGen = DocGenerator([ input_dir ], '/dev/null', config)

    files_to_process = docGen.get_files(docGen.import_from)
    output = docGen.generate_docs()

    expected_strings = [
        # Examples of descriptions:
        'THE COMPUTERSYSTEM SCHEMA REPRESENTS A COMPUTER OR SYSTEM INSTANCE',
        'THE BOOTOPTIONREFERENCE OF THE BOOT OPTION TO PERFORM A ONE-TIME BOOT FROM WHEN BOOTSOURCEOVERRIDETARGET IS <code>UEFIBOOTNEXT</code>.',
        'THE NAME OF THE BOOT ORDER PROPERTY THAT THE SYSTEM USES FOR THE PERSISTENT BOOT ORDER.<br><i>FOR THE POSSIBLE PROPERTY VALUES, SEE <a href="#redfish.dmtf.org/schemas/v1/ComputerSystem.json|details|BootOrderPropertySelection">BootOrderPropertySelection</a> IN PROPERTY DETAILS.',
        '<td>AliasBootOrder</td><td>THE SYSTEM USES THE ALIASBOOTORDER PROPERTY TO SPECIFY THE PERSISTENT BOOT ORDER.</td>',
        # Example of enumTranslations:
        '<td>Continuous (CONTINUOUS)</td>',
        # property name with a translation annotation:
        '<td><nobr><b>AssetTag</b> <i>(Its Mine)</i></nobr></td>',
        # Action parameter with a translation annotation:
        '<nobr><b>ResetType</b> <i>(YOU WANNA RESET THIS THING)</i></nobr>',
        ]

    for x in expected_strings:
        assert x in output
