# Copyright Notice:
# Copyright 2021 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : parse_md_supplement.py

Provides parsing functionality for supplemental schema documents used
with the Redfish documentation generator.

Initial author: Second Rise LLC.
"""

import re
import os.path
import warnings

def parse_markdown_supplement(filehandle, filename):
    """Parse a supplemental markdown file. Returns a dict. """

    parsed = {}
    text = []
    current_item = None


    # Possible top-level headings:
    possible_h1s = ['Schema-Description', 'Schema-Intro', 'Schema-Postscript', 'Property-Details', 'Action-Details']

    # First pass: split into chunks by main heading:
    for raw_line in filehandle:
        line = raw_line.strip('\r\n') # Keep other whitespace
        if line.startswith('#--'):
            if current_item:
                current_content = '\n'.join(text)
                parsed[current_item] = current_content.strip()
            text = []
            next_item = line[3:].strip()
            if next_item in possible_h1s:
                current_item = next_item
            else:
                current_item = None
                warnings.warn('Found an unrecognized heading in %(filename)s: "%(line)s"' % {'filename': filename, 'line': raw_line})

        elif current_item:
            text.append(line)

    return parsed
