#! /usr/bin/python3
# Copyright Notice:
# Copyright 2022-2025 DMTF. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

"""
Redfish OEM Integrator

File : redfish-oem-integrator.py

Brief : A tool used to processes Redfish JSON Schema files and integrate any OEM definitions that are found in the configuration file.
"""

import argparse
import json
import os
import sys
import copy
import shutil
import re

class UnsupportedFeatureException(Exception):
    "Raised when it hits some feature which is not developed yet"
    pass

class IllegalSchemaModificationRequestException(Exception):
    "Raised when an illegal schema modification request is made"
    pass

class JsonSchemaConfigHelper:
    def __init__(self, schema_file, on_change_write_to=None, enabled_by_default=True):
        self.__schema_filepath = schema_file
        if on_change_write_to:
            self.__schema_out_file_path = os.path.abspath(on_change_write_to)
        else:
            self.__schema_out_file_path = on_change_write_to
        self.__schema_name = schema_file.rsplit("/",1)[-1].split(".",1)[0]
        self.__schema_in_file_path = os.path.abspath(schema_file.rsplit("/",1)[0])
        with open(self.__schema_filepath, "r") as fd:
            self.__schema = json.loads(fd.read())
        if "$ref" in self.__schema:
            self.__schema_name = self.__schema["$ref"].rsplit("/",1)[-1]
            self.__definition = self.__schema["definitions"][self.__schema_name]
        else:
            self.__definition = None
        self.__versions = None
        self.__max_version = None
        self.__is_changed = False
        self.__read_only_props = []
        self.__deleted_props = []
        self.__properties_in_use = set()
        self.__enabled = enabled_by_default
        self.__array_items_support = {}
        self.__strlen_support = {}

    def __del__(self):
        # Process the minItems/maxItems if any
        for prop_to_modify in self.__array_items_support:
            minItems = self.__array_items_support[prop_to_modify].get("minItems")
            maxItems = self.__array_items_support[prop_to_modify].get("maxItems")
            if minItems is not None:
                self.__mark_property_metainfo(prop_to_modify, "minItems", minItems)
            if maxItems is not None:
                self.__mark_property_metainfo(prop_to_modify, "maxItems", maxItems)
        for prop_to_modify in self.__strlen_support:
            minLength = self.__strlen_support[prop_to_modify].get("minLength")
            maxLength = self.__strlen_support[prop_to_modify].get("maxLength")
            if minLength is not None:
                self.__mark_property_metainfo(prop_to_modify, "minLength", minLength)
            if maxLength is not None:
                self.__mark_property_metainfo(prop_to_modify, "maxLength", maxLength)

        for prop_to_modify in sorted(self.__read_only_props, reverse=True):
            self.__mark_property_metainfo(prop_to_modify, "readonly", True)

        deleted_prop_base_paths = set()
        for prop_to_del in sorted(self.__deleted_props, reverse=False): # sorted order is critical to ensure if base is removed, sub properties need not be removed anymore
            if prop_to_del in self.__properties_in_use:
                # Someone is using it, do not delete
                continue
            do_delete_property = True
            for deleted_prop_base_path in deleted_prop_base_paths:
                # If a complex property is already deleted from the base of the resource tree,
                # members of the complex type need not be deleted as they may be referred from external schemas.
                # For instance,
                # if #/Prop1 is deleted,
                # no point in deleting #/Prop1/SubProp1
                if prop_to_del.startswith(deleted_prop_base_path+"/"):
                    do_delete_property = False
                    break

            if do_delete_property:
                print("Removing Property: {}".format(prop_to_del))
                self.__remove_property(prop_to_del)
                deleted_prop_base_paths.add(prop_to_del)

        if (self.__is_changed or
            (self.__schema_out_file_path != self.__schema_in_file_path)) and self.__schema_out_file_path != None:
            if self.__is_changed:
                print("Info: {}: Schema modified, writing to {}".format(self.__schema_name, self.__schema_out_file_path))
            else:
                print("Info: {}: Copying schema from source to {}".format(self.__schema_name, self.__schema_out_file_path))
            with open(self.__schema_out_file_path, "w") as fd:
                json.dump(self.__schema, fd, sort_keys=True, indent=4, separators = ( ",", ": " ))

    def __get_ref(self, d):
        ref = None
        if "$ref" in d:
            ref = d["$ref"]
        else:
            if d.get("type") == "array":
                d = d["items"]
            if "$ref"  in d:
                ref = d["$ref"]
            elif "anyOf" in d and type(d["anyOf"]) == list:
                for opt in d["anyOf"]:
                    if "$ref" in opt:
                        ref = opt["$ref"]
                        break
            else:
                raise(UnsupportedFeatureException)
        return ref

    def add_annotation(self, target, annotation_prop, annotation_details):
        '''Add an annotation under the specified Entity or ComplexType'''
        assert(target in self.__schema["definitions"]), f"Invalid Entity or ComplexType {target} specified in annotation path for {self.__schema_name} schema."
        assert("properties" in self.__schema["definitions"][target]), f"Invalid Entity or ComplexType {target} specified in annotation path for {self.__schema_name} schema."
        self.__schema["definitions"][target]["properties"][annotation_prop] = annotation_details
        self.__is_changed = True

    def add_oem_schema_link(self, prop, oem_name, oem_schema_path):
        oem_prop_key = prop + "_Oem"
        self.__schema["definitions"][prop]["properties"]["Oem"]["$ref"] = "#/definitions/{}".format(oem_prop_key)
        self.__schema["definitions"][oem_prop_key] = {
            "additionalProperties": False,
            "description": "An OEM extension to the {} resource.".format(self.get_name()),
            "longDescription": "This object represents the OEM properties of the {} resource. The resource values shall comply with the Redfish Specification-described requirements.".format(self.get_name()),
            "patternProperties": {
                "^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\\\.[a-zA-Z_][a-zA-Z0-9_]*$": {
                    "description": "This property shall specify a valid odata or Redfish property.",
                    "type": [
                        "array",
                        "boolean",
                        "integer",
                        "number",
                        "null",
                        "object",
                        "string"
                    ]
                }
            },
            "properties": {
                oem_name: {
                    "$ref": oem_schema_path,
                    "description": "An Oem extension to the {} resource by {}.".format(self.get_name(), oem_name),
                    "longDescription": "An Oem extension to the {} resource by {}.".format(self.get_name(), oem_name)
                }
            }
        }
        self.__is_changed = True

    def get_definition(self, object=None):
        if not object:
            return self.__definition
        else:
            return self.__schema["definitions"][object]

    def get_type_ref_of_property(self, prop, prop_d=None):
        if prop_d == None:
            prop_d = self.__definition
        assert(prop in prop_d["properties"]), "Invalid property {} specified".format(prop)
        return self.__get_ref(prop_d["properties"][prop])

    def is_oem(self):
        try:
            if self.__schema["owningEntity"] in ["DMTF", "SNIA"]:
                return False
            else:
                return True
        except Exception as _:
            #raise(e)
            #print(self.__schema_name)
            # TODO: Fix Oem and report others
            return True # Very unlikely for a standard schema to not have this property

    def is_update_capable(self):
        return self.__definition.get("updatable") if "updatable" in self.__definition else False

    def is_insert_capable(self):
        return self.__definition.get("insertable") if "insertable" in self.__definition else False

    def is_delete_capable(self):
        return self.__definition.get("deletable") if "deletable" in self.__definition else False

    def disable_delete_capability(self):
        assert(self.is_base_entity() or self.is_collection())
        if self.is_delete_capable():
            self.__definition["deletable"] = False
            self.__is_changed = True

    def disable_update_capability(self):
        assert(self.is_base_entity() or self.is_collection())
        if self.is_update_capable():
            self.__definition["updatable"] = False
            self.__is_changed = True

    def enable_update_capability(self):
        assert(self.is_base_entity() or self.is_collection())
        if not self.is_update_capable():
            self.__definition["updatable"] = True
            self.__is_changed = True

    def disable_insert_capability(self):
        assert(self.is_base_entity() or self.is_collection())
        if self.is_insert_capable():
            self.__definition["insertable"] = False
            self.__is_changed = True

    def get_name(self):
        return self.__schema_name

    def is_collection(self):
        if self.__definition:
            definition = self.__definition
            if "anyOf" not in definition:
                return False
            if len(definition["anyOf"]) > 2:
                return False
            found_id_ref = False
            found_members = False
            for anyof in definition["anyOf"]:
                if ("$ref" in anyof) and anyof["$ref"].endswith("/idRef"):
                    found_id_ref = True
                elif ("properties" in anyof) and ("Members" in anyof["properties"]):
                    found_members = True
            return found_id_ref & found_members
        return False

    def is_base_entity(self):
        if not self.__definition:
            return False
        if ("deletable" in self.__definition) \
            and ("insertable" in self.__definition) \
            and ("updatable" in self.__definition):
            return True
        else:
            if "title" in self.__schema and ".v1_" not in self.__schema["title"]:
                return True
            return False

    def is_versioned_entity(self):
        try:
            if self.__definition["type"] == "object":
                return True
            else:
                return False
        except Exception as _:
            return False

    def uris(self):
        if not self.__definition:
            return None
        uris = []
        if "uris" in self.__definition:
            uris = self.__definition["uris"]
        return uris

    def remove_uri(self, uri):
        assert(self.is_base_entity()), "Uris can be removed only from a base schema"
        try:
            self.__definition["uris"].remove(uri)
            self.__is_changed= True
        except Exception as _:
            pass
            #print("ERROR: {} does not have uri {}".format(self.__schema_name, uri))

    def add_uri(self, uri):
        assert(self.is_base_entity()), "Uris can only be added to a base schema"
        if "uris" not in self.__definition:
            self.__definition["uris"] = [uri]
            self.__is_changed= True
        else:
            if "uri" not in self.__definition["uris"]:
                self.__definition["uris"].append(uri)
                self.__is_changed= True

    def set_max_items(self, property_path, max_items):
        assert (max_items > 0), f"Invalid max items {max_items} passed"
        if property_path in self.__array_items_support and "minItems" in self.__array_items_support[property_path]:
            assert(self.__array_items_support[property_path]["minItems"] <= max_items)
            old_max = self.__array_items_support[property_path].get("maxItems", 0)
            if old_max < max_items:
                self.__array_items_support[property_path]["maxItems"] = max_items
        else:
            self.__array_items_support[property_path] = {"maxItems": max_items}

    def set_min_items(self, property_path, min_items):
        assert (min_items >= 0), f"Invalid min items {min_items} passed"
        if property_path in self.__array_items_support and "maxItems" in self.__array_items_support[property_path]:
            assert(self.__array_items_support[property_path]["maxItems"] >= min_items)
            old_min = self.__array_items_support[property_path].get("minItems", 0)
            if old_min > min_items:
                self.__array_items_support[property_path]["minItems"] = min_items
        else:
            self.__array_items_support[property_path] = {"minItems": min_items}
    def set_max_length(self, property_path, length):
        assert(length > 0), f"Invalid max length {length} passed"
        if property_path in self.__strlen_support and "minLength" in self.__strlen_support[property_path]:
            assert(self.__strlen_support[property_path]["minLength"] <= length)
            old_max = self.__strlen_support[property_path].get("maxLength", 0)
            if old_max < length:
                self.__strlen_support[property_path]["maxLength"] = length
        else:
            self.__strlen_support[property_path] = {"maxLength": length}

    def set_min_length(self, property_path, length):
        assert (length > 0), f"Invalid min length {length} passed"
        if property_path in self.__strlen_support and "maxLength" in self.__strlen_support[property_path]:
            assert(self.__strlen_support[property_path]["maxLength"] >= length)
            old_min = self.__strlen_support[property_path].get("minLength", 0)
            if old_min > length:
                self.__strlen_support[property_path]["minLength"] = length
        else:
            self.__strlen_support[property_path] = {"minLength": length}

    def mark_property_readonly(self, property_path):
        assert(self.is_versioned_entity()), "Property Capabilities can be updated only for versioned schemas"
        assert(property_path.startswith("#/") and len(property_path) > 2), "Invalid property path passed"
        self.__read_only_props.append(property_path)

    def mark_property_in_use(self, property_path):
        self.__properties_in_use.add(property_path)

    def __mark_property_metainfo(self, property_path, key, value):
        try:
            prop_path = property_path.split("/")[1:] # skip the '#'
            prop_d = {}
            print("prop paths: {}".format(prop_path))
            prop_d = self.__definition["properties"][prop_path[0]]
            # print("prop paths: {}".format(prop_path))
            # print("range: {}".format(list(range(len(prop_path)))))
            for i in range(len(prop_path)):
            # prop in prop_path[1:]:
                # print("i={}".format(i))
                # prop = prop_path[i]
                if i+1 == len(prop_path):
                    # print("Setting ../{} as ReadOnly".format(prop))
                    prop_d[key]=value
                    self.__is_changed= True
                else:
                    ref = self.__get_ref(prop_d)
                    # print("Resolving ref {}".format(ref))
                    assert(ref.startswith("#/definitions/"))
                    ref = ref.rsplit("/",1)[-1]
                    # print("Traversing from ../{}/.. to ../{}/{}/..".format(prop, prop, prop_path[i+1]))
                    prop_d = self.__schema["definitions"][ref]["properties"][prop_path[i+1]]
        except Exception as e:
            #print(self.__schema_name)
            #print(property_path)
            #print(prop_d)
            #raise(e)
            pass

    def remove_action(self, action):
        assert(self.is_versioned_entity()), "Actions are present only in versioned schemas"
        action_ref = self.__get_ref(self.__schema["definitions"]["Actions"]["properties"][action])
        assert(action_ref.startswith("#/definitions/"))
        action_def_key = action_ref.rsplit("/",1)[-1]
        if "actionResponse" in self.__schema["definitions"][action_def_key]:
            actionresponse_ref = self.__get_ref(self.__schema["definitions"][action_def_key]["actionResponse"])
            assert(actionresponse_ref.startswith("#/definitions/"))
            actionresponse_def_key = actionresponse_ref.rsplit("/",1)[-1]
            self.__schema["definitions"].pop(actionresponse_def_key)
        self.__schema["definitions"].pop(action_def_key)
        self.__schema["definitions"]["Actions"]["properties"].pop(action)
        self.__is_changed= True

    def remove_action_params(self, action, param, is_input_param):
        try:
            assert(self.is_versioned_entity()), "Action Parameters can be deleted only for versioned schemas"
            if is_input_param:
                action_params_d = self.__schema["definitions"][action].get("parameters")
                param_d = action_params_d.get(param)
                if param_d == None:
                    raise(KeyError)
                if param_d.get("requiredParameter") == True:
                    raise(IllegalSchemaModificationRequestException)
                action_params_d.pop(param)
                self.__is_changed= True
            else:
                raise(UnsupportedFeatureException)
        except (AttributeError, KeyError):
            # Action/parameter might not be supported in this version of the schema; ignore it
            pass
        except Exception as e:
            print(f"Got Exception: {e}")
            raise(e)

    def remove_property(self, property_path):
        assert(self.is_versioned_entity()), "Property can be deleted only for versioned schemas"
        assert(property_path.startswith("#/") and len(property_path) > 2), "Invalid property path passed"
        self.__deleted_props.append(property_path)

    def __remove_property(self, property_path):
        try:
            prop_path = property_path.split("/")[1:] # skip the '#'
            parent_prop_d = self.__definition["properties"]
            #print("prop paths: {}".format(prop_path))
            #print("range: {}".format(list(range(len(prop_path)))))
            for i in range(len(prop_path)):
            #prop in prop_path[1:]:
                #print("i={}".format(i))
                prop = prop_path[i]
                if i+1 == len(prop_path):
                    print("Removing ../{}".format(prop))
                    #prop_d["readonly"]=True
                    parent_prop_d.pop(prop)
                    self.__is_changed= True
                else:
                    ref = self.__get_ref(parent_prop_d[prop])
                    #print("Resolving ref {}".format(ref))
                    assert(ref.startswith("#/definitions/"))
                    ref = ref.rsplit("/",1)[-1]
                    #print("Traversing from ../{}/.. to ../{}/{}/..".format(prop, prop, prop_path[i+1]))
                    parent_prop_d = self.__schema["definitions"][ref]["properties"]
        except Exception as _:
            #print(self.__schema_name)
            #print(property_path)
            #print(parent_prop_d[prop])
            #raise(e)
            print("Warning: {} could not be removed/was already removed".format(property_path))

    def versions(self):
        if not self.is_base_entity():
            return None
        if self.__versions:
            return self.__versions
        versions = []
        for item in self.__definition["anyOf"]:
            ref = item["$ref"]
            if ref.endswith("/idRef"):
                continue
            versions.append(ref.split("#",1)[0].rsplit("/",1)[-1])
        self.__versions = sorted(versions, key = lambda x: tuple(x.split(".")[1][1:].split("_")))
        self.__max_version = self.__versions[-1]
        return self.__versions

    def __properties(self, definition, is_action_params):
        properties = {}
        prop_key = "parameters" if is_action_params else "properties"
        if prop_key not in definition:
            if "enum" in definition:
                # TODO: Enums
                properties = {"@meta.Enums": {x:True for x in definition["enum"]}}
                return properties
            else:
                print("ZZ{} --> {}".format(self.__schema["title"], definition))
        for prop in definition[prop_key]:
            if not is_action_params:
                if prop.startswith("@odata") or prop in ("Id", "Name", "Description"):
                    continue
                if "parameters" in definition and "properties" in definition:
                    # These are standard properties for Actions, target is mandatory
                    if prop not in ["target"]:
                        properties[prop] = {"@meta.Enabled": self.__enabled}
                    else:
                        print("Not setting for {}".format(prop))
                        properties[prop] = {}
                    continue
            prop_d = definition[prop_key][prop]
            properties[prop] = {"@meta.Enabled": self.__enabled}
            # Check if proprty type is array
            typ = prop_d.get("type")
            if typ and typ == "array":
                # Add support to configure in such cases
                properties[prop]["@meta.minItems"] = None
                properties[prop]["@meta.maxItems"] = None
            if is_action_params:
                if prop_d.get("requiredParameter") == True:
                    # Do not give a chance to disable a mandatory parameter
                    properties[prop].pop("@meta.Enabled")
            else:
                if (("required" in definition and prop in definition["required"]) or
                    ("requiredOnCreate" in definition and prop in definition["requiredOnCreate"])):
                    # Do not give a chance to disable a required property
                    properties[prop].pop("@meta.Enabled")
            if (not is_action_params) and "readonly" in prop_d:
                # Presence of this key indicates it is a simple type or an array of simple types
                if prop_d["readonly"]==False:
                    properties[prop]["@meta.AllowWrite"] = True
            else:
                #Indicates it is a Complex property of Array of Complex Properties
                if "items" in prop_d:
                    # It is an array of complextype
                    if "anyOf" in prop_d["items"]:
                        # Possibly Supports null as well
                        # TODO: Prove this
                        for item in prop_d["items"]["anyOf"]:
                            if "$ref" in item:
                                ref = item["$ref"]
                                if ref.startswith("#/definitions/") and (ref != self.__schema["$ref"]):
                                    #It is defined locally in the same file, expand it
                                    properties[prop].update(self.__properties(self.__schema["definitions"][ref.rsplit("/",1)[-1]], is_action_params=False))
                    elif "type" in prop_d["items"]:
                        # Is a simple type of array
                        # Do nothing
                        pass
                    else:
                        #Does not support Null
                        try:
                            ref = prop_d["items"]["$ref"]
                        except:
                            print(prop_d)
                            raise
                        if ref.startswith("#/definitions/") and (ref != self.__schema["$ref"]):
                            #It is defined locally in the same file, expand it
                            properties[prop].update(self.__properties(self.__schema["definitions"][ref.rsplit("/",1)[-1]], is_action_params=False))
                        #print("XX{} --> {}".format(self.__schema["title"], prop))

                elif "anyOf" in prop_d:
                    # It is a complextype
                    #print("YY{} --> {}".format(self.__schema["title"], prop))
                    for item in prop_d["anyOf"]:
                        if "$ref" in item:
                            ref = item["$ref"]
                            if ref.startswith("#/definitions/") and (ref != self.__schema["$ref"]):
                                #It is defined locally in the same file, expand it
                                properties[prop].update(self.__properties(self.__schema["definitions"][ref.rsplit("/",1)[-1]], is_action_params=False))
                elif "$ref" in prop_d:
                    # It is a complextype and does not support anyof
                    ref = prop_d["$ref"]
                    if ref.startswith("#/definitions/") and (ref != self.__schema["$ref"]):
                        #It is defined locally in the same file, expand it
                        properties[prop].update(self.__properties(self.__schema["definitions"][ref.rsplit("/",1)[-1]], is_action_params=False))
                else:
                    pass#print("AAAAA-> {}".format(prop))
        return properties

    def actions(self):
        if not self.is_versioned_entity():
            return None
        definitions = self.__schema["definitions"]
        if "Actions" not in definitions:
            return {}
        if "properties" not in definitions["Actions"]:
            return {}
        #actions = [x for x in definitions["Actions"]["properties"]]# if x != "Oem"]
        actions = {}
        for action in [x for x in definitions["Actions"]["properties"]]:
            action_d = definitions["Actions"]["properties"][action]
            if action == "Oem":
                actions[action]={
                    #"@meta.Enabled": True
                    }
                continue
            actions[action]={
                    #"@meta.Enabled": True,
                    "input_parameters": {},
                    "output_parameters": {}
                }
            ref = action_d["$ref"].rsplit("/",1)[-1]
            actions[action]["input_parameters"] = self.__properties(self.__schema["definitions"][ref], is_action_params = True)
            if "actionResponse" in self.__schema["definitions"][ref]:
                # It has a defined Action Response
                resp_ref = self.__schema["definitions"][ref]["actionResponse"]["$ref"].rsplit("/",1)[-1]
                actions[action]["output_parameters"] = self.__properties(self.__schema["definitions"][resp_ref], is_action_params = False)
        return actions

    def properties(self):
        if not self.__definition:
            return None
        return self.__properties(self.__definition, is_action_params = False)

    def latest_schema(self):
        if self.__max_version:
            return self.__max_version
        self.versions()
        return self.__max_version

