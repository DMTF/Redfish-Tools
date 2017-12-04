#! /usr/local/bin/python3
# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
File: util.py

Brief: Utility method(s) needed by multiple doc generator classes.


Initial author: Second Rise LLC.
"""

import json
import warnings

class DocGenUtilities:
    """ Redfish Documentation Generator Utilities. """

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
