[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

# Redfish doc generator: Content supplement configuration file keys

## Contents

* [About](#about)
* [Configuration keys](#configuration-keys)
* [Examples](#examples)

## About

The content supplement configuration file is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. The base configuration file contains a pointer to this file. If the pointer is a relative path, is relative to the location of the base configuration file.

Use the `--config` command-line argument to specify the base configuration file. The [base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file") can include a pointer to the content supplement configuration file.

The configuration keys in the content supplement configuration file do not have command&#8209;line argument equivalents.

## Configuration keys

* [description](#description)
* [keywords](#keywords)
* [property_description_overrides](#property_description_overrides)
* [property_fulldescription_overrides](#property_fulldescription_overrides)
* [schema_link_replacements](#schema_link_replacements)
* [schema_supplement](#schema_supplement)
* [units_translation](#units_translation)

<dl>
   <dt id="description"><h3>description</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Provides description for the <code>config.json</code> file.</dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="keywords"><h3>keywords</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps Redfish keywords to values as you want them to appear in the documentation.</dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="property_description_overrides"><h3>property_description_overrides</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a></dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps property names to strings that replace the descriptions of the named properties.</dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="property_fulldescription_overrides"><h3>property_fulldescription_overrides</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a></dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps property names to strings that replace the descriptions of the named properties. These replacements are <i>full</i> in that the doc generator omits any additional information that it normally appends, like a reference to the definition of the property in another schema.</dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="schema_link_replacements"><h3>schema_link_replacements</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a></dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps reference URIs to replacement URIs. The match type is full or partial. Replaces one link with another link. The dictionary structure is:</dd>
         <dd>
            <pre lang="json">"schema_link_replacements": {
   "https://somewhere.example.com/some/path/to/a/some_schema.json": {
      "full_match": true,
      "replace_with": "https://docserver.example.org/some_schema_doc.html"
   },
   "fancy": {
      "full_match": false,
      "replace_with": "https://docserver.example.org/fancy_schemas.html"
   }
}</pre>
         </dd>
         <dd>In this structure:</dd>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Attribute</th>
                     <th align="left" valign="top">Description</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top">URI</td>
                     <td align="left" valign="top">Defines the URI to replace.</td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>full_match</code></td>
                     <td align="left" valign="top">Boolean. If <code>true</code>, the match is full. Otherwise, the match is partial.</td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>replace_with</code></td>
                     <td align="left" valign="top">Defines the replacement URI.</td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="schema_supplement"><h3>schema_supplement</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a></dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps schema names to a dictionary of structured content, including text overrides for property descriptions, replacements for unit abbreviations, schema-specific introductions, property description substitutions, and other supplementary data. All elements in this structure are optional.</dd>
         <dd>The structure of this object is:</dd>
         <dd>
            <pre lang="json">"schema_supplement": {
   "SchemaName": {
      "description": "A string to replace the schema description. Plain text or markdown.",
      "mockup": "A path or URI to a mockup file.",
      "jsonpayload": "A chunk of JSON.",
      "intro": "",
      "property_description_overrides": {
         "PropertyName": "a string, plain text or markdown.",
         "AnotherPropertyName": "a string, plain text or markdown."
      },
      "property_fulldescription_overrides": {
         "YetAnotherPropertyName": "a string, plain text or markdown. This string will also eliminate any additional data the doc generator would normally append to the description."
      },
      "property_details": {
         "EnumPropertyName": "A string, plain text or markdown. This will be inserted after the property description and prior to the table of enum details in the property information under Property Details.",
         "property_details": {
            "UUID": "\nThe UUID property contains a value that represents the universal unique identifier number (UUID) of a system.\n\nThe UUID property is a string data type. The format of the string is the 35-character string format specified in RFC4122: \"xxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\". Each x represents a hexadecimal digit (0-f).\n\nRegarding the case of the hex values, RFC4122 specifies that the hex values should be lowercase characters. Most modern scripting languages typically also represent hex values in lowercase characters following the RFC. However, dmidecode, WMI and some Redfish implementations currently use uppercase characters for UUID on output."
         }
      }
   }
}</pre>
         </dd>
         <dd>In this structure:</dd>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th align="left" valign="top">Attribute</th>
                     <th align="left" valign="top">Description</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td align="left" valign="top"><code>SchemaName</code></td>
                     <td align="left" valign="top">
                        <p>Defines the schema name as either a bare schema name or a schema name with an underscore and an appended major version.</p>
                        <p>For example, <code>"ComputerSystem"</code> or <code>"ComputerSystem_2"</code>.</p>
                     </td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>description</code></td>
                     <td align="left" valign="top">Replaces the description of the schema.</td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>intro</code></td>
                     <td align="left" valign="top">Defines a string to replace the description or append to the <code>description</code> string, if provided.</td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>mockup</code></td>
                     <td align="left" valign="top">
                        <p>Mutually exclusive with <code>jsonpayload</code>. If you specify both attributes, <code>mockup</code> takes precedence.</p>
                        <blockquote><b>Note:</b> If you specify a <code>payload_dir</code> key in the <a href="README-base-configuration-file.md#configuration-keys" title="README-base-configuration-file.md#configuration-keys">base configuration file</a>, the payload directory takes precedence over <code>mockup</code>.</blockquote>
                     </td>
                  </tr>
                  <tr>
                     <td align="left" valign="top"><code>jsonpayload</code></td>
                     <td align="left" valign="top">
                        <p>Mutually exclusive with <code>mockup</code>. If you specify both attributes, <code>mockup</code> takes precedence.</p>
                        <blockquote><b>Note:</b> If you specify a <code>payload_dir</code> key in the <a href="README-base-configuration-file.md#configuration-keys" title="README-base-configuration-file.md#configuration-keys">base configuration file</a>, the payload directory takes precedence over <code>jsonpayload</code>.</blockquote>
                     </td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="units_translation"><h3>units_translation</h3></dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a></dd>
         <dt>Description</dt>
         <dd>Dictionary. Maps Redfish schema units to units as you want them to appear in the documentation.</dd>
         <dd>No default. No command-line equivalent.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
</dl>

## Examples

Several files in the `sample_inputs` directory provide example content supplement configuration files that you can use when you generate different types of documentation.

The following sample content supplement configuration files are associated with these output modes:

| Sample content supplement configuration file | Configuration keys | Output mode |
| :------------------------------------------- | :----------------- | :---------- | 
| [`sample_inputs/profile_mode/content_supplement.json`](sample_inputs/profile_mode/content_supplement.json#L1 "sample_inputs/profile_mode/content_supplement.json#L1") | <ul><li><a href="#units_translation">units_translation</a></li></ul> | <a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a> |
| [`sample_inputs/subset/content_supplement.json`](sample_inputs/subset/content_supplement.json#L1 "sample_inputs/subset/content_supplement.json#L1") | <ul><li><a href="#units_translation">units_translation</a></li></ul> | <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a> | 
| [`sample_inputs/standard_html/content_supplement.json`](sample_inputs/standard_html/content_supplement.json#L1 "sample_inputs/standard_html/content_supplement.json#L1") | <ul><li><a href="#description">description</a></li><li><a href="#keywords">keywords</a></li><li><a href="#property_description_overrides">property_description_overrides</a></li><li><a href="#schema_supplement">schema_supplement</a></li><li><a href="#units_translation">units_translation</a></li></ul> | <a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a> | 
| [`sample_inputs/standard_html/content_supplement.json`](sample_inputs/standard_html/content_supplement.json#L1 "sample_inputs/standard_html/content_supplement.json#L1") | <ul><li><a href="#description">description</a></li><li><a href="#keywords">keywords</a></li><li><a href="#property_description_overrides">property_description_overrides</a></li><li><a href="#schema_supplement">schema_supplement</a></li><li><a href="#units_translation">units_translation</a></li></ul> | <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">Standard normative</a> |
