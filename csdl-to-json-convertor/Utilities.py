#!/usr/bin/python

"""
CSDL to JSON Convertor

The Distributed Management Task Force (DMTF) grants rights under copyright in
this software on the terms of the BSD 3-Clause License as set forth below; no
other rights are granted by DMTF. This software might be subject to other rights
(such as patent rights) of other parties.


Copyrights.

Copyright (c) 2016, Contributing Member(s) of Distributed Management Task Force,
Inc.. All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    Neither the name of the Distributed Management Task Force (DMTF) nor the
    names of its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


Patents.

This software may be subject to third party patent rights, including provisional
patent rights ("patent rights"). DMTF makes no representations to users of the
standard as to the existence of such rights, and is not responsible to
recognize, disclose, or identify any or all such third party patent right,
owners or claimants, nor for any incomplete or inaccurate identification or
disclosure of such rights, owners or claimants. DMTF shall have no liability to
any party, in any manner or circumstance, under any legal theory whatsoever, for
failure to recognize, disclose, or identify any such third party patent rights,
or for such party’s reliance on the software or incorporation thereof in its
product, protocols or testing procedures. DMTF shall have no liability to any
party using such software, whether such use is foreseeable or not, nor to any
patent owner or claimant, and shall have no liability or responsibility for
costs or losses incurred if software is withdrawn or modified after publication,
and shall be indemnified and held harmless by any party using the software from
any and all claims of infringement by a patent owner for such use.

DMTF Members that contributed to this software source code might have made
patent licensing commitments in connection with their participation in the DMTF.
For details, see http://dmtf.org/sites/default/files/patent-10-18-01.pdf and
http://www.dmtf.org/about/policies/disclosures.
"""

import http.client

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
                filename = directory + "\\" + filename

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
