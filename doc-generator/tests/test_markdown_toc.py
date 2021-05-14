# Copyright Notice:
# Copyright 2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: test_markdown_toc.py

Brief: Test(s) of TOC generation in markdown output.
"""

import os
import copy
from unittest.mock import patch
import pytest
from doc_generator import DocGenerator
from doc_formatter import MarkdownGenerator

testcase_path = os.path.join('tests', 'samples', 'markdown_toc')

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
    'add_toc': True,
}


@patch('urllib.request') # so we don't make HTTP requests. NB: samples should not call for outside resources.
def test_markdown_toc_basic(mockRequest):
    ''' Checks for expected output strings (table of contents and anchors in headings) for a basic case. '''

    config = copy.deepcopy(base_config)

    input_blob = '''
These are some example headings.

# Head 1

Some text and stuff.

## Head 2

Some text and stuff.

## Another head 2

Some text and stuff.
Some text and stuff.

### Head 3

(Head 3 will not appear in the TOC.)

# Head 1 the second

Some text and stuff.

## And one last head 2

fin.
'''

    expected_toc = '''
- [Head 1](#head-1)

   - [Head 2](#head-2)

   - [Another head 2](#another-head-2)

- [Head 1 the second](#head-1-the-second)

   - [And one last head 2](#and-one-last-head-2)
'''

    expected_anchors = [
        '# <a name="head-1"></a>Head 1',
        '## <a name="head-2"></a>Head 2',
        '## <a name="another-head-2"></a>Another head 2',
        '# <a name="head-1-the-second"></a>Head 1 the second',
        '## <a name="and-one-last-head-2"></a>And one last head 2'
        ]

    doc_formatter = MarkdownGenerator({}, None, {}, 0)
    output = doc_formatter.generate_and_add_toc(input_blob)

    assert expected_toc in output
    for anchor in expected_anchors:
        assert anchor in output
