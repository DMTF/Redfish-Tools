# Redfish OEM Integrator

Copyright 2022-2024 DMTF.  All rights reserved.

## About

The Redfish OEM Integrator is a Python3 tool that processes Redfish JSON Schema files, modifies their contents to remove functionality not supported by the implementation, and integrates definitions for OEM extensions supported by the implementation.

## Requirements

Ensure that the machine running the tool has Python3 installed.

## Usage

```
usage: redfish-oem-integrator.py [-h] --input INPUT --output OUTPUT
                                 [--config CONFIG]

A tool used to processes Redfish JSON Schema files and integrate any OEM
definitions that are found in the configuration file.

required arguments:
  --input INPUT, -I INPUT
                        The folder containing the JSON files to convert
  --output OUTPUT, -O OUTPUT
                        The folder to write the OEM integrated JSON files

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -C CONFIG
                        The configuration file containing various OEM bindings
                        in JSON format
```

Example: `python3 redfish-oem-integrator.py --input <JSON-Dir> --output <JSON-Dir> --config <Config-File>`

The tool will process the JSON Schema files referenced by the *input* argument.
It will then update each JSON Schema file based on the configuration specified by the *config* argument and save the modified JSON Schema files to the directory referenced by the *output* argument.

## Config File

The config file contains the following terms to control how the tool processes JSON Schema files:

* `OemConfigurationFilePath`: The filename and path that contains the resource configurations that describe what the implementation supports.
    * It's recommended to reference a file in its own directory to ensure the descriptors are not mixed with other files, especially if `StoreConfigInSeparateFiles` contains `true`.
    * See [Resource Config](#resource-config) for more information about the contents.
* `OemBindingsFilePath`: The filename and path to the file that describes where OEM objects and actions are inserted into the implementation.
    * See [OEM Bindings Config](#oem-bindings-config) for more information about the contents.
* `StoreConfigInSeparateFiles`: `true` indicates if each resource has its own configuration file and `false` indicates if all resouce configurations are contained in a single, monolithic file.
* `EnableNewAdditionsByDefault`: When parsing the contents of the *input* directory and adding new properties not currently in the resource configuration, `true` will enable the new property in the configuration and `false` will disable the new property in the configuration.

### Resource Config

The file referenced by the `OemConfigurationFilePath` term contains the resource configurations that describe what the implementation supports.
The file contains a JSON object whose key-value pairs consist of the resource name and a JSON object that contains the configuration for that resource.
For example:

```
{
    "AccountService": {
        <AccountService configuration>
    },
    "ComputerSystem": {
        <ComputerSystem configuration>
    },
    ... <Other resources>
}
```

Each resource configuration contains descriptors for the actions, capabilities, and properties found in the resource.
For example:

```
{
  "actions": {
    "#Resource.Action1": {
      "input_parameters": {
        "Parameter1": {
          "@meta.Enabled": false
        }
      },
      "output_parameters": {}
    },
    "#Resource.Action2": {
      "input_parameters": {},
      "output_parameters": {}
    }
  },
  "capabilities": {
    "deletable": {
      "dmtf": false
    },
    "insertable": {
      "dmtf": false
    },
    "updatable": {
      "@meta.oem": true,
      "dmtf": true
    }
  },
  "properties": {
    "Property1": {
      "@meta.Enabled": false
    },
    "Property2": {
      "@meta.Enabled": false
    },
    "Property3": {
      "@meta.AllowWrite": true,
      "@meta.Enabled": true
    },
    "Property4": {
      "@meta.AllowWrite": false,
      "@meta.Enabled": true
    },
    "Property5": {
      "@meta.Enabled": true
    }
  }
}
```

Inside the `actions` and `properties` definitions:

* `@meta.Enabled` specifies if the implementation supports the action, parameter, or property.  Setting it to `false` will remove the corresponding JSON Schema definition from the output JSON Schema file.
* `@meta.AllowWrite` specifies if the implementation supports modifications of the property.  Setting it to `false` will mark the property as read-only in output JSON Schema file.

Inside the `capabilities` definitions:

* `dmtf` specifies if the resource is deletable (supports `DELETE`), insertable (supports `POST`), and updatable (supports `PATCH` or `PUT`).

When `StoreConfigInSeparateFiles` contains `true`, each resource object in the file contains a `$ref` statement to reference the file containing the resource configuration.

### OEM Bindings Config

The file referenced by the `OemBindingsFilePath` term contains a JSON object that describes how different OEM object and action definitions are inserted into the JSON Schema output.
For example:

```
{
    "ServiceRoot": {
        "Oem": {
            "Contoso": {
                "$ref": "http://Contoso.com/schemas/ContosoServiceRoot.json#/definitions/ContosoServiceRoot"
            }
        }
    },
    "AccountService": {
        "OemActions": {
            "#ContosoAccountService.AutoConfig": {
                "$ref": "http://Contoso.com/schemas/ContosoAccountService.json#/definitions/AutoConfig"
            }
        }
    }
}
```

## Guides

Constructing the [resource configurations](#resource-config) is not necessary.
The tool contains intelligence to build a default configuration for all resources based on the contents of the *input* directory containing all of the JSON Schema files to convert.
The tool also automatically updates the resource configurations if the *input* directory contains newer schema files.

### Running for the First Time

When running for the first time, ensure the directory and file referenced by the `OemConfigurationFilePath` does not exist.
Let the tool run once with the desired JSON Schema files to convert.
When the tool completes, open the [resource configuration files](#resource-config) and modify their contents to enable/disable properties, actions, action parameters, and resource capabilities.
Run the tool again; the *output* directory will contain the modified JSON Schema files per their respective resource configurations.

### Running Again with New JSON Schema Files

Let the tool run once with the desired JSON Schema files to convert.
When the tool completes, open the [resource configuration files](#resource-config) for new or updated resource and modify their contents to enable/disable the new properties, actions, action parameters, and resource capabilities.
Run the tool again; the *output* directory will contain the modified JSON Schema files per their respective resource configurations.
