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

import cgi
import cgitb
import sys
import xml.etree.ElementTree as ET
import Utilities as UT
import os
import argparse
import configparser

# Enable the printing of error information
#cgitb.enable()
enable_debugging = False

if enable_debugging == True:
    import pdb

###############################################################################
# Name: Constants                                                             #
# Description:                                                                #
#   Defines constants used in the script                                      #
###############################################################################

schemaLocation = "http://redfish.dmtf.org/schemas/" 
schemaBaseLocation = schemaLocation + "v1/"
odataSchema = schemaBaseLocation + "odata.4.0.0.json"
redfishSchema = schemaLocation + "v1/redfish-schema.v1_1_0.json"

#########################################################################################################
# Class Name: JsonSchemaGenerator                                                                       #
# Description:                                                                                          #
#  This class to performs conversion of CSDL (XML) schema into JSON schema.                             #
#########################################################################################################
class JsonSchemaGenerator:

    # Static member variables
    schemaname = ''                     # Schema name for which the generation is being done
    parsed = []                         # List of URIs that have been parsed
    current_schema_classname = ''       # Class for which the schema is being generated
    definition_block_contents = []

    #################################################################
    # Name: __init__                                                #
    # Description:                                                  #
    #   Constructor for JsonSchemaGeneratorUtils class              #
    #################################################################
    def __init__(self, schema_name_value):

        JsonSchemaGenerator.schemaname = schema_name_value

    ########################################################################################################
    # Name: get_ref_value_for_type                                                                         #
    # Description:                                                                                         #
    #  Generate the value of ref based on the name of the type and namespace/file of the type              #
    ########################################################################################################
    def get_ref_value_for_type(self, typetable, current_typename, root_namespace):

        refvalue = ""
        current_typedata = typetable[current_typename]

        # get the most recent version of this type less than or equal to the current namespace
        current_namespace = current_typedata["Namespace"]
        if(current_namespace.find(".") > 0) :
            current_namespace = self.get_current_namespace(current_typedata["Name"], current_namespace, root_namespace, typetable)

        typetype = current_typedata["TypeType"]
        simplename = current_typedata["Name"]

#todo: fix logic to be more generic post-v1
        # If the current type is defined in this namespace
        if (current_typename == "Resource.Item") :
            refvalue = odataSchema + "#/definitions/idRef"
        elif ( typetype != "Action" and self.include_type(simplename, current_namespace, root_namespace, typetable ) ) or (typetype == "Action" and self.include_type(simplename, current_typedata["BoundNamespace"], root_namespace, typetable) ):
            refvalue = "#/definitions/" + simplename
        else:
            refvalue = schemaBaseLocation + current_typedata["Alias"] + ".json#/definitions/" + simplename

        return refvalue

    #################################################################################
    # Name: extract_filenamefrom_url                                                #
    # Description:                                                                  #
    #  The method consumes a URL and extracts filename from it. The implementation  #
    #  is tightly bound to the format in which URL is expected.                     #
    #################################################################################
    @staticmethod
    def extract_filenamefrom_url(url):
    
        url_parts = url.rsplit("/", 1)
        return url_parts[-1]

    ############################################################################################
    # Name: get_typename_without_namespace                                                     #
    # Description:                                                                             #
    #   The method consumes a typename and returns strips out the namespace name.              #
    #   The name of the type excluding the namespace name is returned back.                    #
    #   The implementation is tightly bound to the format in which the type names are defined. #
    ############################################################################################
    @staticmethod
    def get_typename_without_namespace(fullyqualifiedtypename):
        
        typename_parts = fullyqualifiedtypename.rsplit('.', 1)
        return typename_parts[-1]

    ###############################################################################################################
    # Name: extract_underlyingtype_from_collectiontype                                                            #
    # Description:                                                                                                #
    #  Takes name of the collection type and returns the underlying type for which the colleciton was created.    #
    #  Based on the input, the return value might or might not contain the namespace of the underlying type       #
    ###############################################################################################################
    @staticmethod
    def extract_underlyingtype_from_collectiontype(collection_typename, excludenamespace = False):
    
        underlyingtype = collection_typename
        if(collection_typename.startswith("Collection(")):
            underlyingtype = collection_typename[11:]
            underlyingtype = underlyingtype[:-1]

            if excludenamespace == True:
                underlyingtype_parts = underlyingtype.rsplit('.', 1)
                underlyingtype = underlyingtype_parts[-1]

        # Return the processed value. If the typename did not contain "Collection" keywork, it will be returned as-is
        return underlyingtype

    #################################################################
    # Name: is_inline_type                                          #
    # Description:                                                  #
    #  Returns True if property should be written inline            #
    #################################################################
    def is_inline_type(self, type, typetable):

        if( not(self.has_basetype(typetable, type, "Resource.Links")) and type["Name"] != "Actions" and type["Name"] != "OemActions" ):
            return True;

        return False

    #################################################################
    # Name: is_collection                                           #
    # Description:                                                  #
    #  Returns True if type is a collection type                    #
    #################################################################
    def is_collection(self, typename):
        return typename.startswith("Collection(")

    ##########################################################################
    # Name: is_required_property                                             # 
    # Description:                                                           #
    #  Returns True if the property being evaulated is a required property.  #
    ##########################################################################
    def is_required_property(self, property):

        for annotation in property:
            if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                continue

            if annotation.attrib["Term"] == "Redfish.Required":
                if "Bool" in annotation.attrib.keys():
                    if annotation.attrib["Bool"] == "false":
                        break

                return True

        return False

    ##########################################################################
    # Name: is_redfish_enum                                                  # 
    # Description:                                                           #
    #  Returns True if the type has the Redfish enum annotation.             #
    ##########################################################################
    def is_redfish_enum(self, type):

        for annotation in type:
            if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                continue

            if annotation.attrib["Term"] == "Redfish.Enumeration":
                if "Bool" in annotation.attrib.keys():
                    if annotation.attrib["Bool"] == "false":
                        break
                return True

        return False

    ##########################################################################
    # Name: has_basetype                                                     # 
    # Description:                                                           #
    #  Returns True if the type has the specified base type n its hierarchy. #
    ##########################################################################
    def has_basetype(self, typetable, type, basetype):

        # does it have the base type anywhere in it's hierarchy?
        while True:
            if "BaseType" in type["Node"].attrib.keys():
                basetypename = type["Node"].attrib["BaseType"]
                if basetypename == basetype:
                    return True
                else:
                    if basetypename == type["Namespace"] + "." + type["Name"]:
                        print("Circular Reference Error in base type of " + basetypename )
                        return False
                    else:
                       type = typetable[basetypename]
            else:
                break

        # by default, types allow additional properties
        return False

    ##########################################################################
    # Name: isabstract                                                       # 
    # Description:                                                           #
    #  Returns True if the type is abstract.                                 #
    ##########################################################################
    def isabstract(self, type):
        return self.getattribute(type,"Abstract","true") 		   

    ##########################################################################
    # Name: getattribute                                                     # 
    # Description:                                                           #
    #  Returns True if the type has the attribute with the specfied value    #
    ##########################################################################
    def getattribute(self, type, attribute, value):
        if attribute in type["Node"].attrib.keys():
            if type["Node"].attrib[attribute].upper() == value.upper():
                return True
        return False 		   

    ##########################################################################
    # Name: allows_additional_properties                                     # 
    # Description:                                                           #
    #  Returns True if the type allows additional properties.                #
    ##########################################################################
    def allows_additional_properties(self, type, typetable):

        # if type is abstract, it must allow additional properties
        if self.isabstract(type):
            return True
				
        # does it have the AdditionalProperties attribute anywhere in it's hierarchy?
        while True:
            for annotation in type["Node"]:
                if annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                    if annotation.attrib["Term"] == "OData.AdditionalProperties":
                        if "Bool" in annotation.attrib.keys():
                            if annotation.attrib["Bool"] == "false":
                                return False
                            else:
                                return True
                        else:
                            return True
								 
            if "BaseType" in type["Node"].attrib.keys():
                basetypename = type["Node"].attrib["BaseType"]
                if basetypename in typetable:
                    type = typetable[basetypename]
                else:
                    break
            else:
                break

        # by default, types allow additional properties
        return True

    ##########################################################################
    # Name: is_requiredOnCreate_property                                     # 
    # Description:                                                           #
    #  Returns True if the property being evaulated is required on create.   #
    ##########################################################################
    def is_requiredOnCreate_property(self, property):

        for annotation in property:
            if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                continue

            if annotation.attrib["Term"] == "Redfish.RequiredOnCreate":
                if "Bool" in annotation.attrib.keys():
                    if annotation.attrib["Bool"] == "false":
                        break

                return True

        return False
		
    #####################################################################################
    # Name: get_dynamic_property_patterns_content                                       # 
    # Description:                                                                      #
    #  Parses the contents of the XML and return contents of a dynamic property pattern #
    #####################################################################################
    def get_dynamic_property_patterns_content(self, annotation):
    
        patterncontent = []
        for collection in annotation:
            for record in collection:
                pattern = {}
                for propertyvalue in record:
                    pattern.update({propertyvalue.attrib["Property"] : propertyvalue.attrib["String"]})
                patterncontent.append(pattern)

        return patterncontent

    ##########################################################################
    # Name: get_edmtype_to_jsontype                                          # 
    # Description:                                                           #
    #  Takes a type and returns the corresponding json type                  #
    ##########################################################################
    def get_edmtype_to_jsontype(self, inputType):
    
        edmtojson = {
                        "Edm.String": "string",
                        "Edm.Int16": "number",
                        "Edm.Int32": "number",
                        "Edm.Int64": "number",
                        "Edm.Boolean": "boolean",
                        "Edm.Decimal": "number",
                        "Edm.DateTimeOffset": "string",
                        "Edm.Primitive": "primitive"
                    }

        if not inputType in edmtojson:
            return "object"
    
        return edmtojson[inputType]

    ##########################################################################
    # Name: emit_property_patterns                                           # 
    # Description:                                                           #
    #  Emits any property patterns on the object                             #
    ##########################################################################
    def emit_property_patterns(self, typetable, namespace, annotated, depth, prefixuri):

        output = ""
        fcontinue = True
        written = []

        #for each type in the heirarchy
        while ( fcontinue == True ):
            for annotation in annotated:
                if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                    continue

                term = annotation.attrib["Term"]

                if term == "Redfish.DynamicPropertyPatterns":
                    content = self.get_dynamic_property_patterns_content(annotation)
                    for record in content:
                        output += ",\n"
                        output += UT.Utilities.indent(depth+1) + "\"" + record["Pattern"] + "\": {\n"
                        jsontype = self.get_edmtype_to_jsontype(record["Type"])
                        if jsontype == "object":
                            refvalue = self.get_ref_value_for_type(typetable, record["Type"], namespace)
                            output += UT.Utilities.indent(depth+2)+ "\"$ref\": \"" + refvalue + "\""                        
                        elif jsontype == "primitive":
