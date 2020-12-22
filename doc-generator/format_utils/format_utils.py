# Copyright Notice:
# Copyright 2018-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: format_utils.py

Brief : Contains output utilities for Doc Formatters (generic class; implements markdown).

Initial author: Second Rise LLC.
"""

class FormatUtils():

    last_caption = ""

    def head_one(self, text, level, anchor_id=None):
        """Add a top-level heading, relative to the generator's level"""
        add_level = '' + '#' * level
        return add_level + '# ' + text + "\n"

    def head_two(self, text, level, anchor_id=None):
        """Add a second-level heading, relative to the generator's level"""
        add_level = '' + '#' * level
        return add_level + '## ' + text + "\n"

    def head_three(self, text, level, anchor_id=None):
        """Add a third-level heading, relative to the generator's level"""
        add_level = '' + '#' * level
        return add_level + '### ' + text + "\n"

    def head_four(self, text, level, anchor_id=None):
        """Add a fourth-level heading, relative to the generator's level"""
        add_level = '' + '#' * level
        return add_level + '#### ' + text + "\n"

    def head_five(self, text, level, anchor_id=None):
        """Add a fifth-level heading, relative to the generator's level"""
        add_level = '' + '#' * level
        return add_level + '##### ' + text + "\n"

    @staticmethod
    def para(text):
        """ Format text as a paragraph """
        return "\n" + text + "\n"

    @staticmethod
    def make_paras(text):
        """ For some formats, will split text at linebreaks and output as paragraphs """
        return text

    @staticmethod
    def bold(text):
        """Apply bold to text"""
        return '**' + text + '**'

    @staticmethod
    def italic(text):
        """Apply italic to text"""
        return '*' + text + '*'

    @staticmethod
    def br():
        """ Return a linebreak if in-cell linebreaks are supported. Assume they are not by default. """
        return ' '

    @staticmethod
    def nobr(text):
        """ Wrap a bit of text in nobr tags, for formats that supply that. """
        return text

    @staticmethod
    def nbsp():
        """ A non-breaking space, for formats that supply that """
        return '  '

    def make_row(self, cells):
        row = '| ' + ' | '.join(cells) + ' |'
        return row

    def make_header_row(self, cells):
        return self.make_row(cells)

    def _make_separator_row(self, num):
        return self.make_row(['---' for x in range(0, num)])

    def make_table(self, rows, header_rows=None, css_class=None):

        # Get the number of cells from the first row.
        firstrow = rows[0]
        numcells = firstrow.count(' | ') + 1
        if not header_rows:
            header_rows = [ self.make_header_row(['   ' for x in range(0, numcells)]) ]
        header_rows.append(self._make_separator_row(numcells))

        return '\n'.join(['\n'.join(header_rows), '\n'.join(rows)])

    def add_table_caption(self, caption):
        self.last_caption = caption
        return _('Table') + ': ' + _('Table') + ' TBL_nn: <a name=table_TBL_nn>' + caption + '</a>'

    def add_table_reference(self, lead_in):
        return lead_in + '[' + _('Table') + ' TBL_nn++](#table_TBL_nn \"' + self.last_caption + '\").'
