# Copyright Notice:
# Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : toc_parser.py

Brief : Parser to generate TOC from HTML text.

Initial author: Second Rise LLC.
"""
from html.parser import HTMLParser

class ToCParser(HTMLParser):

    def __init__(self, levels=None):
        super(ToCParser, self).__init__()
        self.toc = []
        self.current = None
        if levels:
            self.levels = levels
        else:
            self.levels = ['h2']

    def handle_starttag(self, tag, attrs):
        if tag in self.levels:
            for attr in attrs:
                if attr[0] == 'id' and attr[1] :
                    self.current = { 'level': tag, 'link_id': attr[1], 'text': '' }
                    break

    def handle_data(self, data):
        if self.current:
            self.current['text'] += data


    def handle_endtag(self, tag):
        if self.current and self.current['level'] == tag:
            self.toc.append(self.current)
            self.current = None

    def close(self):
        if self.current:
            self.toc.append(self.current)
            self.current = None

        return self.toc
