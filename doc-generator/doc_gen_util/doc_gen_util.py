#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
File: util.py

Brief: Utility method(s) needed by multiple doc generator classes.


Initial author: Second Rise LLC.
"""

import urllib.request
import json
import os
import re
import warnings

class DocGenUtilities:
    """ Redfish Documentation Generator Utilities. """

    timeout = 4 # Seconds for HTTP timeout

    @staticmethod
    def load_as_json(filename):
        """Load json data from a file, printing an error message on failure."""

        # We will generate an "unversioned" odata URI, which is not a thing that exists,
        # in order to group objects. This is a hack and should be eliminated.
        if '/odata.json' in filename:
            return None

        data = {}
        try:
            # Parse file as json
            jsondata = open(filename, 'r', encoding="utf8")
            data = json.load(jsondata)
            jsondata.close()
        except (OSError, json.JSONDecodeError) as ex:
            warnings.warn('Unable to read ' + filename + ': ' + str(ex))

        return data


    @staticmethod
    def http_load_as_json(uri):
        """Load a URI and convert from JSON"""

        try:
            if '://' not in uri:
                uri = 'http://' + uri

            # We will generate an "unversioned" odata URI, which is not a thing that exists,
            # in order to group objects. This is a hack and should be eliminated.
            if 'odata.json' in uri:
                return None

            f = urllib.request.urlopen(uri, None, DocGenUtilities.timeout)
            json_string = f.read().decode('utf-8')
            json_data = json.loads(json_string)
            return json_data

        except Exception as ex:
            warnings.warn("Unable to retrieve data from '" + uri + "': " + str(ex))
            return None


    @staticmethod
    def http_load(uri):
        """ Load URI and return response """
        try:
            if '://' not in uri:
                uri = 'http://' + uri

            f = urllib.request.urlopen(uri, None, DocGenUtilities.timeout)
            return f.read().decode('utf-8')

        except Exception as ex:
            warnings.warn("Unable to retrieve data from '" + uri + "': " + str(ex))
            return None


    @staticmethod
    def html_get_links(uri):
        """ Get the links from an HTML page at a URI """
        content = DocGenUtilities.http_load(uri)
        links = []

        if content:
            urlinfo = urllib.parse.urlparse(uri)
            urlpath = ''.join([urlinfo.scheme, '://', urlinfo.netloc])

            m = re.findall('href="([^"]+)"', content)
            for href in m:
                if re.match(r'\S+://', href):
                    links.append(href)
                elif href.startswith('/'):
                    links.append(''.join([urlpath, href]))
                else:
                    if uri.endswith('/'):
                        links.append(''.join([uri, href]))
                    else:
                        links.append('/'.join([uri, href]))

        return links


    @staticmethod
    def local_get_links(path):
        """ Get the file names with full paths at path """
        path = os.path.abspath(path)
        filenames = os.listdir(path)

        filenames = [os.path.join(path, x) for x in filenames]
        return filenames

    @staticmethod
    def compare_versions(version, context_version):
        """ Returns +1 if version is newer than context_version, -1 if version is older, 0 if equal """

        if version == context_version:
            return 0
        else:
            if '_' in version:
                sep = '_'
            else:
                sep = '.'
            version_parts = version.split(sep)
            if '_' in context_version:
                sep = '_'
            else:
                sep = '.'
            context_parts = context_version.split(sep)

            # versions are expected to have three parts, but fill in 0 if not
            while len(version_parts) < 3:
                version_parts.append("0")
            while len(context_parts) < 3:
                context_parts.append("0")
            for i in range(3):
                if int(version_parts[i]) > int(context_parts[i]):
                    return 1
                if int(version_parts[i]) < int(context_parts[i]):
                    return -1
            return 0


    @staticmethod
    def make_unversioned_ref(this_ref):
        """Get the un-versioned string based on a (possibly versioned) ref"""
        unversioned = None
        pattern = re.compile(r'(.+)\.v([^\.]+)\.json(#.+)?')
        match = pattern.fullmatch(this_ref)
        if not match and 'odata' in this_ref:
            pattern = re.compile(r'(.+/odata)\.(.+)\.json(#.+)?')
            match = pattern.fullmatch(this_ref)
        if match:
            unversioned = match.group(1) + '.json'
            if match.group(3):
                unversioned += match.group(3)

        return unversioned


    @staticmethod
    def get_ref_version(this_ref):
        """Get the version string based on a (possibly versioned) ref"""

        version_string = None
        pattern = re.compile(r'.+\.v([^\.]+)\.json.*')
        match = pattern.fullmatch(this_ref)
        if match:
            version_string = match.group(1)
            version_string = version_string.replace('_', '.')
        return version_string


    @staticmethod
    def get_payload_name(schema_name, version, action_name=None):

        major_version = version.split('.')[0]
        payload_name = schema_name + '-v' + major_version + '-'
        if action_name:
            payload_name += 'action-' + action_name + '.json'
        else:
            payload_name += 'example.json'

        return payload_name