class JSONSchemaConfigManager:
    def __init__(self, schema_source_path, schema_dest_path, cfg):
        self.__schema_source_path = schema_source_path
        self.__schema_dest_path = schema_dest_path
        self.__config_file_path = cfg["OemConfigurationFilePath"]
        self.__separate_configs = cfg["StoreConfigInSeparateFiles"]
        self.__config_dir = self.__config_file_path.rsplit('/', 1)[0]
        self.__config_d = {}
        self.__diff = {
                "new_schemas": [],
                "old_schemas": {}
            }
        self.__enabled_default_value = cfg["EnableNewAdditionsByDefault"]

    def generate_config(self):
        """"""
        for file in sorted(os.listdir(self.__schema_source_path)):
            if ".v" in file:
                continue #Will load up only the latest versions as extracted from the base schemas
            schema_name = file.split(".",1)[0]
            f_path = os.path.abspath(os.path.join(self.__schema_source_path, file))
            json_schema = JsonSchemaConfigHelper(
                schema_file=f_path,
                on_change_write_to=None,
                enabled_by_default=self.__enabled_default_value)
            '''if json_schema.isOem():
                # Skip schema
                continue'''
            #print(json_schema.get_name())
            self.__config_d[schema_name] = {}
            if json_schema.is_collection():
                self.__config_d[schema_name]["uris"] = {x:{"@meta.Enabled":self.__enabled_default_value} for x in json_schema.uris()}
                self.__config_d[schema_name]["capabilities"] = {
                            "deletable": {"dmtf": json_schema.is_delete_capable()}, # Collections cannot be deleted
                            "updatable": {"dmtf": json_schema.is_update_capable()}, # Collections cannot be patched
                            "insertable": {"dmtf": json_schema.is_insert_capable()}
                        }
                if json_schema.is_insert_capable():
                    self.__config_d[schema_name]["capabilities"]["insertable"]["@meta.oem"] = True # Allow to restrict capability
            elif json_schema.is_base_entity():
                self.__config_d[schema_name]["uris"] = {x:{"@meta.Enabled":self.__enabled_default_value} for x in json_schema.uris()}
                self.__config_d[schema_name]["capabilities"] = {
                            "deletable": {"dmtf": json_schema.is_delete_capable()},
                            "updatable": {"dmtf": json_schema.is_update_capable(), "@meta.oem": json_schema.is_update_capable()}, # Implementations may override updatable capability of schemas, e.g. adding new patchable Oem properties
                            "insertable": {"dmtf": json_schema.is_insert_capable()} # Instances cannot be POST-ed
                        }
                if json_schema.is_delete_capable():
                    self.__config_d[schema_name]["capabilities"]["deletable"]["@meta.oem"] = True # Allow to restrict capability
                #if json_schema.isUpdateCapable():
                #    self.__config_d[schema_name]["capabilities"]["updatable"]["@meta.oem"] = True # Allow to restrict capability
                # TODO: Check if this is really needed
                #self.__config_d[schema_name]["versions_supported"] = {x: {"@meta.Enabled": True} for x in json_schema.versions()}
                latest_schema = json_schema.latest_schema()
                latest_schema_path = os.path.abspath(os.path.join(self.__schema_source_path, latest_schema))
                inst_schema = JsonSchemaConfigHelper(
                    schema_file=latest_schema_path,
                    on_change_write_to=None,
                    enabled_by_default=self.__enabled_default_value)
                if inst_schema.is_versioned_entity():
                    self.__config_d[schema_name]["actions"] = inst_schema.actions()
                    self.__config_d[schema_name]["properties"] = inst_schema.properties()
            else:
                # These are only referenced from elsewhere, no customizations allowed
                print("Reference Only Schema: {}".format(schema_name))

    def __found_new_schema(self, schema):
        self.__diff["new_schemas"].append(schema)

    def __found_new_action(self, schema, action):
        if schema not in self.__diff["old_schemas"]:
            self.__diff["old_schemas"][schema]={
                    "new_properties": [],
                    "new_actions": [],
                    "now_writable_properties": [],
                    "new_uris": []
                }
        self.__diff["old_schemas"][schema]["new_actions"].append(action)

    def __found_new_uri(self, schema, uri):
        if schema not in self.__diff["old_schemas"]:
            self.__diff["old_schemas"][schema]={
                    "new_properties": [],
                    "new_actions": [],
                    "now_writable_properties": [],
                    "new_uris": []
                }
        self.__diff["old_schemas"][schema]["new_uris"].append(uri)

    def __found_new_property(self, schema, prop):
        if schema not in self.__diff["old_schemas"]:
            self.__diff["old_schemas"][schema]={
                    "new_properties": [],
                    "new_actions": [],
                    "now_writable_properties": [],
                    "new_uris": []
                }
        self.__diff["old_schemas"][schema]["new_properties"].append(prop)

    def __found_property_now_writable(self, schema, prop):
        if schema not in self.__diff["old_schemas"]:
            self.__diff["old_schemas"][schema]={
                    "new_properties": [],
                    "new_actions": [],
                    "now_writable_properties": [],
                    "new_uris": []
                }
        self.__diff["old_schemas"][schema]["now_writable_properties"].append(prop)

    def __merge_properties_recursively(self, schema, new_prop_d, old_prop_d, prop, prop_path="#"):
        #Skip merging any @OEM stuff in properties, they will be processed separately
        if prop.startswith("@OEM."):
            return
        #print("Merging {}/{} in {}".format(prop_path, prop, schema))
        if prop not in old_prop_d:
            # New Property, merge the complete block
            self.__found_new_property(schema, prop_path + "/" + prop)
            #old_prop_d[prop] = new_prop_d[prop]
            # Nothing to do, the generated config is the one to write back
            #print("Adding new property: {}/{}".format(prop_path, prop))
        else:
            # Property is not new
            for merge_key in ["@meta.AllowWrite", "@meta.Enabled"]:
                if merge_key in new_prop_d[prop] and merge_key not in old_prop_d[prop]:
                    # Property was made writable newly
                    self.__found_property_now_writable(schema, prop_path + "/" + prop)
                    # Copy the meta info from new to old
                    #old_prop_d[prop]["@meta.AllowWrite"] = new_prop_d[prop]["@meta.AllowWrite"]
                    # Nothing to do, the generated config is the one to write back
                    #print("Adding @meta.AllowWrite: {}/{}".format(prop_path, prop))
                elif merge_key in new_prop_d[prop] and merge_key in old_prop_d[prop]:
                    # Preserve value from Old
                    new_prop_d[prop][merge_key] = old_prop_d[prop][merge_key]
            for merge_key in ["@meta.minItems", "@meta.maxItems"]:
                if merge_key in old_prop_d[prop] and merge_key in new_prop_d[prop]:
                    # Keep configured value if valid
                    if old_prop_d[prop][merge_key] and old_prop_d[prop][merge_key] > 0: # 0 is valid
                        new_prop_d[prop][merge_key] = old_prop_d[prop][merge_key]
                    else:
                        new_prop_d[prop][merge_key] = None # Set to None indicating that it has not been configured

            for merge_key in ["@meta.minLength", "@meta.maxLength"]:
                # This is a manually added one, not specified by the CSDL spec
                if merge_key in old_prop_d[prop]:
                    new_prop_d[prop][merge_key] = old_prop_d[prop][merge_key]

            sub_properties = [x for x in new_prop_d[prop] if not x.startswith("@meta.")]
            for sub_prop in sub_properties:
                if sub_prop not in old_prop_d[prop]:
                    # New subproperty, merge entire block
                    #old_prop_d[prop][sub_prop]=new_prop_d[prop][sub_prop]
                    #print("Adding new property: {}/{}/{}".format(prop_path, prop, sub_prop))
                    # Nothing to do, the generated config is the one to write back
                    pass
                else:
                    # Recursively merge all subproperties
                    self.__merge_properties_recursively(schema, new_prop_d[prop], old_prop_d[prop], sub_prop, prop_path + "/" + prop)

    def __merge_oem_config_directives(self, current_config, generated_config):
        """"""
        if type(current_config) != type(generated_config):
            return
        assert(type(current_config) != list), "No list types supported yet in configs"
        if type(current_config) == dict:
            # Iterate and copy all keys starting with @OEM.
            for oem_key in [k for k in current_config.keys() if k.startswith("@OEM.")]:
                generated_config[oem_key] = current_config[oem_key]
            # For all other keys present on both the configs, recursively merge
            for key in [k for k in current_config.keys() if (not k.startswith("@OEM.")) and (k in generated_config)]:
                if type(current_config[key]) in [list, dict]:
                    self.__merge_oem_config_directives(current_config[key], generated_config[key])


    def merge_configs(self):
        """Merge the existing configuration into the newly generated configuration. This will not modify customizable values."""
        try:
            # Load the current configuration
            with open(self.__config_file_path, "r") as fd:
                current_config = json.load(fd)
                for schema in current_config.keys():
                    if "$ref" in current_config[schema]:
                        expansion_file = os.path.join(self.__config_dir, current_config[schema]["$ref"])
                        try:
                            with open(expansion_file, "r") as fd2:
                                current_config[schema] = json.load(fd2)
                        except Exception as _:
                            print("XX")
                            current_config[schema] = {}
        except Exception as _:
            print("X")
            current_config = {}

        # First merge all the @OEM.* directives from current config to the generated config
        self.__merge_oem_config_directives(current_config, self.__config_d)

        try:
            # Merge the existing config into the generated DMTF config, keep Oem configured values intact
            # This will ensure DMTF config format will always be updated with the custom configs.
            for schema in self.__config_d:
                # Iterate for each schema in the generated config and merge data from current config
                if schema not in current_config:
                    # New Schema, copy entire schema block to current config
                    self.__found_new_schema(schema)
                    #current_config[schema] = self.__config_d[schema]
                    # Nothing to do, the generated config is the one to write back
                    continue

                if "capabilities" in self.__config_d[schema]:
                    if "capabilities" not in current_config[schema]:
                        #current_config[schema]["capabilities"] = self.__config_d[schema]["capabilities"]
                        # Nothing to do, the generated config is the one to write back
                        pass # TODO??
                    else:
                        for capability in self.__config_d[schema]["capabilities"]:
                            #TODO:  Add this condition back once new schema processor is compelete. Have changed for now to keep the meta changes as it is for non modified csdl schemas
                            # if ("@meta.oem" in self.__config_d[schema]["capabilities"][capability] and
                            if ("@meta.oem" in current_config[schema]["capabilities"][capability]):
                                # if present in both, merge the oem config
                                self.__config_d[schema]["capabilities"][capability]["@meta.oem"] = current_config[schema]["capabilities"][capability]["@meta.oem"]

                if "actions" in self.__config_d[schema]:
                    if "actions" in current_config[schema]:
                        # Attempt to merge
                        curr_actions_d = current_config[schema]["actions"]
                        for action in curr_actions_d:
                            if action.startswith("@"):
                                continue
                            if action not in self.__config_d[schema]["actions"]:
                                print("Action {} found in previous config but not in the newly generated DMTF config. Removing {} from config!".format(action, action))
                                continue
                            #self.__config_d[schema]["actions"][action]["@meta.Enabled"] = curr_actions_d[action]["@meta.Enabled"] # Copy this user config
                            for param_typ in ["input_parameters", "output_parameters"]:
                                if param_typ in curr_actions_d[action]:
                                    for param in curr_actions_d[action][param_typ]:
                                        if (("@meta.Enabled" in curr_actions_d[action][param_typ][param]) and
                                            ("@meta.Enabled" in self.__config_d[schema]["actions"][action][param_typ][param])):
                                            self.__config_d[schema]["actions"][action][param_typ][param]["@meta.Enabled"] = curr_actions_d[action][param_typ][param]["@meta.Enabled"]
                    '''else:
                        for action in self.__config_d[schema]["actions"]:
                            # Iterate through all the actions in the generated config
                            #if "actions" not in current_config[schema]:
                                # New actions coming up
                                #current_config[schema]["actions"]={}
                                # Nothing to do, the generated config is the one to write back
                                #pass
                            if action not in current_config[schema]["actions"]:
                                # This action was added newly, copy entire action block to current config
                                self.__found_new_action(schema, action)
                                #current_config[schema]["actions"][action] = self.__config_d[schema]["actions"][action]
                                # Nothing to do, the generated config is the one to write back
                                continue
                            # TODO: Check for changes in existing actions
                            # TODO: do for action input/output parameters as well
                            if '''

                if "uris" in self.__config_d[schema]:
                    for uri in self.__config_d[schema]["uris"]:
                        # Iterate through all the uris in the generated config
                        if uri not in current_config[schema]["uris"]:
                            # This uri was newly added, add this uri to current config
                            self.__found_new_uri(schema, uri)
                            #current_config[schema]["uris"][uri]=True
                            # Nothing to do, the generated config is the one to write back
                        else:
                            # Overwrite new config with current config
                            self.__config_d[schema]["uris"][uri]["@meta.Enabled"] = current_config[schema]["uris"][uri]["@meta.Enabled"]
                    # Copy any Oem defined URIs
                    for uri in current_config[schema]["uris"]:
                        if uri not in self.__config_d[schema]["uris"]:
                             self.__config_d[schema]["uris"][uri] = current_config[schema]["uris"][uri]

                if "properties" in self.__config_d[schema]:
                    if "properties" not in current_config[schema]:
                        # New properties coming up
                        #current_config[schema]["properties"]={}
                        # Nothing to do, the generated config is the one to write back
                        #print("Adding ALL NEW properties: {}".format(schema))
                        pass
                    for prop in self.__config_d[schema]["properties"]:
                        # Iterate through all the properties in the generated config
                        self.__merge_properties_recursively(schema, self.__config_d[schema]["properties"], current_config[schema]["properties"], prop)
                else:
                    if not schema.endswith("Collection"):
                        print("XXXXXXXXXXXXXXXXXXXXX %s" %(schema))
            #self.__config_d = current_config
            #print("="*10)
            #print(self.__config_d)
        except Exception as e:
            print(schema)
            raise(e)

    def write_config(self):
        if not os.path.exists(self.__config_dir):
            os.makedirs(self.__config_dir)
        with open(self.__config_file_path, "w") as fd:
            if not self.__separate_configs:
                #Store entire config in a single file
                json.dump(self.__config_d, fd, sort_keys=True, indent=2)
            else:
                #Break into individual files
                config_to_write = copy.deepcopy(self.__config_d)
                for schema in sorted(config_to_write.keys()):
                    new_file = os.path.join(self.__config_dir, schema) + ".json"
                    with open(new_file, "w") as fd2:
                        json.dump(config_to_write[schema], fd2, sort_keys=True, indent=2)
                    config_to_write[schema] = {"$ref": schema+".json"}
                json.dump(config_to_write, fd, sort_keys=True, indent=2)
        #with open("diff.json", "w") as fd:
        #    json.dump(self.__diff, fd, sort_keys=True, indent=2)

    def __process_properties(self, schema_obj, property, prop_d, prop_path="#"):
        my_prop_path = prop_path + "/" + property
        minItems = prop_d.get("@meta.minItems")
        maxItems = prop_d.get("@meta.maxItems")
        minLength = prop_d.get("@meta.minLength")
        maxLength = prop_d.get("@meta.maxLength")

        if minItems:
            schema_obj.set_min_items(my_prop_path, minItems)
        if maxItems:
            schema_obj.set_max_items(my_prop_path, maxItems)
        if maxLength:
            schema_obj.set_max_length(my_prop_path, maxLength)
        if minLength:
            schema_obj.set_min_length(my_prop_path, minLength)
        if "@meta.AllowWrite" in prop_d and not prop_d["@meta.AllowWrite"]:
            print("{}: Marking property {} as ReadOnly".format(schema_obj.get_name(), my_prop_path)) #TODO: what if it is a complex prop with mismatching capabilities
            schema_obj.mark_property_readonly(my_prop_path)
        if "@meta.Enabled" in prop_d and not prop_d["@meta.Enabled"]:
            print("{}: Marking property for removal {}".format(schema_obj.get_name(), my_prop_path)) #TODO: what if it is a complex prop with mismatching capabilities
            schema_obj.remove_property(my_prop_path)
        else:
            # Property in use, make a note of it
            schema_obj.mark_property_in_use(my_prop_path)
        for sub_property, prop_d in prop_d.items():
            if sub_property.startswith("@meta.") or sub_property.startswith("@OEM."):
                continue
            self.__process_properties(schema_obj, sub_property, prop_d, my_prop_path)

    # def __process_actions(self, schema_obj, action, action_d):
    #     # if action_d.get("@meta.Enabled") == False:
    #     #     schema_obj.removeAction(action)
    #     if

    def __process_action_params(self, schema_obj, action, action_d):
        """"""
        for param_type, is_input in [("input_parameters", True)]: # TODO: Code for ("output_parameters", False)]
            params_d = action_d.get(param_type)
            if params_d == None:
                continue
            for param, param_d in params_d.items():
                if param_d.get("@meta.Enabled") == False:
                    # remove param
                    action_name = action.rsplit(".",1)[-1]
                    schema_obj.remove_action_params(action_name, param, is_input)

    def process_configs(self):
        """"""
        try:
            for schema_file in sorted(os.listdir(self.__schema_source_path)):
                schema_name = schema_file.split(".",1)[0]
                in_schema_path = os.path.join(self.__schema_source_path, schema_file)
                out_schema_path = os.path.join(self.__schema_dest_path, schema_file)
                schema_obj = JsonSchemaConfigHelper(
                    schema_file = in_schema_path,
                    on_change_write_to = out_schema_path,
                    enabled_by_default = self.__enabled_default_value)
                #print ("Processing: {}".format(schema_file))

                if schema_obj.is_collection() or schema_obj.is_base_entity():
                    if schema_name in self.__config_d:
                        schema_conf_d = self.__config_d[schema_name]

                        # Perform unsupported URIs removal and Oem uris addition
                        for uri, uri_info in schema_conf_d["uris"].items():
                            is_enabled = uri_info["@meta.Enabled"]
                            if not is_enabled:
                                print("{}: Removing URI {}".format(schema_name, uri))
                                schema_obj.remove_uri(uri)
                            elif uri not in schema_obj.uris() and is_enabled:
                                print("{}: Adding URI {}".format(schema_name, uri))
                                schema_obj.add_uri(uri)

                        # Change Schema capability
                        for cap, cap_conf in schema_conf_d["capabilities"].items():
                            if ("@meta.oem" in cap_conf) and (cap_conf["@meta.oem"] != cap_conf["dmtf"]):
                                assert(cap in ["updatable", "deletable", "insertable"])
                                if cap == "updatable":
                                    if cap_conf["@meta.oem"] == True:
                                        schema_obj.enable_update_capability()
                                    else:
                                        schema_obj.disable_update_capability()
                                elif cap_conf["@meta.oem"] == False:
                                    if cap == "deletable":
                                        schema_obj.disable_delete_capability()
                                    else:
                                        schema_obj.disable_insert_capability()
                                else:
                                    raise(IllegalSchemaModificationRequestException)
                elif schema_obj.is_versioned_entity():
                    if schema_name in self.__config_d:
                        # Perform property Updates (RW->RO) and Deletions
                        for property, prop_d in schema_conf_d["properties"].items():
                            self.__process_properties(schema_obj, property, prop_d)

                        # Process Actions
                        if "actions" in schema_conf_d:
                            for action, action_d in schema_conf_d["actions"].items():
                                if action.startswith("@"):
                                    continue
                                # Process only if action is supported
                                if schema_conf_d["properties"]["Actions"][action].get("@meta.Enabled") != True:
                                    continue
                                self.__process_action_params(schema_obj, action, action_d)

                                # self.__process_actions(schema_obj, action, action_d)


                # Versions
                # Always go latest

                '''elif schema_obj.isBaseEntity():
                    #pass#print("\tBase Schema.... Update Capabilities and supported URIs")
                    if schema_name in self.__config_d:
                        schema_conf_d = self.__config_d[schema_name]
                        #Remove unsupported URIs
                        for uri, is_enabled in schema_conf_d["uris"].items():
                            if not is_enabled:
                                print("{}: Removing URI {}".format(schema_name, uri))
                                schema_obj.removeUri(uri)
                elif schema_obj.isVersionedEntity():
                    #pass#print("\tVersioned Schema.... Remove unsupported properties, parameters and enums, update capabilities, etc")
                    for property, prop_d in schema_conf_d["properties"].items():
                        self.__process_properties(schema_obj, property, prop_d)
                else:
                    pass#print("Skipped!!!")'''
        except Exception as e:
            print("SchemaName: {}".format(schema_name))
            print(schema_conf_d)
            raise(e)

