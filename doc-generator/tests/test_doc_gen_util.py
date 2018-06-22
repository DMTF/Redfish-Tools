# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

import os
import urllib.request
import pytest
from unittest.mock import patch
from doc_gen_util import DocGenUtilities

sampledir = os.path.join('tests', 'samples', 'json')

def test_load_as_json():
    data = DocGenUtilities.load_as_json(os.path.join(sampledir, '1.json'))
    assert data['foo'] == 'bar' and data['baz'] == ['foo', 'bar', 'baz']

def test_load_as_json_file_not_found_warns():
    with pytest.warns(UserWarning):
        data = DocGenUtilities.load_as_json(os.path.join(sampledir, '404.json'))
        assert data == {}

def test_load_as_json_file_not_good_warns():
    with pytest.warns(UserWarning):
        data = DocGenUtilities.load_as_json(os.path.join(sampledir, 'badjson.json'))
        assert data == {}


@patch('urllib.request')
def test_html_get_links(mockRequest):
    sampleFile = open(os.path.join('tests', 'samples', 'schema_index_sample.html'), 'rb')
    expected_links = ['http://www.dmtf.org/standards/redfish',
                      'https://testing.mock/schemas/AccountService.v1_3_0.json',
                      'https://testing.mock/schemas/AccountService_v1.xml',
                      'https://testing.mock/schemas/ActionInfo.v1_0_3.json',
                      'https://testing.mock/schemas/ActionInfo_v1.xml']
    mockRequest.urlopen.return_value = sampleFile
    links = DocGenUtilities.html_get_links("https://testing.mock/foo.html");
    links.sort()
    assert links == expected_links
