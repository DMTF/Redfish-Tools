# Copyright Notice:
# Copyright 2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/main/LICENSE.md

"""
File : parse_md_supplement.py

Provides parsing functionality for supplemental schema documents used
with the Redfish documentation generator.

Initial author: Second Rise LLC.
"""

import re
import os.path
import warnings

def parse_markdown_supplement(data, filename):
    """Parse a supplemental markdown file. Returns a dict. """

    # Possible top-level headings:
    possible_h1s = ['description', 'jsonpayload', 'property_details', 'action_details']
    parsed = _parse_blob(data, marker='#--', filename=filename, limit_headings=possible_h1s)

    if parsed.get('property_details'):
        parsed['property_details'] = _parse_blob(parsed['property_details'], filename=filename, marker="##--")


    if parsed.get('action_details'):
        parsed['action_details'] = _parse_blob(parsed['action_details'], filename=filename, marker="##--")


    return parsed


def _parse_blob(blob, marker='#--', filename=None, limit_headings=None):

    marker_len = len(marker)
    text = []
    current_item = None
    parsed = {}

    # First pass: split into chunks by main heading:
    for raw_line in blob.splitlines():
        line = raw_line.strip('\r\n') # Keep other whitespace
        if line.startswith(marker):
            if current_item:
                current_content = '\n'.join(text)
                parsed[current_item] = current_content.strip()
            text = []
            next_item = line[marker_len:].strip()
            if limit_headings and next_item not in limit_headings:
                current_item = None
                warnings.warn('Found an unrecognized heading in %(filename)s: "%(line)s"' % {'filename': filename, 'line': raw_line})
            else:
                current_item = next_item

        elif current_item:
            text.append(line)

    # At end of loop, we likely have a current item waiting to be saved:
    if current_item:
        current_content = '\n'.join(text)
        parsed[current_item] = current_content.strip()

    return parsed