'''if __name__ == "__main__":
    with open("dmtf-config.json", "r") as fd:
        cfg = json.load(fd)
    cfgmgr = JSONSchemaConfigManager(schema_path, cfg)
    cfgmgr.generate_config()
    cfgmgr.merge_configs()
    cfgmgr.write_config()'''

#######

class DMTFOemIntegrator:
    """
    Class for managing Oem bindings into DMTF Schemas

    Args:
        json_in_file_path: The path to Redfish JSON Schema files to reference
        json_out_file_path: The path to Redfish JSON Schema files which will be generated
        dmtf_oem_bindings: Config file with all dmtf-to-oem bindings
    """

    def __init__( self, json_in_file_path, json_out_file_path, config ):
        self.config = config
        self.json_in_file_path = json_in_file_path
        self.json_out_file_path = json_out_file_path
        cfgmgr = JSONSchemaConfigManager(json_in_file_path, json_out_file_path, config)
        cfgmgr.generate_config()
        cfgmgr.merge_configs()
        cfgmgr.write_config()
        cfgmgr.process_configs()
        oem_binding_file_path = config.get("OemBindingsFilePath", None)
        if oem_binding_file_path:
            with open(config["OemBindingsFilePath"]) as fd:
                self.__oem_bindings = json.load(fd)
        else:
            self.__oem_bindings = None
        annotations_file_path = config.get("AnnotationsFilePath", None)
        if annotations_file_path:
            with open(config["AnnotationsFilePath"]) as fd:
                self.__annotations = json.load(fd)
        else:
            self.__annotations = None


    def integrate_oems(self):
        """
        Process all the DMTF-Oem bindings.
        Read files from json_out_file_path and overwrite the files
        """
        def get_paths(d, path=[]):
            paths = []
            if type(d) == dict:
                for p in d.keys():
                    if type(d[p]) == dict:
                        paths.extend(get_paths(d[p], path+[p]))
                    else:
                        paths.append(path+[p])
            return paths
        for schema, schema_bindings in self.__oem_bindings.items():
            for prop, binding in schema_bindings.items():
                if prop == "OemActions":
                    print("Found OemAction extension for the %s resource" %(schema))
                    # Now Open the Json file and write it
                    file_pat = "%s.v" %schema
                    for fname in sorted(os.listdir(self.json_out_file_path)):
                        try:
                            if fname.startswith(file_pat):
                                print("Extending %s with OemActions %s" %(fname, ", ".join(sorted(binding.keys()))))
                                in_schema_path = os.path.join(self.json_out_file_path, fname)
                                out_schema_path = os.path.join(self.json_out_file_path, fname)
                                with open(in_schema_path, "r") as fd:
                                    jsonschema = json.load(fd)
                                new_binding = {}
                                for action_schema_name in binding:
                                    action_name = action_schema_name.split(".")[-1]
                                    old_ref = binding[action_schema_name]["$ref"]
                                    old_ref_file = old_ref.split("#",1)[0].rsplit("/",1)[-1]
                                    old_ref_file_path = os.path.join(self.json_in_file_path, old_ref_file)

                                    with open(old_ref_file_path) as fd:
                                        old_ref_file_obj = json.load(fd)
                                        action_ref_latest = old_ref_file_obj["definitions"][action_name]["anyOf"][-1]["$ref"]
                                        new_binding[action_schema_name] = {"$ref":action_ref_latest}
                                jsonschema["definitions"]["OemActions"]["properties"] = new_binding

                                with open(out_schema_path, "w") as fd:
                                    json.dump(jsonschema, fd, indent = 4, sort_keys=True, separators=(',', ': '))
                        except Exception as e:
                            print("Unable to extend %s with OemActions %s: Exception (%s)" %(fname, ", ".join(sorted(binding.keys())), e))
                elif prop == "Oem":
                    print("Found Oem extension for the %s resource" %(schema))
                    key_name = "%s_%s" %(schema, prop)
                    new_json_data = {
                                        "additionalProperties": False,
                                        "description": "The OEM extension to the %s resource." %(schema),
                                        "longDescription": "This object represents the OEM properties. The resource values shall comply with the Redfish Specification-described requirements.",
                                        "patternProperties": {
                                            "^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\\\.[a-zA-Z_][a-zA-Z0-9_]*$": {
                                                "description": "This property shall specify a valid odata or Redfish property.",
                                                "type": [
                                                    "array",
                                                    "boolean",
                                                    "integer",
                                                    "number",
                                                    "null",
                                                    "object",
                                                    "string"
                                                ]
                                            }
                                        },
                                        "properties": {},
                                        "type": "object"
                                    }
                    for oem_name, oem_binding in binding.items():
                        new_json_data["properties"][oem_name] = {
                                                "$ref": oem_binding["$ref"],
                                                "description": "An Oem extension to the %s resource." %(schema),
                                                "longDescription": "An Oem extension to the %s resource." %(schema)
                                            }
                    # Now Open the Json file and write it
                    file_pat = "%s.v" %schema
                    for fname in sorted(os.listdir(self.json_out_file_path)):
                        try:
                            if fname.startswith(file_pat):
                                print("Extending %s with Oem %s" %(fname, key_name))
                                in_schema_path = os.path.join(self.json_out_file_path, fname)
                                out_schema_path = os.path.join(self.json_out_file_path, fname)
                                with open(in_schema_path, "r") as fd:
                                    jsonschema = json.load(fd)
                                jsonschema["definitions"][key_name] = new_json_data
                                jsonschema["definitions"][jsonschema["$ref"].rsplit("/",1)[-1]]["properties"]["Oem"]["$ref"] = "#/definitions/%s" %(key_name)

                                with open(out_schema_path, "w") as fd:
                                    json.dump(jsonschema, fd, indent = 4, sort_keys=True, separators=(',', ': '))
                        except Exception as e:
                            print("Unable to extend %s with Oem %s: Exception (%s)" %(fname, key_name, e))
                elif prop == "Links":
                    print("Found Oem Links extension for the %s resource" %(schema))
                    key_name = "%s_%s_Oem" %(schema, prop)
                    new_json_data = {
                                        "additionalProperties": False,
                                        "description": "The OEM Links extension to the %s resource." %(schema),
                                        "longDescription": "This object represents the OEM properties. The resource values shall comply with the Redfish Specification-described requirements.",
                                        "patternProperties": {
                                            "^([a-zA-Z_][a-zA-Z0-9_]*)?@(odata|Redfish|Message)\\\\.[a-zA-Z_][a-zA-Z0-9_]*$": {
                                                "description": "This property shall specify a valid odata or Redfish property.",
                                                "type": [
                                                    "array",
                                                    "boolean",
                                                    "integer",
                                                    "number",
                                                    "null",
                                                    "object",
                                                    "string"
                                                ]
                                            }
                                        },
                                        "properties": {},
                                        "type": "object"
                                    }
                    for oem, oem_desc in binding.items():
                        for oem_name, oem_binding in oem_desc.items():
                            new_json_data["properties"][oem_name] = {
                                                    "$ref": oem_binding["$ref"],
                                                    "description": "An Oem extension to the %s resource." %(schema),
                                                    "longDescription": "An Oem extension to the %s resource." %(schema)
                                                }
                    # Now Open the Json file and write it
                    file_pat = "%s.v" %schema
                    for fname in sorted(os.listdir(self.json_out_file_path)):
                        try:
                            if fname.startswith(file_pat):
                                print("Extending %s with Oem %s" %(fname, key_name))
                                in_schema_path = os.path.join(self.json_out_file_path, fname)
                                out_schema_path = os.path.join(self.json_out_file_path, fname)
                                with open(in_schema_path, "r") as fd:
                                    jsonschema = json.load(fd)
                                jsonschema["definitions"][key_name] = new_json_data
                                jsonschema["definitions"]["Links"]["properties"]["Oem"]["$ref"] = "#/definitions/%s" %(key_name)

                                with open(out_schema_path, "w") as fd:
                                    json.dump(jsonschema, fd, indent = 4, sort_keys=True, separators=(',', ': '))
                        except Exception as e:
                            print("Unable to extend %s with Oem %s: Exception (%s)" %(fname, key_name, e))
                else:
                    # Generic, traverse down the properties in the schema
                    # TODO: This logic below should be able to take care of all the if-elif cases above
                    print("Found generic Oem extension(s) for the %s resource" %(schema))
                    schema_cache = {} # Use a cache to batch all the schema changes in one shot
                    file_pat = "%s.v" %schema
                    key_name = "%s_%s_Oem" %(schema, prop)
                    paths = get_paths(binding, [prop])
                    for key_path_list in paths:
                        next_key_oem_name = False
                        next_key_ref = False
                        oem_name = None
                        oem_ref = None
                        keys_to_oem = []
                        x = schema_bindings
                        for k in key_path_list:
                            if k == "Oem":
                                next_key_oem_name = True
                            elif next_key_oem_name == True:
                                oem_name = k
                                next_key_oem_name = False
                                next_key_ref = True
                            elif next_key_ref == True:
                                assert(k == "$ref"), "Invalid Binding Format! Expecting $ref!"
                                assert(type(x[k]) == str), "Invalid Binding Format! $ref should be a string!"
                                oem_ref = x[k]
                                break
                            else:
                                keys_to_oem.append(k)
                            x = x[k]
                        key_name = "%s_%s_Oem" %(schema,"_".join(keys_to_oem))
                        for fname in sorted(os.listdir(self.json_out_file_path)):
                            try:
                                if fname.startswith(file_pat):
                                    print("Extending %s with Oem %s" %(fname, key_name))
                                    in_schema_path = os.path.join(self.json_out_file_path, fname)
                                    out_schema_path = os.path.join(self.json_out_file_path, fname)
                                    json_schema = schema_cache.get(in_schema_path)
                                    if json_schema == None:
                                        json_schema = JsonSchemaConfigHelper(in_schema_path, out_schema_path)
                                        schema_cache[in_schema_path] = json_schema
                                    _prop_d = None
                                    referenced_type_to_modify = None
                                    parent_prop_d = None # Initial None will indicate it is a property in the root
                                    for p in keys_to_oem:
                                        # print("Processing: {} of #/{}".format(p, "/".join(keys_to_oem)))
                                        ref = json_schema.get_type_ref_of_property(p, parent_prop_d)
                                        assert(ref.startswith("#/")), "{} property must be a local reference".format(p)
                                        ref_type = ref.rsplit("/",1)[-1]
                                        referenced_type_to_modify = ref_type
                                        parent_prop_d = json_schema.get_definition(ref_type)
                                    json_schema.add_oem_schema_link(referenced_type_to_modify, oem_name, oem_ref)
                            except Exception as e:
                                print("Unable to extend %s with Oem %s: Exception (%s)" %(fname, key_name, e))
                                raise(e)
                    #raise(Exception("Not Yet Implemented!!"))

    def inject_annotations(self):
        def load_supported_annotations():
            annotation_file = os.path.join(self.json_out_file_path, "redfish-payload-annotations-v1.json")
            supported_annotations = {}
            with open(annotation_file, "r") as fd:
                data = json.load(fd)
            supported_annotations["properties"] = data["properties"]
            supported_annotations["patternProperties"] = data["patternProperties"]
            supported_annotations["patternRegexes"] = {}
            for pattern in data["patternProperties"]:
                pat_key = "@" + pattern.split("@",1)[-1][:-1] # Example: ^([a-zA-Z_][a-zA-Z0-9_]*)?@Redfish.AllowableValues$
                supported_annotations["patternRegexes"][pat_key] = {"re": re.compile(pattern, re.M), "pat": pattern}
            return supported_annotations
        def get_annotation_details(supported_annotations, annotation):
            # HACK to allow "MultipartHttpPushUri@Redfish.OperationApplyTimeSupport" till schema is fixed
            if "@Redfish.OperationApplyTimeSupport" in annotation:
                annotation = "@Redfish.OperationApplyTimeSupport"
            # End of HACK
            if annotation in supported_annotations["properties"]:
                return supported_annotations["properties"][annotation]
            for pat_key in supported_annotations["patternRegexes"]:
                if pat_key not in annotation:
                    continue
                if supported_annotations["patternRegexes"][pat_key]["re"].match(annotation):
                    return supported_annotations["patternProperties"][supported_annotations["patternRegexes"][pat_key]["pat"]]
            print(f"Unable to find annotation {annotation} in supported annotations")
            return None
        if not self.__annotations:
            return
        supported_annotations = load_supported_annotations()
        json_schema_files_map = {} # Prefix  based map for faster lookup: ServiceRoot.v -> [ServiceRoot.v1_1_0.json, ServiceRoot.v1_2_0.json]
        for f in sorted(os.listdir(self.json_out_file_path)):
            if not f.endswith(".json") or ".v" not in f:
                continue
            schema_name = f.split(".v")[0]
            k = schema_name+".v"
            if schema_name not in json_schema_files_map:
                json_schema_files_map[k] = []
            json_schema_files_map[k].append(os.path.join(self.json_out_file_path, f))
        for schema_name, annotation_details in self.__annotations.items():
            schema_key = schema_name + ".v"
            if schema_key not in json_schema_files_map:
                continue
            for f in json_schema_files_map[schema_key]:
                json_schema = JsonSchemaConfigHelper(f, f)
                for target, annotation in annotation_details.items():
                    for annotation_prop in annotation:
                        annotation_details = get_annotation_details(supported_annotations, annotation_prop)
                        assert(annotation_details != None), "Unsupported Annotation: %s" %(annotation_prop)
                        json_schema.add_annotation(target, annotation_prop, annotation_details)

