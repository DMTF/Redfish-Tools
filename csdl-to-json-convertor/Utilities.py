#!/usr/bin/python
# Copyright Notice:
# Copyright (C) 2016 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/LICENSE.md

"""
CSDL to JSON Convertor utilities
"""

import http.client
import os

class Utilities:

    #########################################################################################################
    # Name: show_interactive_mode                                                                           #
    # Description:                                                                                          #
    # Displays a form for input.                                                                            #
    # This method should be called when there is an error or user wants to generate the JSON                #
    # in an interactive fashion                                                                             #            
    #########################################################################################################
    @staticmethod
    def show_interactive_mode(error):
        result  = "Content-type: text/html\n"
        result += "\n"
        result += "<HTML>\n"
        result += " <HEAD>\n"
        result += "  <TITLE>\n"
        result += "   CSDL to JSON Convertor\n"
        result += "  </TITLE>\n"
        result += " </HEAD>\n"
        result += " <BODY>\n"
        result += "  <H1>CSDL to JSON Convertor</H1>\n"
        if error is not None:
            result += "Error: "
            result += error
            result += "\n"        
        result += "  <H2>Overview</H2>\n"
        result += "  <p> This service converts OData CSDL metadata files to JSON Schema equivalents.\n"
        result += "  <H2>Usage</H2>\n"
        result += "  <p> This service can be used in interactive mode or command mode.\n"
        result += "  <H3>Interactive Mode</H3>\n"
        result += "  <p> You are currently using the service's interactive mode.\n"
        result += "  From here, you can use the form below to request conversion of a CSDL metadata file\n"
        result += "  Simply type or paste the URL of the target CSDL Metadata file into the textbox and click Convert\n"
        result += "  <H3>Command Mode</H3>\n"
        result += "  <p> Make an HTTP GET request against a URL of the following form: <b>http://<i>service</i>?url=<i>URL</i>#<i>type</i></b>.\n"
        result += "  Here, <b><i>service</i></b> is the URL to this service (your browser's current address), <b><i>URL</i></b> is the URL of the CSDL Metadata and <b><i>type</i></b> is the type for which to return a JSON Schema representation.\n"
        result += "  Make sure you accept the <b>application/json</b> content type.\n"
        result += "  <FORM target=\"service.py\">\n"
        result += "   URL: <input name=\"url\" type=\"text\" size=\"100\" /> \n"
        result += "   <input name=\"submitBtn\" type=\"submit\" value=\"Convert\" />\n"
        result += "  </FORM>\n"
        result += " </BODY>\n"
        result += "</HTML>\n"
    
        return result


    #################################################################
    # Name: open_url                                                #
    # Description:                                                  #
    # Opens the target file and extracts data from it.              #
    #################################################################
    @staticmethod
    def open_url(url, directory):

	#temp hack to always open from file
        if( url.find("OData") < 0 ):
            decoded = Utilities.open_as_file(url, directory)
            return decoded

        # TODO: handle cases where URL is malformed
        try:
            connections = {}
            hostStart = url.find("//")
            prefix = url[:hostStart]
            hostStop = url.find("/", hostStart + 2)
            hostname = url[hostStart + 2 : hostStop]
            resname  = url[hostStop :]
            
            if hostname in connections.keys():
                conn = connections[hostname]
            else:
                conn = http.client.HTTPConnection(hostname)
                connections[hostname] = conn

            conn.request("GET", resname)
            response = conn.getresponse()
            data = response.read()
            decoded = data.decode("utf-8")

            if response.status != 200:
                decoded = Utilities.open_as_file(url, directory)

        except:
            decoded = Utilities.open_as_file(url, directory)

        return decoded


    #################################################################
    # Name: open_as_file                                            #
    # Description:                                                  #
    # Opens the target file and extracts data from it.              #
    #################################################################
    @staticmethod
    def open_as_file(url, directory):

        try:
            filelocation = url.rfind("/")
            if(filelocation > 0):
                filename=url[filelocation+1:]
            else:
                filename=url

            if(len(directory) > 0 ):
                filename = directory + os.path.sep + filename

            metafile = open(filename)
            decoded = metafile.read()

        except:
            decoded = ""
            print("failed to open " + url + " as " + filename)

        return decoded

    #################################################################
    # Name: indent                                                  #
    # Description:                                                  #
    # Enumeration for various scenarios                             #
    #################################################################
    @staticmethod
    def indent(depth) :
        return "    " * depth
