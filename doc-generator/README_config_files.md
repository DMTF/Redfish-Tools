[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="https://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

# Redfish doc generator configuration and supplemental files

You define configuration keys in the [base configuration file](#base-configuration-file).

This file can include pointers to:

* The optional [content supplement configuration file](#content-supplement-configuration-file), which also contains configuration keys.
* The [boilerplate intro](#boilerplate-intro-file) and the [boilerplate postscript](#boilerplate-postscript-file) supplemental files, which contain supplemental content.

## Base configuration file

* [Base configuration file overview](#base-configuration-file-overview)
* [Base configuration file keys](#base-configuration-file-keys)
* [Example base configuration files and command-line invocations](#example-base-configuration-files-and-command-line-invocations)

### Base configuration file overview

The base configuration file is a JSON file that configures the generated documentation and can include pointers to the content supplement configuration file and the boilerplate intro and boilerplate postscript supplemental files.

To include supplemental files and the content supplement configuration file, add pointers to these files at the bottom of the base configuration file:

```json
{
   ...
   "boilerplate_intro": "./intro.md",
   "boilerplate_postscript": "./postscript.md", 
   "content_supplement": "./content_supplement.json"
}
```

If the base configuration file points to the:

| File                             | The doc generator                 |
| :------------------------------- | :-------------------------------- |
| Content supplement configuration | Reads configuration keys from the file. |
| Boilerplate intro                | Includes content from the file before the generated documentation. |
| Boilerplate postscript           | Includes content from the file after the generated documentation. |

Depending on the [output format and mode](README.md#output-formats-and-modes "README.md#output-formats-and-modes"), the configuration keys in the base configuration file can change. Therefore, [several flavors of the base configuration file](#example-base-configuration-files-and-command-line-invocations "#example-base-configuration-files-and-command-line-invocations") are available.

To specify the path to the base configuration file, use the [--config](#usage "#usage") command‑line argument.

### Base configuration file keys

The `uri_mapping` configuration key is required but all other configuration keys are optional. Because you can only specify the required `uri_mapping` key in the base configuration file, the `--config` command-line argument is required but all other command-line arguments are optional.

For a mapping of configuration keys to command-line arguments, see [Mapping of command-line-arguments to configuration keys](README.md#table-mapping-of-command-line-arguments-to-configuration-keys "README.md#table-mapping-of-command-line-arguments-to-configuration-keys").

* [actions_in_property_table](#actions_in_property_table)
* [add_toc](#add_toc)
* [boilerplate_intro](#boilerplate_intro)
* [boilerplate_postscript](#boilerplate_postscript)
* [combine_multiple_refs](#combine_multiple_refs)
* [content_supplement](#content_supplement)
* [description](#description)
* [description_overrides](#description_overrides)
* [escape_chars](#escape_chars)
* [excluded_annotations](#excluded_annotations)
* [excluded_pattern_properties](#excluded_pattern_properties)
* [excluded_properties](#excluded_properties)
* [excluded_schemas](#excluded_schemas)
* [format](#format)
* [html_title](#html_title)
* [import_from](#import_from)
* [locale](#locale)
* [normative](#normative)
* [object_reference_disposition](#object_reference_disposition)
* [omit_version_in_headers](#omit_version_in_headers)
* [outfile](#outfile)
* [payload_dir](#payload_dir)
* [profile_doc](#profile_doc)
* [profile_terse](#profile_terse)
* [profile_uri_to_local](#profile_uri_to_local)
* [property_index](#property_index)
* [property_index_config_out](#property_index_config_out)
* [registry_uri_to_local](#registry_uri_to_local)
* [subset_doc](#subset_doc)
* [suppress_version_history](#suppress_version_history)
* [uri_mapping](#uri_mapping)
* [version](#version)

#### actions_in_property_table

String. Indicates whether to include **Actions** in property tables:

* `true`. (Default) Include **Actions** in property tables.
* `false`. Exclude **Actions** from property tables.
   
#### add_toc

String. Indicates whether to generate a table of contents (TOC):

* `true`. (Default) Generate a TOC and place it either at the beginning of the generated HTML file or in the `[add_toc]` location if that directive appears in the boilerplate intro or boilerplate postscript file.
    
    By default, the table of contents (TOC) appears at the top of the HTML file. If the `[add_toc]` directive appears anywhere in the boilerplate intro or boilerplate postscript file, `add_toc` key is `true` by default.
    
* `false`. Do not generate a TOC.
   
#### boilerplate_intro

String. Defines the location of the HTML or Markdown file that contains the content to appear at the beginning of the document before the generated schema documentation. A relative path is relative to the location of the configuration file.

#### boilerplate_postscript

String. Defines the location of the HTML or Markdown file that contains the content to appear at the end of the document after the generated schema documentation. A relative path is relative to the location of the configuration file.

#### combine_multiple_refs

Integer. Indicates whether, and at what threshold, to move references to the same object into **Property details** with a single-row listing for each object in the main table rather than expand in place:

* Absent or `0`. No combining occurs. Default is `0`.
* `1`. Does not make sense. Not valid.
* `2` or greater. Defines the number of references to the same object to combine and place into the **Property details** clause.

This example moves a referenced object to **Property details** when it is referred to three or more times:

```json
"combine_multiple_refs": 3
```

#### content_supplement

String. Defines the location of the [content supplement configuration file](#content-supplement-configuration-file "#content-supplement-configuration-file"), which is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. A relative path is relative to the location of the configuration file.

#### description

String. Provides the description for the base configuration file.

#### description_overrides

Object. Overrides descriptions for individual properties. Values are lists, which enable different overrides for the same property in different schemas. Each object in the list can have the following entries:

* `type`. Property type.
* `schemas`. List of schemas to which this element applies.
* `globalOverride`. Overrides the description for all instances of the property with the `overrideDescription`.
* `description`. Description in the schema.[<sup>**\[1\]**</sup>](#footnote1 "#footnote1")
* `knownException`. A variant description is expected.[<sup>**\[1\]**</sup>](#footnote1 "#footnote1")

<a id="footnote1"></a><sup>**\[1\]**</sup> The `description` and `knownException` keys are primarily for your own reference. When generating configuration output, the doc generator includes the description and sets `knownException` to `false`. You can edit the output to distinguish expected exceptions from those that need attention. Neither field affects the property index document itself.

> **Note:** Although `description_overrides` has a similar function to `property_description_overrides` in other output modes, it has a different structure.

* The following example changes the descriptions for all `EventType` property instances that have the `string` type to `"The type of an event recorded in this log."`:
    
    ```json
    "EventType": [{
     "overrideDescription": "The type of an event recorded in this log.",
     "globalOverride": true,
     "type": "string"
    }]
    ```

* The following example provides override descriptions for instances of `FirmwareVersion`:
    
    ```json
    "FirmwareVersion": [{
     "description": "Firmware version.",
     "type": "string",
     "knownException": true,
     "overrideDescription": "Override text for FirmwareVersion",
     "schemas": [
        "AttributeRegistry/SupportedSystems"
     ]
    }, {
     "overrideDescription": "The firmware version of this thingamajig.",
     "type": "string",
     "knownException": true,
     "schemas": ["Power/PowerSupplies",
        "Manager",
        "ComputerSystem/TrustedModules",
        "Storage/StorageControllers"
     ]
    }, {
     "description": "The version of firmware for this PCIe device.",
     "type": "string",
     "knownException": true,
     "schemas": ["PCIeDevice"]
    }]
    ```
    
    In the example:
    
    * The first entry provides an override description for `FirmwareVersion` instances with the `Firmware version` description and the `string` type in the listed schemas.
    * The second entry provides an override description for `FirmwareVersion` instances with the `string` type in the listed schemas.
    * The third entry identifies a `FirmwareVersion` instance with the `The version of firmware for this PCIe device.` description and the `string` type, but does not provide an override description.

#### escape_chars

Array of strings. Defines the one or more character to escape in the generated Markdown. For example, you can escape the `@` character if your Markdown processor converts strings with embedded `@` characters to `mailto` links. Default is `[]`.

#### excluded_annotations

Array of strings. Defines one or more annotation names to exclude from the generated documentation. For example, The `*` character at the beginning of a string is the wildcard character. Default is `[]`.

#### excluded_pattern_properties

Array of strings. Defines a list of pattern properties to exclude from the generated documentation. In JSON, you must escape back slashes.

**Example**: `"\"` becomes `"\\"`.

#### excluded_properties

Array of strings. Defines property names to exclude from the generated documentation. The `*` character at the beginning of a string is the wildcard character.

`"*odata.count"` matches `"Members\@odata.count"` and others.

The following example omits any property name that ends with `"@odata.count"`:

```json
"excluded_properties": ["description", "Id", "@odata.context", "@odata.type",
   "@odata.id", "@odata.etag", "*@odata.count"
]
```

Default is `[]`.

#### excluded_schemas

Array of strings. Defines schema to exclude from the generated documentation.

#### format

String. Defines the format of the generated documentation:

<table id="table-1--output-formats">
   <caption><b>Table 1 &mdash; Output formats</b></caption>
   <thead>
      <tr>
         <th align="left" valign="top">Output&nbsp;format</th>
         <th align="left" valign="top">Description</th>
      </tr>
   </thead>
   <tbody>
      <tr id="markdown-format">
         <td align="left" valign="top"><code>markdown</code></td>
         <td align="left" valign="top">Markdown file targeted for the DMTF document publication process.</td>
      </tr>
      <tr id="slate-markdown-format">
         <td align="left" valign="top"><code>slate</code></td>
         <td align="left" valign="top">(Default) GitHub-flavored Markdown file targeted for the <a href="https://github.com/slatedocs/slate" title="https://github.com/slatedocs/slate">Slate API doc generator</a>. For Slate, place the <code>index.html.md</code> file in your Slate repository's source directory.</td>
      </tr>
      <tr id="html-format">
         <td align="left" valign="top"><code>html</code></td>
         <td align="left" valign="top">HyperText Markup Language (HTML) file.</td>
      </tr>
      <tr id="csv-format-1">
         <td align="left" valign="top"><code>csv</code></td>
         <td align="left" valign="top">Comma-separated values (CSV) file.</td>
      </tr>
   </tbody>
</table>

#### html_title

String. Defines the HTML `title` element in the generated HTML file.

#### import_from

String. Defines the file name or directory with the JSON schemas to process. Wild cards are acceptable. Default is \`json-schema\`.

#### locale 

Defines the case-sensitive locale code for localized output. The doc generator uses `gettext` to localize strings. Locale files are placed in the `locale` directory in the `doc-generator` root. Localized JSON schema files can contain translated descriptions and annotations.

#### normative

String. Indicates whether to generate normative, or developer-focused, documentation:

* `true`. Generate normative documentation.
* `false`. (Default) Do not generate normative documentation.

#### object_reference_disposition

Object. Defines a data structure that specifies properties to move to the **Common objects** clause and/or objects that should be included in-line where they are referenced, to override default behavior.

This object includes either or both these fields:

* `common_object`. List of property names. For example `"Redundancy"`.
* `include`. List of properties by their full path.

**Example:**

```json
"object_reference_disposition": {
   "common_object": ["Redundancy"],
   "include": [
      "http://redfish.dmtf.org/schemas/v1/PCIeDevice.json#/definitions/PCIeInterface"
   ]
}
```

#### omit_version_in_headers

Boolean. Indicates whether to omit schema versions from clause headings. Value is:

* `true`. Omit schema versions from clause headings.
* `false`. (Default) Show schema versions in clause headings.

#### outfile

String. Defines the generated file. The output format determines the default generated file:

* The `markdown` format generates `output.md`.
* The `html` format generates `index.html`.
* The `csv` format generates `output.csv`.

#### payload_dir

String. Defines the directory location for JSON payload and **Action** examples. Optional.

A relative path is relative to the working directory in which the `doc_generator.py` tool is run. Within the payload directory, use the following naming scheme for example files:

* <code translate="no"><var>SCHEMA-NAME</var>&#8209;v<var>MAJOR-VERSION</var>&#8209;example.json</code> for JSON payload.
* <code translate="no"><var>SCHEMA-NAME</var>&#8209;v<var>MAJOR-VERSION</var>&#8209;action&#8209;<var>ACTION-NAME</var>.json</code> for action examples.

#### profile_doc

String. Defines the path to a JSON profile document for profile documentation. Default is none.

#### profile_terse

String. Indicates whether to generate _terse_ profile documentation for service developers. Includes only the subset of properties with profile requirements. Meaningful only in profile mode when a profile document is also specified.

Value is:

* `true`. Generates _terse_ profile documentation.
* `false`. (Default) Generates verbose profile documentation. Includes all properties regardless of profile requirements.

#### profile_uri_to_local

Object. For profile mode only, defines an object like <code>uri_mapping</code> for locations of profiles. Default is `{}`.

#### property_index

String. Generates *property-index mode* documentation.

#### property_index_config_out

String. Generates updated property index configuration file, with the specified file name. property-index mode only.

#### registry_uri_to_local

Object. For profile mode only, defines an object like `uri_mapping` for locations of registries. Default is `{}`.

#### subset_doc

String. Defines the path to a JSON profile document for schema subset documentation. Default is none.

#### suppress_version_history

Boolean. Indicates whether to suppress the version history.

Value is:

* `true`. (Default) Suppresses the version history.
* `false`. Does not suppress the version history.
   
#### uri_mapping

Object. Defines partial URL of schema repositories as attributes, and local directory paths as values. This object maps partial URIs, as found in the schemas, to local directories. The partial URI includes the domain part of the URI but can omit the `http://` or `https://` protocol:

```json
"uri_mapping": {
   "redfish.dmtf.org/schemas/v1": "./json-schema"
}
```
   
#### version

String. Defines an optional version string, which might be meaningful in the future.

### Example base configuration files and command-line invocations

These examples make the following assumptions:

* The `DMTF/Redfish` and the `DMTF/Redfish-Tools` clones are in the same parent directory.
* The working directory is the `DMTF/Redfish` clone.
* The schemas are in `./json-schema`.
* The `doc_generator.py` is at `../Redfish-Tools/doc-generator/doc_generator.py` relative to your current working directory.

These examples show the various flavors of the base configuration file and the corresponding command&#8209;line invocations:

* [CSV format](#csv-format)
* [Terse profile mode in Markdown format](#terse-profile-mode-in-markdown-format)
* [property-index mode in HTML format](#property-index-mode-in-html-format)
* [Schema subset mode in HTML format](#schema-subset-mode-in-html-format)
* [Standard mode in HTML format](#standard-mode-in-html-format)
* [Standard normative mode in HTML format](#standard-normative-mode-in-html-format)

#### CSV format 

**Sample file:** <a href="sample_inputs/csv/config.json#L1" title="sample_inputs/csv/config.json#L1">sample_inputs/csv/config.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

This example generates <a href="README.md#csv-format" title="README.md#csv-format">CSV format</a> documentation:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/csv/config.json
```

#### Terse profile mode in Markdown format

**Sample file:** <a href="sample_inputs/profile_mode/config.json#L1" title="sample_inputs/profile_mode/config.json#L1">sample_inputs/profile_mode/config.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

**Referenced files:** <code>OCPBasicServer.v1_0_0.json</code> profile and <code>OCPManagedDevice.v1_0_0.json</code>

This example generates <a href="README.md#profile-mode" title="README.md#profile-mode">profile mode</a> documentation:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/profile_mode/config.json
```

#### property-index mode in HTML format

**Sample file:** <a href="sample_inputs/property_index/config.json#L1" title="sample_inputs/property_index/config.json#L1">sample_inputs/property_index/config.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

You can include other configuration keys for your own reference but the doc generator ignores these keys.

This example generates <a href="README.md#property-index-mode" title="README.md#property-index-mode">property-index mode</a> documentation:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/property_index/config.json
```

<blockquote><b>Note:</b> The base configuration file for property index documentation includes the <code>description_overrides</code> key, which is specific to that mode.</blockquote>

#### Schema subset mode in HTML format

**Sample file:** <a href="sample_inputs/subset/config.json#L1" title="sample_inputs/subset/config.json#L1">sample_inputs/subset/config.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

**Referenced files:** <code>OCPBasicServer.v1_0_0.json</code> profile and <code>OCPManagedDevice.v1_0_0.json</code>

This example generates <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema&nbsp;subset mode</a> documentation. The JSON profile document defines the subset:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/subset/config.json
```

#### Standard mode in HTML format

**Sample file:** <a href="sample_inputs/standard_html/config.json#L1" title="sample_inputs/standard_html/config.json#L1">sample_inputs/standard_html/config.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

This example generates <a href="README.md#standard-mode" title="README.md#standard-mode">standard mode</a> documentation:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config.json
```

> **Note:** The `object_reference_disposition` key in this configuration file identifies specific behavior for the `Redundancy` resource and for `PCIeInterface`, defined in `PCIeDevice`.
         
#### Standard normative mode in HTML format

**Sample file:** <a href="sample_inputs/standard_html/config_normative.json#L1" title="sample_inputs/standard_html/config_normative.json#L1">sample_inputs/standard_html/config_normative.json</a>.

For the configuration keys' descriptions, see [Base configuration file keys](#base-configuration-file-keys).

This example generates <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative mode</a> documentation:

```bash
$ python3 ../Redfish-Tools/doc-generator/doc_generator.py --config=../Redfish-Tools/doc-generator/sample_inputs/standard_html/config_normative.json
```

## Content supplement configuration file

* [Content supplement configuration file overview](#content-supplement-configuration-file-overview)
* [Content supplement configuration file keys](#content-supplement-configuration-file-keys)
* [Example content supplement configuration files](#example-content-supplement-configuration-files)

### Content supplement configuration file overview

The content supplement configuration file is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. 

To include the content supplement configuration file, add a pointer to it in the [base configuration file](#base-configuration-file "#base-configuration-file"). If the pointer is a relative path, it is relative to the location of the base configuration file. To specify the path to the base configuration file, use the [`--config`](README.md#usage "README.md#usage") command-line argument. 

### Content supplement configuration file keys

The configuration keys in the content supplement configuration file do not have command&#8209;line argument equivalents.

* [description](#description-1)
* [keywords](#keywords)
* [property_description_overrides](#property_description_overrides)
* [property_fulldescription_overrides](#property_fulldescription_overrides)
* [schema_link_replacements](#schema_link_replacements)
* [schema_supplement](#schema_supplement)
* [units_translation](#units_translation)

#### description

String. Provides the description for the content supplement configuration file.

#### keywords

Dictionary. Maps Redfish keywords to values that should appear in the documentation.

#### property_description_overrides

Dictionary. Maps property names to strings that replace the descriptions of the named properties. Default is `{}`.

#### property_fulldescription_overrides

Dictionary. Maps property names to strings that replace the descriptions of the named properties. These replacements are *full* in that the doc generator omits any additional information that it normally appends, like a reference to the definition of the property in another schema. Default is `{}`.

#### schema_link_replacements

Dictionary. Maps reference URIs to replacement URIs. The match type is full or partial. Replaces one link with another link. Default is `{}`.

The dictionary structure is:

```json
"schema_link_replacements": {
   "https://somewhere.example.com/some/path/to/a/some_schema.json": {
      "full_match": true,
      "replace_with": "https://docserver.example.org/some_schema_doc.html"
   },
   "fancy": {
      "full_match": false,
      "replace_with": "https://docserver.example.org/fancy_schemas.html"
   }
}
```

In this structure:

<b id="table-2--schema_link_replacements-dictionary-structure">Table 2 &mdash; schema_link_replacements dictionary structure</b>

| Attribute      | Description                                                             |
| :------------- | :---------------------------------------------------------------------- |
| URI            | Defines the URI to replace. |
| `full_match`   | Boolean. If `true`, the match is full. Otherwise, the match is partial. |
| `replace_with` | Defines the replacement URI. |
   
#### schema_supplement

Dictionary. Maps schema names to a dictionary of structured content, including text overrides for property descriptions, replacements for unit abbreviations, schema-specific introductions, property description substitutions, and other supplementary data. All elements in this structure are optional. Default is `{}`.

The structure of this object is:

```json
"schema_supplement": {
   "SchemaName": {
      "description": "A string to replace the schema description. Plain text or markdown.",
      "mockup": "A path or URI to a mockup file.",
      "jsonpayload": "A chunk of JSON.",
      "intro": "",
      "property_description_overrides": {
         "PropertyName": "A plain-text or Markdown string.",
         "AnotherPropertyName": "A plain-text or Markdown string."
      },
      "property_fulldescription_overrides": {
         "YetAnotherPropertyName": "A plain-text or Markdown string. Removes any additional data the doc generator normally appends to the description."
      },
      "property_details": {
         "EnumPropertyName": "A plain-text or Markdown string to insert after the property description and before the table of enum details in the property information under Property Details.",
         "property_details": {
            "UUID": "\nThe UUID property contains a value that ..."
         }
      }
   }
}
```

In this structure:

<b id="table-3--schema_supplement-dictionary-structure">Table 3 &mdash; schema_supplement dictionary structure</b>

| Attribute | Description | 
| :-------- | :---------- |
| `SchemaName` | Defines the schema name as either a bare schema name or a schema name with an underscore and an appended major version. For example, `"ComputerSystem"` or `"ComputerSystem_2"`. | 
| `description` | Replaces the schema description. | 
| `mockup` | Mutually exclusive with `jsonpayload`. If you specify both attributes, `mockup` takes precedence.<blockquote><b>Note:</b> If you specify a <a href="#payload_dir" title="#payload_dir">payload_dir</a> key in the base configuration file, the payload directory takes precedence over <code>mockup</code>.</blockquote> |
| `intro` | Replaces or appends the `description` string, if provided. |
| `jsonpayload` | Mutually exclusive with `mockup`. If you specify both attributes, `mockup` takes precedence.<blockquote><b>Note:</b> If you specify a <a href="#payload_dir" title="#payload_dir">payload_dir</a> key in the base configuration file, the payload directory takes precedence over <code>jsonpayload</code>.</blockquote> |
   
#### units_translation

Dictionary. Maps Redfish schema units to units as you want them to appear in the documentation. Default is `{}`.

### Example content supplement configuration files

Several files in the `sample_inputs` directory provide content supplement configuration files that you can use when you generate different types of documentation.

These examples show the various flavors of the content supplement configuration file and the corresponding output modes:

<b id="table-4--content-supplement-configuration-file-examples">Table 4 &mdash; Content supplement configuration file examples</b>

For the configuration keys' descriptions, see [Content supplement configuration file keys](#content-supplement-configuration-file-keys)

| Sample content supplement configuration file | Output&nbsp;mode |
| :------------------------------------------- | :--------------- | 
| [sample_inputs/profile_mode/content_supplement.json](sample_inputs/profile_mode/content_supplement.json#L1 "sample_inputs/profile_mode/content_supplement.json#L1") | <a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a> |
| [sample_inputs/subset/content_supplement.json](sample_inputs/subset/content_supplement.json#L1 "sample_inputs/subset/content_supplement.json#L1") | <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a> | 
| [sample_inputs/standard_html/content_supplement.json](sample_inputs/standard_html/content_supplement.json#L1 "sample_inputs/standard_html/content_supplement.json#L1") | <a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a> | 
| [sample_inputs/standard_html/content_supplement.json](sample_inputs/standard_html/content_supplement.json#L1 "sample_inputs/standard_html/content_supplement.json#L1") | <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">Standard normative</a> | 

## Boilerplate intro file

**Sample boilerplate intro file:** [intro.md](sample_inputs/standard_html/intro.md#L1 "sample_inputs/standard_html/intro.md#L1")

The boilerplate intro file is a Markdown or HTML file that contains supplementary content to include in the output before the generated documentation.

This file can include an `[add_toc]` directive that specifies location for the table of contents.

## Boilerplate postscript file

**Sample boilerplate postscript file:** [postscript.md](sample_inputs/standard_html/postscript.md#L1 "sample_inputs/standard_html/postscript.md#L1")

The boilerplate postscript file is a Markdown or HTML file that contains supplementary content to include in the output after the generated documentation.

This file can include an `[add_toc]` directive that specifies location for the table of contents.
