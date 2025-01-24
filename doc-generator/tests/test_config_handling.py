# Copyright Notice:
# Copyright 2019-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File: test_config_handling.py

Brief: test(s) for correct handling of config options from multiple sources

Users can specify parameters on the command line, and in two json-formatted config files.
These tests validate that parameters are correctly
combined into a single config dictionary, and for parameters that are specified in more than one place,
the command line takes precedence, followed by the config file and finally the supplemental file.
"""

import os
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator


base_cli_args = {
    "config_file": "../Redfish-Tools/doc-generator/sample_inputs/config_for_standard_html.json",
    "import_from": ['/cli/path/to/schemas'],
    "normative": True,
    "format": 'markdown',
    "outfile": "cli_outfile_name.md",
    "payload_dir": "/cli/path/to/payloads",
    "profile_doc": None,
    "profile_terse": False,
    "subset_doc": None,
    "property_index": False,
    "property_index_config_out": None,
    "escape_chars": '@#'
}

base_cfg_in = {
    "html_title": "Title from config",
    "format": "html",
    "import_from": [ "/config/path/to/schemas" ],
    "outfile": "config_outfile_name.html",
    "payload_dir": "/config/path/to/payloads",
    "actions_in_property_table": True,
    "local_to_uri": {
        "/config/path/to/json-schema": "redfish.dmtf.org/schemas/v1"
    },
    "uri_to_local": {
        "redfish.dmtf.org/schemas/v1": "/config/path/to/json-schema"
    },
    "units_translation": {
        "s": "s_from_cfg",
        "Mb/s": "Mb/s_from_cfg",
    }
}

@pytest.mark.filterwarnings('ignore:Schema URI Mapping')
def test_config_keys():
    """ Ensure expected keys are present in config, even if no config input is provided.

    Really, this test just specifies what the DocFormatter classes can rely on having in
    config.
    """

    expected_keys = [
        "actions_in_property_table",
        "cwd",
        "escape_chars",
        "excluded_annotations",
        "excluded_annotations_by_match",
        "excluded_by_match",
        "excluded_pattern_props",
        "excluded_properties",
        "excluded_schemas",
        "excluded_schemas_by_match",
        "import_from",
        "local_to_uri",
        "normative",
        "omit_version_in_headers",
        "outfile_name",
        "output_content",
        "output_format",
        "profile",
        "profile_doc",
        "profile_mode",
        "profile_resources",
        "profile_uri_to_local",
        "schema_supplement",
        "units_translation",
        "schema_link_replacements",
        "uri_to_local",
        "wants_common_objects",
    ]

    config = DocGenerator.combine_configs()
    for key in expected_keys:
        assert key in config


@pytest.mark.filterwarnings('ignore:Schema URI Mapping')
def test_config_defaults():
    """ Ensure expected defaults are set in config, even if no config input is provided.

    """
    cwd = os.getcwd()

    config = DocGenerator.combine_configs()
    assert config['output_format'] == 'slate'
    assert config['output_content'] == 'full_doc'
    assert config['outfile_name'] == 'output.md'
    assert config['cwd'] == cwd

    # import_from should be a list, in this case of one path, to "json-schema" within cwd.
    assert isinstance(config['import_from'], list)
    import_from = config['import_from'].pop()
    assert import_from.startswith(cwd)
    assert import_from.endswith('json-schema')


@patch('sys.exit') # Doc generator warns and exits when some specified paths are not valid on the filesystem.
@pytest.mark.filterwarnings("ignore:\"/config/path/to/payloads\" is not a directory. Exiting.")
def test_config_only(mock_exit):
    """ Test that config is something reasonable when only the config file data is supplied.

    Note: there is no real-world use case where command-line arguments will not be supplied,
    but this test does some work in verifying that values from the config file are carried over.
    """
    cfg = base_cfg_in.copy()
    config = DocGenerator.combine_configs(config_data=cfg)

    assert config.get('local_to_uri') == {
        "/config/path/to/json-schema": "redfish.dmtf.org/schemas/v1"
    }
    assert config.get('uri_to_local') == {
        "redfish.dmtf.org/schemas/v1": "/config/path/to/json-schema"
    }
    assert config.get('units_translation') == {
        "s": "s_from_cfg",
        "Mb/s": "Mb/s_from_cfg",
    }
    assert config.get('html_title') == "Title from config"
    assert config.get('wants_common_objects') == False
    assert config.get('actions_in_property_table') == True
    assert config.get('import_from') == ['/config/path/to/schemas']
    assert config.get('outfile_name') == 'config_outfile_name.html'
    assert config.get('output_format') == 'html'


@patch('sys.exit') # Doc generator warns and exits when some specified paths are not valid on the filesystem.
@pytest.mark.filterwarnings("ignore:\"/config/path/to/payloads\" is not a directory. Exiting.")
def test_config_cannot_set_common_objects(mock_exit):
    """ Test that config file cannot set wants_common_objects to True.

    Since common object (a.k.a. common property) collection only makes sense if there is
    a place to output the results, it wants_common_objects can be set only by the
    data parsed from the supplemental markdown file.
    """
    cfg = base_cfg_in.copy()
    cfg['wants_common_objects'] = True
    config = DocGenerator.combine_configs(config_data=cfg)

    assert config.get('wants_common_objects') == False


@patch('sys.exit') # Doc generator warns and exits when some specified paths are not valid on the filesystem.
@pytest.mark.filterwarnings("ignore:\"/cli/path/to/payloads\" is not a directory. Exiting.")
def test_cli_overrides_config(mock_exit):
    """ Verify that if some parameters are specified in both the config file and the command line,
    the values from the command line are used.
    """

    cli_args = base_cli_args.copy()
    cfg = base_cfg_in.copy()

    config = DocGenerator.combine_configs(command_line_args=cli_args, config_data=cfg)

    assert config.get('import_from') == ['/cli/path/to/schemas']
    assert config.get('outfile_name') == 'cli_outfile_name.md'
    assert config.get('output_format') == 'markdown'
    assert config.get('escape_chars') == ['@', '#']
