# Redfish Schemas - User Documentation

This document contains details about specific properties contained within Schemas defined by the Redfish Specification.  Proper use of section headers allows for the Generator to incorporate the additional information automatically.

# Schema URI Mapping

Map schema URIs to local files. You may omit the protocol (e.g., https://) from the URI.
The doc generator will use the local files when specified and otherwise
follow the full URI, including data from remote files if possible.

## Local-repo: redfish.dmtf.org/schemas/v1 ./json-schema



# Keyword Configuration

# Introduction

# Title goes here

Text placed here will appear at the top of the output.  Document common usage, common properties excluded from the schema tables, and anything else useful...

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum

# Postscript

Text in this section is placed at the end of the document, following all of the schema sections.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum


# Excluded Properties

This section documents properties that are either common throughout the Redfish Schema, or are defined in the Resource.1.x.x or odata.4.x.x schema files.  Therefore, for clarity, they are excluded from the schema-specific tables.

## @odata.context

## @odata.id

## @odata.type

## *@odata.count

# Excluded Schemas

Schemas listed here are excluded from the output document.  This can be used to remove supporting documents while still allowing for easy bulk processing of whole schema directories.

## *Collection

Wildcard removal of anything with "Collection" in the name


# Schema Supplement

This is the schema-specific section.  2nd-level headings indicate the schema name with the major version appended (default is "_1" if not present).

## ManagerAccount_1

### Description

Description text placed before the property table under the schema name.

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum


### JSONPayload

A sample JSON payload can be included, which will land in the language-specific tab when the documentation output file is fed to the Slate documentation tool.


```json
[
  {
    "meeting_id": 1194,
    "name": "Review meeting",
    "start_time": {
      "value": 1431648000,
      "iso_8601": "2015-05-15T00:00:00Z"
    }
  },
  {
    "meeting_id": 1192,
    "name": "Status followup",
    "start_time": {
      "value": 1430956800,
      "iso_8601": "2015-05-07T00:00:00Z"
    }
  },
  {
    "meeting_id": 1199,
    "name": "Status update",
    "start_time": {
      "value": 1430872200,
      "iso_8601": "2015-05-06T00:30:00Z"
    }
  }
]
```

## Processor

### Description

### ProcessorID

3rd-level headings which match property names will add a "Property Details" section after the table (if one isn't auto-generated because of an enumeration table).

#### VendorId

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum

#### IdentificationRegisters

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

#### EffectiveFamily

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
