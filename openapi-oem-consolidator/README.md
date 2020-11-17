# OpenAPI OEM and Redfish Bundle Consolidator

Copyright 2020 DMTF. All rights reserved.

## About

The OpenAPI OEM and Redfish Bundle Consolidator is a tool that consolidates
a published Redfish schema bundle with an OEM's bundle into a single bundle to
compliant with OpenAPI specification.

## Requirements

This tool can run on any operating systems that has Python3 installed. The tool requires the following packages to be installed already:

  * PyYaml
  * ArgParse
  * Pprint
  * re
  * glob
  * os
  * sys

## Usage

Consult the help provided by the tool itself for exact usage syntax:

```
usage: openapi-oem-consolidator.py --help
```

### Preparation 

Before running the tool, create two directories:
 
  * Redfish Directory
  * OEM Directory

These two directories must be different and not a child directory of each other. The directory names are of your choosing.

The Redfish directory must contain the extracted DSP8010 bundle. The OEM directory will contain the OEM's files as described in [OEM Bundle Methodology](#oem-bundle-methodology)

## OEM Bundle Methodology

The OEM directory is a directory that contains two types of files:

  * Normal OEM files
  * Special OEM files

Special OEM files are identified by a file naming convention. Normal OEM files are any files not starting with a period and not having the special file naming convention defined in this document.

Normal OEM files are simply copied to the consolidated (i.e., output) directory. They are expected to be OpenAPI compliant especially if they are referenced by other other OpenAPI files.

There is no limitation to the number of files in this directory.

For an example of an OEM Bundle, look at the contents of the `Example` directory. These examples are not Redfish compliant. The example was tested against 2020.3 Redfish schema bundle.

### Special OEM Files

Special OEM files are files that describe to the tool how to modify the Redfish equivalent files to inject or replace OEM sections in standard Redfish schema. These files are populated by the OEM in an OEM directory.

The following subsections describe their respective special OEM file.

Lastly, all files in the Redfish directory and OEM directories are never modified. The specified output directory will contained the modified versions.

#### openapi.yaml

This file has the same filename as the Redfish one. The tool expects the OEM version to contain the following yaml sections:

  * `info`
  * `opeanapi`

The tool will error if the OEM's `openapi.yaml` contains a `components` section.

The tool takes the `info` section from the OEM's and replaces the `info` section in the Redfish's `openapi.yaml`. 

The tool expects that the `openapi` section specify the same version as the Redfish one. If not, it is an error.

The OEM `openapi.yaml` may contain a `paths` section. The tool just merges the `path` section from both files into one.

This file is required.

#### $(ResourceName)-OEM.yaml

`$(ResourceName)` is a name of a resource such as *ManagerAccount*, *ComputerSystem*. The tool matches `$(ResourceName)-OEM.yaml` to the equivalent unversioned Redfish resource of the name `$(ResourceName).yaml`.

To replace one or more OEM sections in an unversioned Redfish resource YAML file, create a file whose name is `$(ResourceName)-OEM.yaml` in the given OEM directory.

`$(ResourceName)-OEM.yaml` must have the same YAML path as in the Redfish `$(ResourceName).yaml`. 

Only OEM YAML paths are allowed in `$(ResourceName)-OEM.yaml`. All other paths will cause an error. See [OEM YAML Paths](#oem-yaml-paths) for details. The OEM YAML paths will replace the same path in the Redfish `$(ResourceName).yaml`. If a path in `$(ResourceName)-OEM.yaml` is not found in the Redfish equivalent, an error will occur.

#### $(ResourceName)-OEM.v$(ver).yaml

`$(ResourceName)` is a name of a resource such as *ManagerAccount*, *ComputerSystem*. `$(ver)` is the version, using underscore (_) as the version separator, such as *1_0_0*, *1_7_5*. The tool matches `$(ResourceName)-OEM.v$(ver).yaml` to the equivalent versioned Redfish resource of the name `$(ResourceName).v$(ver).yaml`.

To replace one or more OEM sections in a versioned Redfish resource YAML file, create a file whose name is `$(ResourceName)-OEM.v$(ver).yaml` in the given OEM directory.

`$(ResourceName)-OEM.v($ver).yaml` must have the same YAML path as in the Redfish `$(ResourceName).v$(ver).yaml`. 

Only OEM YAML paths are allowed in `$(ResourceName)-OEM.v($ver)yaml`. All other paths will cause an error. See [OEM YAML Paths](#oem-yaml-paths) for details. The OEM YAML paths will replace the same path in the Redfish `$(ResourceName).v$(ver).yaml`. If a path in `$(ResourceName)-OEM.v($ver).yaml` is not found in the Redfish equivalent, an error will occur.

#### $(ResourceName)-OEM.all-vers.y

`$(ResourceName)` is a name of a resource such as *ManagerAccount*, *ComputerSystem*. The tool matches `$(ResourceName)-OEM.all-vers.yaml` to **all** versioned Redfish resource of the name `$(ResourceName).v*.yaml` where the asterisks (*) serves as a wildcard.

This method allows a single OEM file to replace all OEM sections in **all** versions of the same resource.

To replace one or more OEM sections in all versions of a versioned Redfish resource YAML file, create a file whose name is `$(ResourceName)-OEM.all-vers.yaml` in the given OEM directory.

`$(ResourceName)-OEM.all-vers.yaml` must have the same YAML path as in **one** of the versions of a versions Redfish resource of the name `$(ResourceName).v$(ver).yaml`. The tool assumes the same path, ignoring the version information embedded in YAML property names, exist in all versions. If one version does not have the same path, an error will occur.

Only OEM YAML paths are allowed in `$(ResourceName)-OEM.all-vers.yaml`. All other paths will cause an error. See [OEM YAML Paths](#oem-yaml-paths) for details. The OEM YAML paths will replace the same path in each version of the versioned Redfish `$(ResourceName).v$(ver).yaml`. If a path in `$(ResourceName)-OEM.v($ver).yaml` is not found in the Redfish equivalent, an error will occur.

### OEM YAML Paths

YAML paths are YAML object hierarchy paths. OEM YAML paths are YAML paths starting at the root/top to the first occurrence of a property/key name that meets one of these conditions:

  * Property/Key name is exactly "OEM"
  * Property/Key name is exactly "Oem"
  * Property/Key name is exactly "Resource_Oem"
  * Property/Key name ends with "OemActions"

Here are examples of OEM YAML Paths:

OEM YAML Path Example 1:

```yaml
components:
  schemas:
    ComputerSystem_v1_12_0_OemActions:
```

OEM YAML Path Example 2:

```yaml
components:
  schemas:
    ManagerAccount_v1_6_1_ManagerAccount:
      properties:
        Oem:
    
```

OEM YAML Path Example 3:

```yaml
components:
  schemas:
    Resource_Oem:

```

All content under an OEM YAML path will replace the equivalent path in the equivalent Redfish resource.

## Miscellaneous

The tool strips comments in YAML files when consolidating YAML files with OEM extensions. If a Redfish resource YAML file gets combined with OEM extensions, the resulting consolidated file will not contain any comments. The contents of Normal OEM files or non-consolidated Redfish YAML files are preserved as they are simply copied to output directory.

For Special OEM files, if the equivalent file in the Redfish bundle is not found, an error will result.