#Assume DynamicPropertyPatterns primitive types can be nullable
                            output += self.write_primitive_type(depth+2, True)
                        else:
                            output += UT.Utilities.indent(depth + 2) + "\"type\": \"" + jsontype + "\""

                        output += "\n" + UT.Utilities.indent(depth + 1) + "}"
                                                     
            if "BaseType" in annotated.attrib.keys():
                #todo: make more robust
                annotated = typetable[annotated.attrib["BaseType"]]["Node"]
            else:
                fcontinue = False

        return output

    ##########################################################################
    # Name: emit_annotations                                                 # 
    # Description:                                                           #
    #  Emits annotations that are to be added to JSON                        #
    ##########################################################################
    def emit_annotations(self, typetable, namespace, annotated, depth, prefixuri, isnullable = False, ignoreannotations = [], isTypeAttribute=False):

        output = ""
        fcontinue = True
        written = []

        #for each type in the heirarchy
        while ( fcontinue == True ):
            for annotation in annotated:
                if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                    continue

                term = annotation.attrib["Term"]

                if ( (term in ignoreannotations) or (term in written ) ):
                    continue

                #don't add annotation more than once'
                written.append(term)

                if(isTypeAttribute):

                    if (term == "Redfish.Deprecated"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"deprecated\": \"" + annotation.attrib["String"] + "\"" 														                                                     

                    elif (term == "Measures.Unit"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"units\": \"" + annotation.attrib["String"] + "\"" 

                    elif ((term == "Validation.Pattern") or (term == "Redfish.Pattern") ):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"pattern\": \"" + annotation.attrib["String"] + "\""

                    elif (term == "Validation.Minimum"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"minimum\": " + annotation.attrib["Int"]

                    elif (term == "Validation.Maximum"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"maximum\": " + annotation.attrib["Int"]

                    elif (term == "OData.IsURL"):
                        if (not ("Bool" in annotation.attrib.keys() and annotation.attrib["Bool"] == "false")):
                            output += ",\n"
                            output += UT.Utilities.indent(depth) + "\"format\": \"uri\"" 
							                                                     
                else:
                    if (term == "OData.Description"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"description\": \"" + annotation.attrib["String"] + "\""

                    elif (term == "OData.LongDescription"):
                        output += ",\n"
                        output += UT.Utilities.indent(depth) + "\"longDescription\": \"" + annotation.attrib["String"] + "\""

                    elif (term == "OData.Permissions"):
                        if annotation.attrib["EnumMember"] == "OData.Permission/Read" or annotation.attrib["EnumMember"] == "OData.Permissions/Read":
                            output += ",\n"
                            output += UT.Utilities.indent(depth) + "\"readonly\": true"
                        elif annotation.attrib["EnumMember"] == "OData.Permission/ReadWrite" or annotation.attrib["EnumMember"] == "OData.Permissions/ReadWrite":
                            output += ",\n"
                            output += UT.Utilities.indent(depth) + "\"readonly\": false"

            if "BaseType" in annotated.attrib.keys():
                #todo: make more robust
                annotated = typetable[annotated.attrib["BaseType"]]["Node"]

            else:
                fcontinue = False

        return output


    ###################################################################################################
    # Name: get_property_annotation_terms                                                             #
    # Description:                                                                                    #
    #  Extracts Term from the annotations                                                             #
    ###################################################################################################
    def get_property_annotation_terms(self, property):

        result = []

        for annotation in property:
            if not annotation.tag == "{http://docs.oasis-open.org/odata/ns/edm}Annotation":
                continue

            result.append(annotation.attrib["Term"])

        return result


    #########################################################################################################
    # Name: get_payload_actionentry                                                                         #
    # Description:                                                                                          #
    #  Generates JSON for actions                                                                           #
    #########################################################################################################
    def get_payload_actionentry(self, typetable, actionentry, depth, prefixuri, namespace):
        output = ""
        
        actionname = actionentry["Namespace"] + "." + actionentry["Name"]
        propertyname = "#" + actionname
        refvalue = self.get_ref_value_for_type(typetable, actionname, namespace )

        output += UT.Utilities.indent(depth)   + "\"" + propertyname + "\": {\n"
        output += UT.Utilities.indent(depth+1)+ "\"$ref\": \"" + refvalue + "\"\n"
#        output += self.get_action_definition(typetable, actionentry, depth, prefixuri)
        output += UT.Utilities.indent(depth)   + "}"

        return output

    #########################################################################################################
    # Name: get_action_definition                                                                           #
    # Description:                                                                                          #
    #  Generates JSON for action definitions                                                                #
    #########################################################################################################
    def get_action_definition(self, typetable, actionentry, depth, namespace, prefixuri):

        output = self.writepatternproperties(typetable, actionentry, depth+1, namespace, prefixuri)
        output += UT.Utilities.indent(depth+1) +     "\"type\": \"object\",\n"
        output += UT.Utilities.indent(depth+1) +     "\"additionalProperties\": false,\n"
        output += UT.Utilities.indent(depth+1) +     "\"properties\": {\n"

        output += UT.Utilities.indent(depth+2) + "\"title\": {\n"
        output += UT.Utilities.indent(depth+3) +     "\"type\": \"string\",\n"
        output += UT.Utilities.indent(depth+3) +     "\"description\": \"Friendly action name\"\n"
        output += UT.Utilities.indent(depth+2) + "},\n"

        output += UT.Utilities.indent(depth+2) + "\"target\": {\n"
        output += UT.Utilities.indent(depth+3) +     "\"type\": \"string\",\n"
        output += UT.Utilities.indent(depth+3) +     "\"format\": \"uri\",\n"
        output += UT.Utilities.indent(depth+3) +     "\"description\": \"Link to invoke action\"\n"
        output += UT.Utilities.indent(depth+2) + "}"

##todo: url (and title?) should be required
## old code for writing out properties -- save for new parameter model
        if False:
            isfirstparam = True
            for param in actionentry["Node"]:
                if not param.tag == "{http://docs.oasis-open.org/odata/ns/edm}Parameter":
                    continue

                if isfirstparam:
                    isfirstparam = False
                    continue

                paramname = param.attrib["Name"]
                paramtype = "Collection(" + param.attrib["Type"] + ")"

                output += ",\n"
                output += UT.Utilities.indent(depth+2) + "\"" + paramname + "@Redfish.AllowableValues" + "\": {\n"
                output += self.generate_json_for_type(typetable, paramtype, depth + 3, actionentry["Namespace"], prefixuri, False, True)
                output += self.emit_annotations(typetable, actionentry["Namespace"],  param, depth + 3, prefixuri, False)
                output += "\n"
                output += UT.Utilities.indent(depth+2) + "}"

        output += "\n"
        output += UT.Utilities.indent(depth+1) +     "}"
        output += self.emit_annotations(typetable, actionentry["Namespace"],  actionentry["Node"], depth + 1, prefixuri, False)

        return output


    ################################################################################################################
    # Name: get_json_for_special_properties                                                                        #
    # Description:                                                                                                 #
    #  There are a bunch of properties that need special handling. Such properties are handled by this function.   #
    ################################################################################################################
    def get_json_for_special_properties(self, propertyname, depth, prefixuri):
        output = ""

        # If the prefix URI is not set, set it to a blank string 
        if (prefixuri is None):
            prefixuri = ""
        
        if propertyname == "@odata.context":
            output += UT.Utilities.indent(depth+1) + "\"@odata.context\": {\n"
            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/context\"\n"
            output += UT.Utilities.indent(depth+1) + "}"

        elif propertyname == "@odata.id":
            output += UT.Utilities.indent(depth+1) + "\"@odata.id\": {\n"
            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/id\"\n"
            output += UT.Utilities.indent(depth+1) + "}"
            
        elif propertyname == "@odata.type":
            output += UT.Utilities.indent(depth+1) + "\"@odata.type\": {\n"
            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/type\"\n"
            output += UT.Utilities.indent(depth+1) + "}"

        elif propertyname == "@odata.navigationLink":
            output += UT.Utilities.indent(depth+1) + "\"@odata.navigationLink\": {\n"
            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/id\"\n"
            output += UT.Utilities.indent(depth+1) + "}"

        return output

    ########################################################################################################
    # Name: generate_json_for_propertybag_actions                                                          #
    # Description:                                                                                         #
    #  Generated JSON corresponding to an action entry                                                     #
    ########################################################################################################
    def generate_json_for_propertybag_actions(self, typetable, typedata, depth, prefixuri, namespace, firstproperty):

        output = ''
        keys = sorted(typetable.keys())
        for typekey in keys:
            typeentry = typetable[typekey]

            if( not JsonSchemaGenerator.isboundtotype(typetable, typedata, typeentry ) ):
                continue

            # we have two entries for each action. we need to consider only one of this pair
            # we'll consider the one that starts with the namespace to be canonical
            if not typekey == typeentry["Namespace"] + "." + typeentry["Name"]:
                continue

            # we have a bound action; is it bound to this type?
            isboundtotype = False

            for param in typeentry["Node"].iter("{http://docs.oasis-open.org/odata/ns/edm}Parameter"):
                if not param.attrib["Type"] in typetable:
                    break

                if not typetable[param.attrib["Type"]] == typedata:
                    break

                isboundtotype = True
                break

            if isboundtotype:
                if(firstproperty):
                    firstproperty = False
                else:
                    output += ",\n"
                output += self.get_payload_actionentry(typetable, typeentry, depth + 1, prefixuri, namespace)
            
        return {"output":output, "firstproperty":firstproperty}

    ########################################################################################################
    # Name: isboundtotype                                                                                  #
    # Description:                                                                                         #
    #  Returns True if the specified action is bound to the specified type, otherwise returns False        #
    ########################################################################################################
    @staticmethod
    def isboundtotype(typetable, typedata, actionentry):

        if not ( actionentry["TypeType"] == "Action" ):
            return False

        if not ( "IsBound" in actionentry["Node"].attrib.keys() ):
            return False

        if ( actionentry["Node"].attrib["IsBound"] == "false" ):
            return False

        # we have a bound action; is it bound to this type?
        isboundtotype = False
		
        for param in actionentry["Node"].iter("{http://docs.oasis-open.org/odata/ns/edm}Parameter"):
            if not param.attrib["Type"] in typetable:
                break

            if not typetable[param.attrib["Type"]] == typedata:
                break

            isboundtotype = True
            break

        return isboundtotype

    ########################################################################################################
    # Name: writepatternproperties                                                                         #
    # Description:                                                                                         #
    #  Generates pattern properties for an object                                                          #
    ########################################################################################################
    def writepatternproperties(self, typetable, typedata, depth, namespace, prefixuri):

        output=""
        # allow odata and redfish annotations
        output += UT.Utilities.indent(depth) + "\"patternProperties\": {\n"
        output += UT.Utilities.indent(depth+1) + "\"^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message|Privileges)\\\\.[a-zA-Z_][a-zA-Z0-9_.]+$\": {\n"
        output += UT.Utilities.indent(depth+2) + "\"type\": [\n"
        output += UT.Utilities.indent(depth+3) + "\"array\",\n"
        output += UT.Utilities.indent(depth+3) + "\"boolean\",\n"
        output += UT.Utilities.indent(depth+3) + "\"number\",\n"
        output += UT.Utilities.indent(depth+3) + "\"null\",\n"
        output += UT.Utilities.indent(depth+3) + "\"object\",\n"
        output += UT.Utilities.indent(depth+3) + "\"string\"\n"
        output += UT.Utilities.indent(depth+2) + "],\n"
        output += UT.Utilities.indent(depth+2) + "\"description\": \"This property shall specify a valid odata or Redfish property.\"\n"
        output += UT.Utilities.indent(depth+1) + "}"
        output += self.emit_property_patterns(typetable, namespace, typedata["Node"], depth, prefixuri)
        output += "\n"
        output += UT.Utilities.indent(depth)   + "},\n"
		
        return output

    ########################################################################################################
    # Name: write_type                                                                                     #
    # Description:                                                                                         #
    #  writes type attribute                                                                               #
    ########################################################################################################
    def write_type(self, typename, depth, isnullable):

        output  = UT.Utilities.indent(depth)   + "\"type\": "
        if isnullable:
            output += "[\n"
            output += UT.Utilities.indent(depth+1) +     "\"" + typename + "\",\n"
            output += UT.Utilities.indent(depth+1) +     "\"null\"\n"
            output += UT.Utilities.indent(depth)   + "]"
        else:
            output += "\"" + typename +"\""

        return output

    ########################################################################################################
    # Name: write_reference                                                                                #
    # Description:                                                                                         #
    #  Generates JSON for a property reference that may be nullable                                        #
    ########################################################################################################
    def write_reference(self, refvalue, depth, isnullable, allowreference):

        output = UT.Utilities.indent(depth) 
        if isnullable or allowreference:
            output += "\"anyOf\": [\n"
            if allowreference:
                output += UT.Utilities.indent(depth+1) + "{\"$ref\": \"" + odataSchema + "#/definitions/idRef\"},\n"
            output += UT.Utilities.indent(depth+1) + "{\"$ref\": \"" + refvalue + "\"}"
            if isnullable:
                output += ",\n" + UT.Utilities.indent(depth+1) + "{\"type\": \"null\"}"
            output += "\n" + UT.Utilities.indent(depth)   + "]"
        else:
            output += "\"$ref\": \"" + refvalue + "\""

        return output

    ########################################################################################################
    # Name: get_latest_version                                                                             #
    # Description:                                                                                         #
    #  Gets the latest version less than or equal to current namespace for a particular type               #
    ########################################################################################################
    def get_latest_version(self, typetable, typedata, current_namespace):

        #if type is in current namespace, return it
        if typedata["Namespace"] == current_namespace :
            return typedata

        typename=typedata["Name"]
        for key in typetable.keys():
            candidate_type=typetable[key]
            candidate_namespace=candidate_type["Namespace"]
            #if namespace is a more recent namespace of the current type that is less than the current namespace
            if(candidate_type["Name"] == typename and (candidate_namespace == current_namespace or ( not ( self.is_prior_version(candidate_namespace,typedata["Namespace"]) ) and self.is_prior_version(candidate_namespace,current_namespace) ) ) ):
                typedata=candidate_type

        return typedata                

    ########################################################################################################
    # Name: generate_json_for_propertybag                                                                  #
    # Description:                                                                                         #
    #  Generates JSON for all the properties that are defined inside a type                                #
    ########################################################################################################
    def generate_json_for_propertybag(self, typetable, typedata, depth, namespace, prefixuri, isnullable, write_as_reference):

        #find out if there is a later version of this type defined within this namespace
        typedata = self.get_latest_version(typetable,typedata,namespace)

        output = self.write_type("object", depth, isnullable) + ",\n"

        # allow odata and redfish annotations
        output += self.writepatternproperties(typetable, typedata, depth, namespace, prefixuri)
		
        nodes = [typedata["Node"]]
        currenttype = typedata

        while "BaseType" in currenttype["Node"].attrib.keys():
            basetypename = currenttype["Node"].attrib["BaseType"]
            if basetypename in typetable:
                currenttype = typetable[basetypename]
                nodes.append(currenttype["Node"])

            else:
                break

        # Write out Additional Properties
        if ( self.allows_additional_properties(typedata, typetable) ):
            output += UT.Utilities.indent(depth) + "\"additionalProperties\": true,\n"
        else:
            output += UT.Utilities.indent(depth) + "\"additionalProperties\": false,\n"

        output += UT.Utilities.indent(depth)  + "\"properties\": {"
        requiredproperties = []
        requiredcreateproperties = []
        firstproperty = True

        # Generate special properties for EntityType
        if typedata["TypeType"] == "EntityType" and not self.has_basetype(typetable, typedata, "Resource.v1_0_0.ReferenceableMember"):
            output += "\n"
            output += self.get_json_for_special_properties("@odata.context", depth, prefixuri)
            output += ",\n"
            output += self.get_json_for_special_properties("@odata.id", depth, prefixuri)
            output += ",\n"
            output += self.get_json_for_special_properties("@odata.type", depth, prefixuri)
            firstproperty = False

        bindingparameter = True

        # Loop through the nodes in the parsed XML
        for propbag in reversed(nodes):
            propkinds = ["Property", "NavigationProperty", "Parameter"]
            for propkind in propkinds:
                for property in propbag.iter("{http://docs.oasis-open.org/odata/ns/edm}" + propkind):
                    if firstproperty:
                        output += "\n"
                        firstproperty = False
                    else:
                        output += ",\n"

                    if typedata["TypeType"] == "Action" and bindingparameter:
                        bindingparameter = False
                        firstproperty = True
                        continue

                    # Extract Name and Type
                    propname = property.attrib["Name"]
                    proptypename = property.attrib["Type"]

                    #determine nullability
                    propertyisnullable = True
                    if "Nullable" in property.attrib.keys():
                        if property.attrib["Nullable"] == "false":
                            propertyisnullable = False

                    # Handle navigationLinks/NavigationProperty
                    if ( propkind == "NavigationProperty"):

                        # write out common properties for collections
                        if ( not (proptypename is None)) and (self.is_collection(proptypename)):
                            output += UT.Utilities.indent(depth+1) + "\"" + propname + "@odata.count\": {\n"
                            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/count\"\n"
                            output += UT.Utilities.indent(depth+1) + "},\n"

                            output += UT.Utilities.indent(depth+1) + "\"" + propname + "@odata.navigationLink\": {\n"
                            output += UT.Utilities.indent(depth+2) + "\"type\": \"string\",\n"
                            output += UT.Utilities.indent(depth+2) + "\"format\": \"uri\"\n"
                            output += UT.Utilities.indent(depth+1) + "},\n"

                        output += UT.Utilities.indent(depth+1) + "\"" + propname + "\": {\n"

                        # Figure out if OData.AutoExpandReferences is set or "OData.AutoExpand"
                        termvalue = ""
                        for annotation in property.iter("{http://docs.oasis-open.org/odata/ns/edm}Annotation"):
                            if annotation.attrib["Term"] == "OData.AutoExpandReferences":
                                termvalue = "OData.AutoExpandReferences"
                            elif annotation.attrib["Term"] == "OData.AutoExpand":
                                termvalue = "OData.AutoExpand"
                          
                        # Check if it is a collection or not
                        if ( not (proptypename is None)) and (self.is_collection(proptypename)):
                            output += UT.Utilities.indent(depth+2) + "\"type\": \"array\",\n"
                            output += UT.Utilities.indent(depth+2) + "\"items\": {\n"

                            # Get the reference value
                            current_typename = JsonSchemaGenerator.extract_underlyingtype_from_collectiontype(proptypename)
                            refvalue = self.get_ref_value_for_type(typetable, current_typename, namespace)
                            output += self.write_reference(refvalue, depth+3, False, False)+"\n"
                            output += UT.Utilities.indent(depth+2) + "}"
                        else:
                            refvalue = self.get_ref_value_for_type(typetable, proptypename, namespace)
                            output += self.write_reference(refvalue, depth+2, propertyisnullable, False)

					# Handle regular property
                    else:
                        output += UT.Utilities.indent(depth+1) + "\"" + propname + "\": {\n"    

                        # Check if it is a collection or not
                        iscollection = self.is_collection(proptypename)
                        if ( iscollection ):
                            output += UT.Utilities.indent(depth+2) + "\"type\": \"array\",\n"
                            output += UT.Utilities.indent(depth+2) + "\"items\": {\n"
                            proptypename = JsonSchemaGenerator.extract_underlyingtype_from_collectiontype(proptypename)
                            depth += 1

                        # Get all keys and extract typedata for the property
                        ignoreannotations = self.get_property_annotation_terms(property)
                        typetablekeys = typetable.keys()
                        if (proptypename in typetablekeys):
                            if(self.is_inline_type(typetable[proptypename], typetable) ):
                                refvalue = self.get_ref_value_for_type(typetable, proptypename, namespace)
                                output += self.write_reference(refvalue, depth+2, propertyisnullable, False)
                            # write Links, Actions, OemActions inline
                            else:
                                output += self.generate_json_for_type(typetable, proptypename, depth + 2, typedata["Namespace"], prefixuri, propertyisnullable, False, ignoreannotations)

                        # type not in loaded; probably primitive type
                        else:
                            output += self.generate_json_for_type(typetable, proptypename, depth + 2, typedata["Namespace"], prefixuri, propertyisnullable, False, ignoreannotations)

                        output += self.emit_annotations(typetable, typedata["Namespace"], property, depth + 2, prefixuri, False, [], True)

                        if ( iscollection ):
                            output += "\n" + UT.Utilities.indent(depth+1) + "}"
                            depth -= 1

                    if self.is_required_property(property):
                        requiredproperties.append(propname)

                    if self.is_requiredOnCreate_property(property):
                        requiredcreateproperties.append(propname)

                    output += self.emit_annotations(typetable, typedata["Namespace"], property, depth + 2, prefixuri, False)
                    output += "\n"
                    output += UT.Utilities.indent(depth+1) + "}"

        # Handles actions
        result = self.generate_json_for_propertybag_actions(typetable, typedata, depth, prefixuri, namespace, firstproperty)
        output += result["output"]
        firstproperty = result["firstproperty"]

        # Close property block
        if not(firstproperty):
            output += "\n"
            output += UT.Utilities.indent(depth)
        output += "}"

        # Write Required Properties
        if len(requiredproperties) > 0:
            output += ",\n"
            output += UT.Utilities.indent(depth)  + "\"required\": [\n"
            firstrequiredproperty = True

            for propname in requiredproperties:
                if firstrequiredproperty:
                    firstrequiredproperty = False

                else:
                    output += ",\n"

                output += UT.Utilities.indent(depth+1) + "\"" + propname + "\""

            output += "\n"
            output += UT.Utilities.indent(depth)  + "]"
 
        # Write Required On Create Properties
        if len(requiredcreateproperties) > 0:
            output += ",\n"
            output += UT.Utilities.indent(depth)  + "\"requiredOnCreate\": [\n"
            firstproperty = True

            for propname in requiredcreateproperties:
                if firstproperty:
                    firstproperty = False

                else:
                    output += ",\n"

                output += UT.Utilities.indent(depth+1) + "\"" + propname + "\""

            output += "\n"
            output += UT.Utilities.indent(depth)  + "]"

        return output


    ############################################################################################
    # Name: generate_json_for_collection_type                                                  #
    # Description:                                                                             #
    #   Generates JSON corresponding to a collection type                                      #
    ############################################################################################
    def generate_json_for_collection_type(self, typetable, typename, depth, namespace, prefixuri, isnullable, write_as_reference):
        output = ""
        scalarname = typename[11:-1]
        output  = UT.Utilities.indent(depth) + "\"type\": \"array\",\n"
        output += UT.Utilities.indent(depth) + "\"items\": {\n"
        output += self.generate_json_for_type(typetable, scalarname, depth + 1, namespace, prefixuri, isnullable, write_as_reference)
        output += "\n"
        output += UT.Utilities.indent(depth) + "}"

        return output

    ############################################################################################
    # Name: generate_json_for_primitive_types                                                  #
    # Description:                                                                             #
    #   Generates JSON corresponding to primitive types                                        #
    ############################################################################################
    def generate_json_for_primitive_types(self, typename, isnullable, depth):
        output = ""
        edmtojson = {
            "Edm.String": "string",
            "Edm.Int16": "number",
            "Edm.Int32": "number",
            "Edm.Int64": "number",
            "Edm.Boolean": "boolean",
            "Edm.Decimal": "number",
            "Edm.DateTimeOffset": "string",
            "Edm.Guid": "string",
        }

        if typename in edmtojson.keys():
            jsontype = edmtojson[typename]

            output = self.write_type(jsontype, depth, isnullable)

            if typename == "Edm.DateTimeOffset":
                output += ",\n" + UT.Utilities.indent(depth) + "\"format\": \"date-time\""

            if typename == "Edm.Guid":
                output += ",\n" + UT.Utilities.indent(depth) + "\"pattern\": \"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\""

        elif typename == "Edm.PrimitiveType":
            output += self.write_primitive_type(depth, isnullable)

        else:
               print("Primitive Type Not Found!: " + typename)

        return output

    ############################################################################################
    # Name: write_primitive_type                                                               #
    # Description:                                                                             #
    #   Generates JSON corresponding to Edm.PrimitiveType                                      #
    ############################################################################################
    def write_primitive_type(self, depth, isnullable):

        output = ""
        output  = UT.Utilities.indent(depth)   + "\"type\": [\n"
        output += UT.Utilities.indent(depth+1) +     "\"string\",\n"
        output += UT.Utilities.indent(depth+1) +     "\"boolean\",\n"
        output += UT.Utilities.indent(depth+1) +     "\"number\""
        if isnullable: 
            output += ",\n"
            output += UT.Utilities.indent(depth+1) +  "\"null\""
        output += "\n"
        output += UT.Utilities.indent(depth)   + "]"

        return output
    
    ############################################################################################
    # Name: is_prior_version                                                                   #
    # Description:                                                                             #
    #   Returns true if the first namespace is a previous version of the second namespace      #
    ############################################################################################
    def is_prior_version(self, namespace1, namespace2):

        #todo: deal with malformed versions
        major1 = namespace1.find(".")
        major2 = namespace2.find(".")

        # The type is from the unversioned namespace
        if(major1 < 0 or major2 < 0):
            return False

        minor1 = namespace1.find("_", major1+2)
        minor2 = namespace2.find("_", major2+2)

        # The type is from a different major version
        if(namespace1[:minor1] != namespace2[:minor2] ):
            return False

        errata1 = namespace1.find("_",minor1+1)
        errata2 = namespace2.find("_",minor2+1)

        minorversion1 = namespace1[minor1+1:errata1]
        errataversion1 = namespace1[errata1+1:]
        minorversion2 = namespace2[minor2+1:errata2]
        errataversion2 = namespace2[errata2+1:]

        # The type is from a previous version of the namespace
        if(minorversion1 < minorversion2 or (minorversion1 == minorversion2 and errataversion1 < errataversion2 ) ):
            return True

        return False

    ############################################################################################
    # Name: include_type                                                                       #
    # Description:                                                                             #
    #   Returns true if this is the latest minor version of the type less than or equal to     #
    #   the version of the namespace being written                                             #
    ############################################################################################
    def include_type(self, typename, type_namespace, current_namespace, typetable):

        # Namespace is the same as this, so include it
        if(type_namespace == current_namespace):
            return True

        # Namespace is not a previous version of this namespace, so exclude it
        if( not(self.is_prior_version(type_namespace, current_namespace)) ):
            return False

        # Type is defined in current namespace so exclude it
        if( current_namespace+"."+typename in typetable.keys() ):
            return False

        # If there are any newer versions of the type prior to current namespace version, exclude it 
        for key in typetable.keys():
            type=typetable[key]
            if(type["Name"] == typename and self.is_prior_version(type["Namespace"],current_namespace) ):
                if( self.is_prior_version(type_namespace,type["Namespace"]) ):
                    return False

        return True

    ############################################################################################
    # Name: get_current_namespace                                                              #
    # Description:                                                                             #
    #   Returns the namespace of the latest version of a type less than or equal to            #
	#   the current namespace                                                                  #
    ############################################################################################
    def get_current_namespace(self, typename, type_namespace, current_namespace, typetable):

        # If namespace is the same as current namespace, return it
        if(type_namespace == current_namespace):
            return current_namespace

        #if this is not a type we've read, just return its namespace
        if not (type_namespace + "." + typename in typetable.keys()):
            return type_namespace

        # If type namespace is greater than the current namespace, return it (this should never happen)
        if(self.is_prior_version(current_namespace, type_namespace)):
            return type_namespace

        # If type is defined in current namespace return current namespace
        if( current_namespace + "." + typename in typetable.keys() ):
            return current_namespace

        # Return latest version of the type less than or equal to the current namespace version
        for candidate_key in typetable.keys():
            type=typetable[candidate_key]
            if(type["Name"] == typename and self.is_prior_version(type["Namespace"],current_namespace) ):
                if( self.is_prior_version(type_namespace,type["Namespace"]) ):
                     type_namespace=type["Namespace"]

        return type_namespace

    ############################################################################################
    # Name: generate_enum_type                                                                 #
    # Description:                                                                             #
    #   Generates JSON corresponding to an enum                                                #
    ############################################################################################
    def generate_enum_type(self, typetable, typedata, typename, namespace, depth, isnullable, members):

        output = ""

        #if same major version, reference local definitions
        if not(self.include_type(typename, typedata["Namespace"], namespace, typetable) ):
                refvalue = self.get_ref_value_for_type(typetable, typename, namespace)
                output += self.write_reference(refvalue, depth, isnullable, False)

        else:
            output = self.write_type("string", depth, isnullable) + ",\n"

            output += UT.Utilities.indent(depth) + "\"enum\": [\n"
            firstenumvalue = True
            founddescriptions=False
            foundlongdescriptions=False

            for member in members:
                if firstenumvalue:
                    firstenumvalue = False

                else:
                    output += ",\n"

                output += UT.Utilities.indent(depth+1) + "\"" + member["Name"] + "\""

                if member["Description"] != "":
                   founddescriptions = True

                if member["LongDescription"] != "":
                   foundlongdescriptions = True

            output += "\n"
            output += UT.Utilities.indent(depth) + "]"

            if founddescriptions:
                output += ",\n"
                output += UT.Utilities.indent(depth) + "\"enumDescriptions\": {\n"
                firstenumvalue = True

                for member in members:
                    if member["Description"] != "":
                        if firstenumvalue:
                            firstenumvalue = False

                        else:
                            output += ",\n"

                        output += UT.Utilities.indent(depth+1) + "\"" + member["Name"] + "\": \"" + member["Description"] + "\""
            
                output += "\n"
                output += UT.Utilities.indent(depth)  + "}"

            if foundlongdescriptions:
                output += ",\n"
                output += UT.Utilities.indent(depth) + "\"enumLongDescriptions\": {\n"
                firstenumvalue = True

                for member in members:
                    if member["LongDescription"] != "":
                        if firstenumvalue:
                            firstenumvalue = False

                        else:
                            output += ",\n"

                        output += UT.Utilities.indent(depth+1) + "\"" + member["Name"] + "\": \"" + member["LongDescription"] + "\""
            
                output += "\n"
                output += UT.Utilities.indent(depth)  + "}"

        return output

    ############################################################################################
    # Name: generate_json_for_EnumTypes                                                        #
    # Description:                                                                             #
    #   Generates JSON corresponding to a Enum type                                            #
    ############################################################################################
    def generate_json_for_EnumTypes(self, typetable, typedata, typename, namespace, depth, isnullable):

        members = []

        for member in typedata["Node"].iter("{http://docs.oasis-open.org/odata/ns/edm}Member"):
            description = ""
            longdescription = ""
            for annotation in member.iter("{http://docs.oasis-open.org/odata/ns/edm}Annotation"):
                if annotation.attrib["Term"] == "OData.Description":
                   description = annotation.attrib["String"]
                elif annotation.attrib["Term"] == "OData.LongDescription":
                   longdescription = annotation.attrib["String"]

            members.append({"Name":member.attrib["Name"], "Description":description, "LongDescription":longdescription})

        return self.generate_enum_type(typetable, typedata, typename, namespace, depth, isnullable, members)

    ############################################################################################
    # Name: generate_json_for_RefishEnum                                                       #
    # Description:                                                                             #
    #   Generates JSON corresponding to a Redfish enum type                                    #
    ############################################################################################
    def generate_json_for_RedfishEnum(self, typetable, typedata, typename, namespace, depth, isnullable):

        members = []

        for annotation in typedata["Node"].iter("{http://docs.oasis-open.org/odata/ns/edm}Annotation"):
            if annotation.attrib["Term"] == "Redfish.Enumeration":
                for element in annotation:
                    if element.tag == "{http://docs.oasis-open.org/odata/ns/edm}Collection":
                        for record in element.iter("{http://docs.oasis-open.org/odata/ns/edm}Record"):
                            description = ""
                            longdescription = ""
                            for propertyvalue in record.iter("{http://docs.oasis-open.org/odata/ns/edm}PropertyValue"):
                                if propertyvalue.attrib["Property"] == "Member":
                                    member = propertyvalue.attrib["String"]
                                    break

                            for annotation in record.iter("{http://docs.oasis-open.org/odata/ns/edm}Annotation"):
                                if annotation.attrib["Term"] == "OData.Description":
                                    description = annotation.attrib["String"]
                                elif annotation.attrib["Term"] == "OData.LongDescription":
                                    longdescription = annotation.attrib["String"]

                            members.append({"Name":member,"Description":description,"LongDescription":longdescription})
                    break
            break

        return self.generate_enum_type(typetable, typedata, typename, namespace, depth, isnullable, members)

    ##############################################################################
    # Name: generate_json_for_type                                               #
    # Description:                                                               #
    #  Generates JSON for a particular type                                      #
    ##############################################################################
    def generate_json_for_type(self, typetable, typename, depth, namespace, prefixuri, isnullable, write_as_reference, ignoreannotations = []):

        output = ""

        # Collections
        if self.is_collection(typename):
            output = self.generate_json_for_collection_type(typetable, typename, depth, namespace, prefixuri, isnullable, write_as_reference)
            return output

        # "Primitive" types
        if typename.startswith("Edm."):
            output = self.generate_json_for_primitive_types(typename, isnullable, depth)
            return output

        # Throw error if the type is not found
        if not typename in typetable.keys():
            print("Error: " + typename + " not found.")
            return UT.Utilities.indent(depth)  + "\"ERROR\": \"type " + typename + " unrecognized.\""

        typedata = typetable[typename]
        typetype = typedata["TypeType"]

        if typetype == "EnumType":
            output += self.generate_json_for_EnumTypes(typetable, typedata, typename, namespace, depth, isnullable)

        elif typetype == "EntityType":
            if self.include_type(typename, typedata["Namespace"], namespace, typetable) and not write_as_reference:
                ##include the id for collection resources (resources already include them in the unversioned namespace)
                if self.has_basetype(typetable, typedata, "Resource.v1_0_0.ResourceCollection"):
                    output += UT.Utilities.indent(depth) + "\"anyOf\": [\n"
                    output += UT.Utilities.indent(depth+1) + "{\n"
                    output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/idRef\"\n"
                    output += UT.Utilities.indent(depth+1) + "},\n"
                    output += UT.Utilities.indent(depth+1) + "{\n"
                    output += self.generate_json_for_propertybag(typetable, typedata, depth+2, namespace, prefixuri, isnullable, write_as_reference) +"\n"
                    output += UT.Utilities.indent(depth+1) + "}\n"
                    output += UT.Utilities.indent(depth) + "]"
                else:
                    output += self.generate_json_for_propertybag(typetable, typedata, depth, namespace, prefixuri, isnullable, write_as_reference)
            else:
                #this code never appears to get called
                output = UT.Utilities.indent(depth) + "\"@odata.id\": \"" + typedata["JsonUrl"] + "#" + typename + "\""
                return output

        elif typetype == "ComplexType":
            if self.include_type(typename, typedata["Namespace"], namespace, typetable) and not write_as_reference:
                output = self.generate_json_for_propertybag(typetable, typedata, depth, namespace, prefixuri, isnullable, write_as_reference)
            else:
                refvalue = self.get_ref_value_for_type(typetable, typename, namespace)
                output += self.write_reference(refvalue, depth, isnullable, False)
                
                return output

        elif typetype == "Action":
            if self.include_type(typename, typedata["Namespace"], namespace, typetable) and not write_as_reference:
                output = self.generate_json_for_propertybag(typetable, typedata, depth, namespace, prefixuri, isnullable, write_as_reference)
            else:
                simplename = typename[typename.rfind(".") + 1 :]
                output = UT.Utilities.indent(depth) + "\"@odata.id\": \"" + typedata["JsonUrl"] + "#" + simplename + "\""
                return output

        elif typetype == "TypeDefinition":
            underlyingtype = typedata["Node"].attrib["UnderlyingType"]

            if underlyingtype == "Edm.String" and self.is_redfish_enum(typedata["Node"]):
                output += self.generate_json_for_RedfishEnum(typetable, typedata, typename, namespace, depth, isnullable)
 
            else:
                output = self.generate_json_for_type(typetable, underlyingtype, depth, namespace, prefixuri, isnullable, False)
                output += self.emit_annotations(typetable, namespace, typedata["Node"], depth, prefixuri, isnullable, ignoreannotations, True)

        else:
            return UT.Utilities.indent(depth) + "ERROR: unknown TypeType " + typetype

        # Emit type annotations
        output += self.emit_annotations(typetable, namespace, typedata["Node"], depth, prefixuri, isnullable, ignoreannotations)

        return output

    ################################################################################
    # Name: generate_json_for_reference_type                                       #
    # Description:                                                                 #
    #  generates a json payload for an unversioned reference to the specified type #
    ################################################################################
    def generate_json_for_reference_type(self, typetable, typename, schemaname, depth, prefixuri, includeIdRef):

        output = ""
        derivedtypes = self.get_derived_types(typetable, typename, schemaname)
        write_as_array = len(derivedtypes) > 1 or includeIdRef
        if(write_as_array):
            output += UT.Utilities.indent(depth+1) + "\"anyOf\": [\n"
            depth+=1
            if(includeIdRef):
                output += UT.Utilities.indent(depth+1) + "{\n"
                output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + odataSchema + "#/definitions/idRef\"\n"
                output += UT.Utilities.indent(depth+1) + "}"

        #for each type that derives from this type
        isFirst= not(includeIdRef)
        for derivedtype in derivedtypes:
            if(not(isFirst)):
                output += ",\n"
            else:
                isFirst=False
            if(write_as_array):
                output += UT.Utilities.indent(depth+1) + "{\n"
            output += UT.Utilities.indent(depth+2) + "\"$ref\": \"" + prefixuri + derivedtype["Namespace"] + ".json#/definitions/" + derivedtype["Name"] + "\""
            if(write_as_array):
                output += "\n"
                output += UT.Utilities.indent(depth+1) + "}"

        if(write_as_array):
            output += "\n"
            output += UT.Utilities.indent(depth) + "]"
  
        return output

    ################################################################################
    # Name: get_derived_types                                                      #
    # Description:                                                                 #
    #  Generates a list of all types derived from current type                     #
    ################################################################################
    def get_derived_types(self, typetable, basetypename, basetypenamespace):

        basetypename = basetypenamespace + "." + basetypename
        typenames = sorted(typetable.keys())
        visitedtypes=[]
        derivedtypes = []

        for currentType in typenames:
            typedata = typetable[currentType]
            typetype = typedata["TypeType"]
            typename = typedata["Name"]
            typenamespace = typedata["Namespace"]
        
            if(not ((typename + ":" + typenamespace) in visitedtypes )) :
                # This type has not been parsed yet
                visitedtypes.append(typename + ":" + typenamespace)
                if ( typetype == "EntityType" or typetype == "ComplexType"):
                    # Check if the type being processed is derived from Resource or ResourceCollection
                    if ( self.has_basetype(typetable, typedata, basetypename) ): 
                        derivedtypes.append(typedata)

        return derivedtypes

    ################################################################################
    # Name: generate_typetable                                                     #
    # Description:                                                                 #
    #  Populates the collection that contains information related to               #
    #  all the data types relevent to generation of JSON                           #
    ################################################################################
    @staticmethod
    def generate_typetable(url, directory, is_from_refuri):

        JsonSchemaGenerator.parsed.append(url)
        data = UT.Utilities.open_url(url, directory)
    
        if len(data) == 0:
            return {}

        root = ET.fromstring(data)
        typetable = {}
        namespaces = []

        refuri = ""

        for reference in root.iter("{http://docs.oasis-open.org/odata/ns/edmx}Reference"):
            refuri = reference.attrib["Uri"]

            #todo: only load types from referenced namespaces			      
            if not refuri in JsonSchemaGenerator.parsed:
                typetable = dict(list(typetable.items()) + list(JsonSchemaGenerator.generate_typetable(refuri, directory, True)["Typetable"].items()))
    
        for dataservices in root.iter("{http://docs.oasis-open.org/odata/ns/edmx}DataServices"):
            current_file_typetable = {}
            namespace = ""
            alias = ""
            for schema in dataservices.iter("{http://docs.oasis-open.org/odata/ns/edm}Schema"):
                namespace = schema.attrib["Namespace"]
                if(is_from_refuri == False):
                   namespaces.append(namespace)

                alias = namespace
                if "Alias" in schema.attrib.keys():
                    alias = schema.attrib["Alias"]

                jsonurl = schemaBaseLocation + alias + ".json"
 
                typekinds = ["EntityType", "ComplexType", "TypeDefinition", "EnumType", "Action"]

                for typekind in typekinds:
                    for typedata in schema.iter("{http://docs.oasis-open.org/odata/ns/edm}" + typekind):

                        # Populate data related to the type
                        typename = typedata.attrib["Name"]
                        typeentry = {}
                        typeentry["TypeType"] = typekind
                        typeentry["JsonUrl"] = jsonurl 
                        typeentry["Namespace"] = namespace
                        typeentry["Alias"] = alias
                        typeentry["Name"] = typename
                        typeentry["Node"] = typedata

                        # Set base type
                        if "BaseType" in typedata.attrib:
                            typeentry["BaseType"] = typedata.attrib["BaseType"]
                        else:
                            typeentry["BaseType"] = ""

                        typeentry["RefUri"] = refuri
                        typeentry["IsFromRefUri"] = is_from_refuri

                        # Put it in a temporary dictionary so that we only process a small number of types if any extra processing is required.
                        current_file_typetable[namespace + "." + typename] = typeentry
                        current_file_typetable[alias + "." + typename] = typeentry
            
            typetable.update(current_file_typetable)
			
        #set bound namespace for actions
        typekeys = typetable.keys()
        for key in typekeys:
            boundtype={}
            action=typetable[key]
            if(action["TypeType"]=="Action"):
                action["BoundNamespace"] = action["Namespace"]
                for bindingkey in typekeys:
                    bindingtype = typetable[bindingkey]
                    if( JsonSchemaGenerator.isboundtotype(typetable,bindingtype,action) ):
                        action["BoundNamespace"] = bindingtype["Namespace"]
                        break

        typeinfo = {}
        typeinfo["Namespaces"] = namespaces
        typeinfo["Typetable"] = typetable
        return typeinfo

    ################################################################################################################
    # Name: generate_definition_block                                                                              #
    # Description:                                                                                                 #
    #  Generates the definitions block and adds all the complexTypes and types that derive from ReferenceableMember #
    #  into it.                                                                                                    #
    ################################################################################################################
    def generate_definition_block(self, typetable, depth, isnullable, namespace, prefixuri):

        typenames = sorted(typetable.keys())
        parsedtypes = []
        type_count = 0
        output = ""

        # Loop though all the types defined and generate them one by one.
        for currentType in typenames:
            typedata = typetable[currentType]
            typetype = typedata["TypeType"]
            currentNamespace = typedata["Namespace"]
            basetype = typedata["BaseType"]
            typename = typedata["Name"]
        
            if(not ((typename + ":" + currentNamespace) in parsedtypes)) :
                # This type has not been parsed yet. Process it now.
                #if this is an inline type to include, that's not an abstract complex type in the Resource namespace
                if ( (typetype!= "Action" and ( self.include_type(typename,currentNamespace, namespace, typetable) and self.is_inline_type(typedata, typetable) and not (typetype=="ComplexType" and self.isabstract(typedata) and currentNamespace == "Resource" ) ) )
                    or (typetype == "Action" and self.include_type(typename, typedata["BoundNamespace"], namespace, typetable)) ):
                    # Add comma if this is not the first definition, otherwise write start of definitions block
                    if (type_count > 0):
                        output += ",\n"
                    else:
                        output += UT.Utilities.indent(depth) + "\"definitions\": {\n"

                    # Start type definition
                    output += UT.Utilities.indent(depth+1) + "\"" + typename + "\": {\n"
                    # Add it to the list so that it does not get generated again.
                    parsedtypes.append(typename + ":" + currentNamespace)

                    # Generate JSON for the type and append it to the output
                    if (typetype == "Action"):
                        output += self.get_action_definition(typetable, typedata, depth + 1, namespace, prefixuri)

                    # todo: support other versions (derived) of Resource and ReferenceableMember
                    elif ( basetype == "Resource.v1_0_0.Resource" ):
                        output += self.generate_json_for_reference_type(typetable, typename, namespace, depth + 1, prefixuri, True)
                    elif ( self.isabstract(typedata) ):
                        output += self.generate_json_for_reference_type(typetable, typename, namespace, depth + 1, prefixuri, False)
                    else:
                        output += self.generate_json_for_type(typetable, currentType, depth+2, namespace, prefixuri, False, False)

                    output += "\n" + UT.Utilities.indent(depth + 1) + "}"
                    type_count += 1
                
        # Close the definitions block
        if (type_count > 0):
            output += "\n" + UT.Utilities.indent(depth) + "}"

        return output

    ##############################################################################
    # Name: generate_json_for_file                                               #
    # Description:                                                               #
    #  Convert all types in given file                                           #
    ##############################################################################
    def generate_json_for_file(self, typetable, depth, isnullable, filename, namespace, prefixuri, ignoreannotations = []):

        output = ""

        # If there are any types that derive from Resource.v1_0_0.Resource, reference them
        typenames = sorted(typetable.keys())
        parsedtypes = []
        validationtypes = []
        validationtypecount = 0

        # Loop through all the types defined in the file and generate output
        for currentType in typenames:
            typedata = typetable[currentType]
            typetype = typedata["TypeType"]
            typename = typedata["Name"]
            typenamespace = typedata["Namespace"]
        
            if(not ((typename + ":" + typenamespace) in parsedtypes)) :
                # This type has not been parsed 
                parsedtypes.append(typename + ":" + typenamespace)
                if ( (typenamespace == namespace) and (typedata["IsFromRefUri"] == False) and (typetype == "EntityType" and (self.has_basetype(typetable, typedata, "Resource.v1_0_0.Resource" ) or self.has_basetype(typetable, typedata, "Resource.v1_0_0.ResourceCollection") ) ) ): 
                    validationtypecount += 1
                    validationtypes.append(self.get_ref_value_for_type(typetable, currentType, namespace))

        title=namespace
        if(validationtypecount == 1):
            title = title + "." + validationtypes[0][validationtypes[0].rfind("/")+1:]

        output += UT.Utilities.indent(depth) + "\"title\": \"#" + title + "\",\n"

        if(validationtypecount > 1):
           output += UT.Utilities.indent(depth) + "\"anyOf\": [\n"
           first = True
           for validationtype in validationtypes:
               if (first == True):
                   first=False
               else:
                   output += ",\n"
               output += UT.Utilities.indent(depth + 1) + "{ \"$ref\": \"" + validationtype + "\" }"
           output += "\n"
           output += UT.Utilities.indent(depth) + "],\n"

#todo: clean up conditional logic
        elif validationtypecount == 1:
           output += UT.Utilities.indent(depth) + "\"$ref\": \"" + validationtypes[0] + "\",\n"

		#now generate definition block
        output += self.generate_definition_block(typetable, depth, isnullable, namespace, prefixuri)

        return output

    ##########################################################################################################
    # Name: generate_json_files                                                                               #
    # Description:                                                                                           #
    #  Consumes the results that were returned as final output and generates the corresponsing JSON files.   #
    ##########################################################################################################
    @staticmethod
    def generate_json_files(name, results, args):
        screenoutput = ''
        depth = 0

        # Loop through all the results and 
        screenoutput += "\nContent-type: application/json\n"
        # return the JSON result
        fileoutput  = ''
        # Insert the starting bracket
        fileoutput += UT.Utilities.indent(depth) + "{\n"
        # Add the Schema tag
        fileoutput += UT.Utilities.indent(depth+1) + "\"$schema\": \"" + redfishSchema + "\",\n"
        # Fill in the result
        fileoutput += results
        # Add Copyright
        fileoutput += ",\n"
        fileoutput += UT.Utilities.indent(depth+1) + "\"copyright\": \"" + args.copyright + "\"\n"
        # End starting bracket
        fileoutput += UT.Utilities.indent(depth) + "}\n"
        screenoutput += fileoutput
        filename = name + ".json"

#fix this for web use
        filename=args.outdir + "\\" + filename
        file = open(filename, "wb")
        file.write(bytes(fileoutput, 'utf-8'))
        file.close()
            
        return screenoutput

    ###################################################################################################
    # Name: parse_url                                                                                 #
    # Description:                                                                                    #
    #  Parses the input URL and extracts the filename, namespace and classname from the URL           #
    #  Also reports an error if the URL is not formed correctly.                                      #
    ###################################################################################################
    @staticmethod
    #fix this - get the namespace and alias from the file
    def parse_url(url):
        result = {}
        namespaceStart = -1
        incorrect_url = False
    
        # Look for first # in the URL
        filename_end = url.rfind("#")

        # If there is a # in the url then continue processing else report an error
        if filename_end > 0:
            filename = url[: filename_end]
            result.update({'filename' : filename})

            # Extract prefixURI from the filename
            lastindex = filename.rfind("/")
            prefixuri = filename[:lastindex + 1]
            result.update({'prefixuri' : prefixuri})

            # Using post_filename_string figureout what was passed i.e. typename or namespace.
            post_filename_string = url[filename_end + 1:]
            result.update({'namespace' : post_filename_string})                

        #hack to deal emulate parse logic -- todo: fix parse logic
        elif url.endswith(".xml"):
            prefixuri =  schemaBaseLocation
            lastindex = url.find(".xml")
            filename=url
            result.update({'filename' : prefixuri + filename})
            result.update({'prefixuri' : prefixuri})
            result.update({'namespace' : filename[:lastindex] + ".v1_0_0"})

        if incorrect_url == True:
            result.update({'error' : 'Incorrect URL - Please specify a URL like:\n 1. http://<filename>#<namespace> or \n 2. http://<filename>#<datatype>\n e.g. http://localhost:9080/rest/v1/redfish.dmtf.org/redfish/v1/Chassis_v1#Chassis.Chassis'})

        return result

#################################################################
# Name: set_config_args                                         #
# Description:                                                  #
#  If not set, override the command line arguments with config  #
#  file.                                                        # 
#################################################################
def set_config_args(args, config):
    options = config._sections['default']
    if (args.directory == None) and 'directory' in options:
        args.directory = config.get('default', 'directory')
    if (args.url == None) and 'url' in options:
        args.url = config.get('default', 'url')
    if (args.copyright == None) and 'copyright' in options:
        args.copyright = config.get('default', 'copyright')
    if (args.outdir == None) and outdir in options:
        args.outdir = config.get('default', 'outdir')

#################################################################
# Name: main                                                    #
# Description:                                                  #
#  Method where the execution of webservice is inititated.      # 
#################################################################
def main():

    parser = argparse.ArgumentParser(description='Convert CSDL XML schema into Redfish style JSON schema')
    parser.add_argument('--directory', '-d', dest='directory', help='The directory of the CSDL files to convert')
    parser.add_argument('--url', '-u', dest='url', help='The url of the CSDL files to convert')
    parser.add_argument('--copyright', '-C', dest='copyright', help='The copyright notice to add to the JSON')
    parser.add_argument('--outdir', '-O', dest='outdir', default='./json', help='The output directory for the JSON schema output')
    parser.add_argument('--verbose', '-v', action='count', default=0, dest='verbose', help='Increase the verbosity of the output')

    args = parser.parse_args()

    if os.path.exists('.config.ini'):
        config = configparser.ConfigParser()
        config.readfp(open('.config.ini'))
        set_config_args(args, config)

    if args.copyright == None:
        args.copyright = 'Copyright 2014-2016 Distributed Management Task Force, Inc. (DMTF). For the full DMTF copyright policy, see http://www.dmtf.org/about/policies/copyright'

    if args.verbose >= 1:
        pdb.set_trace()

    # read the arguments passed to the service
    form = cgi.FieldStorage()

    if 'directory' in form:
        if enable_debugging == True:
            args.directory=form['directory']
        else:
            args.directory=form['directory'].value

    if 'url' in form:
        if enable_debugging == True:
            args.url = form['url']
        else:
            args.url = form['url'].value

    if (args.directory == None) and (args.url == None):
        parser.print_help()
        exit(1)

    if args.url != None:
        return generate_json(args.url, args.directory, args)
		                
    elif (args.directory != None):
         for file in os.listdir(args.directory):
             if ( file.endswith(".xml") ):
               print("generating JSON for: " + file)
               JsonSchemaGenerator.parsed = []
               generate_json(file, args.directory, args)

    else:
         result = UT.Utilities.show_interactive_mode("Please specify URL as part of the input")
         return result


#################################################################
# Name: generate_json                                           #
# Description:                                                  #
#  Generate JSON from inputs.                                   # 
#################################################################
def generate_json(url, directory, args):

    # Parse the URL and extract input values from the URL
    url_inputs = JsonSchemaGenerator.parse_url(url)
       
    typename = ''
    namespace = ''
    filename = ''
    prefixuri = ''
    error = ''
    specialodatatype = ''
    generateOdataFile = ''
    screenoutput = ''
    depth = 0
        
    if 'error' in url_inputs:
        error = url_inputs['error']
        result = UT.Utilities.show_interactive_mode(error)
    else:
        if 'filename' in url_inputs:
            filename = url_inputs['filename']
            
        if 'namespace' in url_inputs:
            namespace = url_inputs['namespace']

        if 'typename' in url_inputs:
            typename = url_inputs['typename']

        if 'prefixuri' in url_inputs:
            prefixuri = url_inputs['prefixuri']

        # create a dictionary from type names to type data
            
        jsonresults = {}
            
        # Create the type table
        typeinfo = JsonSchemaGenerator.generate_typetable(filename, directory, False)
        typetable = typeinfo["Typetable"]
        namespaces = typeinfo["Namespaces"]
			    
        # Create a JSON schema representation of the indicated file/namespace
        for currentnamespace in namespaces:
            # Create an object of JsonSchemaGenerator
            current_schema = JsonSchemaGenerator(currentnamespace)

            # Get Json results
            jsonresults = current_schema.generate_json_for_file(typetable, depth+1, "", filename, currentnamespace, prefixuri, False)

            # Generate the files with the results and then get the screen output
            screenoutput = JsonSchemaGenerator.generate_json_files(currentnamespace, jsonresults, args)
                
    return screenoutput


if __name__ == "__main__":
    result = main()
#    print(result)
