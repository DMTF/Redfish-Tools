#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File: util.py

Brief: Utility method(s) needed by multiple doc generator classes.


Initial author: Second Rise LLC.
"""

import urllib.request
import json
import re
import warnings

class DocGenUtilities:
    """ Redfish Documentation Generator Utilities. """

    timeout = 2 # Seconds for HTTP timeout

    @staticmethod
    def load_as_json(filename):
        """Load json data from a file, printing an error message on failure."""
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
            urlpath = ''.join([urlinfo.scheme, '://', urlinfo.hostname])

            m = re.findall('href="([^"]+)"', content)
            for href in m:
                if re.match('\s+://', href):
                    links.append(m)
                elif href.startswith('/'):
                    links.append(''.join([urlpath, href]))
                else:
                    if uri.endswith('/'):
                        links.append(''.join([uri, href]))
                    else:
                        links.append('/'.join([uri, href]))

        return links
