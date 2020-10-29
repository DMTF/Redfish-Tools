# Copyright Notice:
# Copyright 2017-2020 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File : csv_generator.py

Brief : This file contains definitions for the CsvGenerator class.

Initial author: Second Rise LLC.
"""

import copy
import csv
import io
import warnings
from . import DocFormatter

class CsvGenerator(DocFormatter):
    """Provides methods for generating CSV docs from Redfish schemas."""


    def __init__(self, property_data, traverser, config, level=0):
        super(CsvGenerator, self).__init__(property_data, traverser, config, level)
        self.separators = {
            'inline': ', ',
            'linebreak': '\n',
            'pattern': ', '
            }
        self.output = io.StringIO()
        self.writer = csv.writer(self.output)
        self.schema_name = self.schema_version = ''

        if self.config.get('profile_mode'):
            headings = [
                _('Schema Name'),
                _('Schema Version'),
                _('Property Name (chain)'),
                _('Read Requirement'),
                _('Write Requirement'),
                _('Minimum Count'),
                _('Conditional Requirement'),
                _('Purpose'),
                _('Type'),
                _('Nullable'),
                _('Description'),
                _('Normative Description'),
                _('Units'),
                _('Minimum Value'),
                _('Maximum Value'),
                _('Enumerations'),
                _('Pattern'),
                '']
        else:
            headings = [
                _('Schema Name'),
                _('Schema Version'),
                _('Property Name (chain)'),
                _('Type'),
                _('Permissions'),
                _('Required'),
                _('Nullable'),
                _('Description'),
                _('Normative Description'),
                _('Units'),
                _('Minimum Value'),
                _('Maximum Value'),
                _('Enumerations'),
                _('Pattern'),
                '']
        self.writer.writerow(headings)


    def format_property_row(self, schema_ref, prop_name, prop_info, prop_path=[], in_array=False, as_action_parameters=False,
                                in_schema_ref=None):
        """Format information for a single property.

        Returns an object with 'row', 'details', and 'action_details':

        'row': content for the main table being generated.
        'details': content for the Property Details section.
        'action_details': content for the Actions section.

        This may include embedded objects with their own properties.
        CSV does not use depth, and instead includes the object path an extended name.
        """

        traverser = self.traverser
        row = []
        nextrows = []
        collapse_array = False # Should we collapse a list description into one row? For lists of simple types
        has_enum = False
        formatted_details = self.parse_property_info(schema_ref, prop_name, prop_info, prop_path)

        # Eliminate dups in these these properties and join with a delimiter:
        props = {
            'prop_type': self.separators['inline'],
            'descr': self.separators['linebreak'],
            'object_description': self.separators['linebreak'],
            'item_description': self.separators['linebreak']
            }

        for property_name, delim in props.items():
            if isinstance(formatted_details[property_name], list):
                property_values = []
                for val in formatted_details[property_name]:
                    if val and val not in property_values:
                        if isinstance(val, list): # this is a nested description; chain the property name
                            for elt in val:
                                elt[2] = '.'.join([prop_name, elt[2]])
                                nextrows.append(elt)
                        else:
                            property_values.append(val)
                formatted_details[property_name] = delim.join(property_values)

        prop_type = formatted_details['prop_type']
        prop_units = formatted_details['prop_units']

        profile_mode = self.config.get('profile_mode')
        if profile_mode:
            # profile_access = self.format_base_profile_access(formatted_details)
            profile_read_req = formatted_details.get('profile_read_req', '')
            profile_write_req = formatted_details.get('profile_write_req', '')
            profile_purpose = formatted_details['profile_purpose']
            profile_min_count = formatted_details.get('profile_mincount', '')
            profile_cond_req = ''
            cond_details = formatted_details.get('profile_conditional_details')
            if cond_details:
                profile_cond_req = cond_details.get(prop_name, '')

        long_description = formatted_details['normative_descr']
        description = formatted_details['non_normative_descr']

        if formatted_details['read_only']:
            permissions = 'RO'
        else:
            permissions = 'RW'
        if formatted_details['nullable']:
            nullable = 'Yes'
        else:
            nullable = 'No'

        required = ''
        if formatted_details['prop_required_on_create']:
            required = 'required on create'
        elif formatted_details['prop_required']:
            required = 'required'

        if isinstance(prop_info, list):
            p_i = prop_info[0]
        else:
            p_i = prop_info

        min_val = p_i.get('minimum', '')
        max_val = p_i.get('maximum', '')
        pattern = ''

        pattern = formatted_details.get('pattern')

        enumerations = ''
        if 'enum' in p_i:
            p_i['enum'].sort(key=str.lower)
            enumerations = ', '.join(p_i['enum'])

        schema_name = self.schema_name
        version = self.schema_version

        if profile_mode:
            row = [schema_name, version, prop_name, profile_read_req, profile_write_req, profile_min_count,
                   profile_cond_req, profile_purpose,
                   prop_type, nullable,
                   description, long_description, prop_units, min_val, max_val, enumerations, pattern]
        else:
            row = [schema_name, version, prop_name, prop_type, permissions, required, nullable,
                   description, long_description, prop_units, min_val, max_val, enumerations, pattern]
        rows = [row]
        for nextrow in nextrows:
            rows.append(nextrow)
        return { 'row': rows, 'details': {}, 'action_details': {} }


    def format_property_details(self, prop_name, prop_type, prop_description, enum, enum_details,
                                supplemental_details, parent_prop_info, profile={}):
        """Generate a formatted table of enum information for inclusion in Property Details."""

        # Property details are not included in CSV output.
        return ''


    def format_action_details(self, prop_name, action_details):
        """Generate a formatted Actions section.

        Currently, Actions details are entirely derived from the supplemental documentation."""
        # Action details are not included in CSV output.
        return ''


    def format_action_parameters(self, schema_ref, prop_name, prop_descr, action_parameters, profile):
        """Generate a formatted Actions section from parameters data"""
        # Action details are not included in CSV output.
        return ''


    def format_base_profile_access(self, formatted_details):
        """Massage profile read/write requirements for display. Override parent, omitting min_count. """

        if formatted_details.get('is_in_profile'):
            profile_access = self._format_profile_access(read_only=formatted_details.get('read_only', False),
                                                         read_req=formatted_details.get('profile_read_req'),
                                                         write_req=formatted_details.get('profile_write_req'),
                                                         min_count=None)
        else:
            profile_access = ''

        return profile_access


    def link_to_own_schema(self, schema_ref, schema_full_uri):
        """Format a reference to a schema."""
        result = super().link_to_own_schema(schema_ref, schema_full_uri)
        return result


    def link_to_outside_schema(self, schema_full_uri):
        """Format a reference to a schema_uri, which should be a valid URI"""
        return '['+ schema_full_uri + '](' + schema_full_uri + ')'


    def output_document(self):
        """Return full contents of document"""

        result = self.output.getvalue()
        self.output.close()
        return result


    def format_conditional_details(self, schema_ref, prop_name, conditional_reqs):
        """Generate a formatted Conditional Details section from profile data"""
        formatted = []

        for creq in conditional_reqs:
            req_desc = ''
            purpose = creq.get('Purpose', '')
            subordinate_to = creq.get('SubordinateToResource', '')
            compare_property = creq.get('CompareProperty', '')
            req = self.format_conditional_access(creq)

            if creq.get('BaseRequirement'):
                # Don't output the base requirement
                continue

            elif subordinate_to:
                req_desc = _('Resource instance is subordinate to %(phrase)s') % {'phrase': (' ' + _('from') + ' ').join('"' + x + '"' for x in subordinate_to)}

            if compare_property:
                comparison = creq.get('Comparison')
                if comparison in ['Equal', 'LessThanOrEqual', 'GreaterThanOrEqual', 'NotEqual']:
                    comparison += ' ' + _('to')

                compare_values = creq.get('CompareValues') or creq.get('Values') # Which is right?
                if compare_values:
                    compare_values = ', '.join('"' + x + '"' for x in compare_values)

                if req_desc:
                    req_desc += ' and '
                req_desc += _('"%(property)s" is %(comparison)s') % {'property': compare_property, 'comparison': comparison}

                if compare_values:
                    req_desc += ' ' + compare_values

            req_string = req_desc + ': ' + req
            if purpose:
                req_string += ' (' + purpose + ')'
            formatted.append(req_string)

        return "\n".join(formatted)


    def add_section(self, text, link_id=False, schema_ref=False):
        """ Rather than a top-level heading, for CSV we set the first column (schema name) """
        if ' ' in text:
            self.schema_name, self.schema_version = text.split(' ', 1)
        else:
            self.schema_name = text
            self.schema_version = ''
        self.this_section = {}

    def add_description(self, text):
        """  CSV omits schema description """
        pass


    def add_uris(self, uris):
        """ CSV omits URIs """
        pass


    def add_json_payload(self, json_payload):
        """ JSON payloads don't make sense for CSV  """
        if json_payload:
            warnings.warn("JSON payloads are ignored in CSV output")


    def add_property_row(self, rows):
        """ Add the row to the buffer. Unlike other formats, for CSV the argument is list of lists.  """
        for row in rows:
            self.writer.writerow(row)


    def add_registry_reqs(self, registry_reqs):
        """ CSV output doesn't include registry requirements. """
        pass