def main():
    """
    Main entry point for the script
    """

    # Get the input arguments
    arg_get = argparse.ArgumentParser( description = "A tool used to processes Redfish JSON Schema files and integrate any OEM definitions that are found in the configuration file." )
    arg_get.add_argument( "--input", "-I", type = str, required = True, help = "The folder containing the JSON files to convert" )
    arg_get.add_argument( "--output", "-O",  type = str, required = True, help = "The folder to write the OEM integrated JSON files" )
    arg_get.add_argument( "--config", "-C", type = str, help = "The configuration file containing various OEM bindings in JSON format" )
    args = arg_get.parse_args()

    # Create the output directory (if needed)
    if not os.path.exists( args.output ):
        os.makedirs( args.output )
    else:
        # If input and output are different directories, clean output dir
        if args.output != args.input:
            shutil.rmtree(args.output)
            os.makedirs( args.output )

    # Read the configuration file
    config_data = {}
    if args.config is not None:
        try:
            with open( args.config ) as config_file:
                config_data = json.load( config_file )
        except json.JSONDecodeError:
            print( "ERROR: {} contains a malformed JSON object".format( args.config ) )
            sys.exit( 1 )
        except:
            print( "ERROR: Could not open {}".format( args.config ) )
            sys.exit( 1 )

    # Step through each file in the input directory
    integrator = DMTFOemIntegrator(args.input, args.output, config_data)
    integrator.integrate_oems()
    integrator.inject_annotations()
    return 0

if __name__ == '__main__':
    sys.exit( main() )
