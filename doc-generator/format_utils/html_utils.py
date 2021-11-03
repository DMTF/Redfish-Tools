# Copyright Notice:
# Copyright 2018 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: html_utils.py

Brief : Contains output utilities for Doc Formatters that output HTML.

Initial author: Second Rise LLC.
"""
import markdown
from . import FormatUtils

class HtmlUtils(FormatUtils):

    @staticmethod
    def _head_base(text, level, anchor_id=None):
        if anchor_id:
            open_tag = '<h' + level + ' id="' + anchor_id + '">'
        else:
            open_tag = '<h' + level + '>'
        return open_tag + text + '</h' + level + '>'

    def head_one(self, text, level, anchor_id=None):
        """Add a top-level heading, relative to the generator's level"""
        level = str(level + 1)
        return self._head_base(text, level, anchor_id)

    def head_two(self, text, level, anchor_id=None):
        """ Make a second-level heading, relative to the current formatter level """
        level = str(level + 2)
        return self._head_base(text, level, anchor_id)

    def head_three(self, text, level, anchor_id=None):
        """ Make a third-level heading, relative to the current formatter level """
        level = str(level + 3)
        return self._head_base(text, level, anchor_id)

    def head_four(self, text, level, anchor_id=None):
        """ Make a fourth-level heading, relative to the current formatter level """
        level = str(level + 4)
        return self._head_base(text, level, anchor_id)

    def head_five(self, text, level, anchor_id=None):
        """ Make a fifth-level heading, relative to the current formatter level """
        level = str(level + 5)
        return self._head_base(text, level, anchor_id)


    @staticmethod
    def para(text):
        """ Format text as a paragraph """
        return "<p>" + text + "</p>"

    @staticmethod
    def bold(text):
        """Apply bold to text"""
        return '<b>' + text + '</b>'

    @staticmethod
    def italic(text):
        """Apply italic to text"""
        return '<i>' + text + '</i>'

    @staticmethod
    def br():
        """ Return a linebreak if in-cell linebreaks are supported. Assume they are not by default. """
        return '<br>'

    @staticmethod
    def nobr(text):
        """ Wrap a bit of text in nobr tags, for formats that supply that. """
        return '<nobr>' + text + '</nobr>'

    @staticmethod
    def nbsp():
        """ A non-breaking space, for formats that supply that """
        return '&nbsp;'

    @staticmethod
    def make_div(text, css_class=None):
        """ Make a div, optionally applying a css class """
        div = []
        if css_class:
            div.append('<div class="' + css_class + '">')
        else:
            div.append('<div>')
        div.append(text)
        div.append('</div>')
        return '\n'.join(div)

    def make_row(self, cells):
        """ Make an HTML row """
        row = ''.join(['<td>' + cell + '</td>' for cell in cells])
        return '<tr>' + row + '</tr>'

    def make_header_row(self, cells):
        """ Make an HTML row, using table header markup """
        row = ''.join(['<th>' + cell + '</th>' for cell in cells])
        return '<tr>' + row + '</tr>'

    def make_table(self, rows, header_rows=None, css_class=None, last_column_wide=False):

        """ Make an HTML table from the provided rows, which should be HTML markup """
        if header_rows:
            head = '<thead>\n' + '\n'.join(header_rows) + '\n</thead>\n'
        else:
            head = ''
        body = '<tbody>\n' + '\n'.join(rows) + '\n</tbody>'
        if css_class:
            table_tag = '<table class="' + css_class + '">'
        else:
            table_tag = '<table>'

        return table_tag + '\n' + head + body + '</table>'


    @staticmethod
    def markdown_to_html(markdown_blob, **args):
        """ Convert markdown to HTML """
        html_blob = markdown.markdown(markdown_blob,
                                      extensions=['markdown.extensions.codehilite',
                                                  'markdown.extensions.fenced_code',
                                                  'markdown.extensions.tables',
                                                  'markdown.extensions.toc'])
        # Look for empty table rows; used to get tables without headers recognized:
        if '<table>' in html_blob:
            lines = []
            html_updated = False
            in_thead = False
            thead_lines = []
            discard_thead = False
            for line in html_blob.splitlines():
                if in_thead:
                    if line == '</thead>':
                        thead_lines.append(line)
                        in_thead = False
                        if discard_thead:
                            html_updated = True
                        else:
                            [lines.append(x) for x in thead_lines]
                    elif line not in ['<tr>', '<th></th>', '</tr>']:
                        discard_thead = False
                        continue
                    else:
                        thead_lines.append(line)
                elif line == '<thead>':
                    in_thead = True
                    discard_thead = True
                    thead_lines = [line]
                    continue
                else:
                    lines.append(line)

            if html_updated:
                html_blob = '\n'.join(lines)

        elif args.get('no_para'):
            if html_blob[0:3] == '<p>':
                html_blob = html_blob[3:-4]

        return html_blob
