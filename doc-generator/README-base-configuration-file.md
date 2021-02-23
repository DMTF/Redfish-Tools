[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

# Redfish doc generator: Base configuration file keys

## Contents

* [About](#about)
* [Configuration keys](#configuration-keys)

## About

The base configuration file is a JSON file that configures the generated documentation and can include pointers to the [content supplement configuration file](README_config_files.md#content-supplement-configuration-file "README_config_files.md#content-supplement-configuration-file") and the [boilerplate intro](README_config_files.md#boilerplate-intro-file "README_config_files.md#boilerplate-intro-file") and [boilerplate postscript](README_config_files.md#boilerplate-postscript-file "README_config_files.md#boilerplate-postscript-file") supplemental files.

Use the `--config` command-line argument to specify the base configuration file.

The names of some configuration keys differ from their command&#8209;line argument equivalents. Unless otherwise noted, the configuration key has the same meaning as its command&#8209;line argument equivalent. 

The `uri_mapping` configuration key is required but all other configuration keys are optional. Because this key is required and it can only be specified in the base configuration file, the `--config` command-line argument is required but all other arguments are optional.

See also [Configuration](README.md#configuration) and [Mapping of command-line arguments to configuration keys](README.md#mapping-of-command-line-arguments-to-configuration-keys).

## Configuration keys

* [actions_in_property_table](#actions_in_property_table)
* [add_toc](#add_toc)
* [boilerplate_intro](#boilerplate_intro)
* [boilerplate_postscript](#boilerplate_postscript)
* [combine_multiple_refs](#combine_multiple_refs)
* [content_supplement](#content_supplement)
* [description](#description)
* [description_overrides](#description_overrides)
* [excluded_annotations](#excluded_annotations)
* [excluded_pattern_properties](#excluded_pattern_properties)
* [excluded_properties](#excluded_properties)
* [excluded_schemas](#excluded_schemas)
* [format](#format)
* [html_title](#html_title)
* [import_from](#import_from)
* [normative](#normative)
* [object_reference_disposition](#object_reference_disposition)
* [outfile](#outfile)
* [payload_dir](#payload_dir)
* [profile_doc](#profile_doc)
* [profile_terse](#profile_terse)
* [profile_uri_to_local](#profile_uri_to_local)
* [property_index](#property_index)
* [registry_uri_to_local](#registry_uri_to_local)
* [subset_doc](#subset_doc)
* [suppress_version_history](#suppress_version_history)
* [uri_mapping](#uri_mapping)
* [version](#version)

<dl>
   <dt id="actions_in_property_table">
      <h3><code>actions_in_property_table</code></h3>
   </dt>
   <dd>
      <table>
         <tbody>
            <tr>
               <td align="left" valign="top"><b>Type</b></td>
               <td align="left" valign="top">String</td>
            </tr>
            <tr>
               <td align="left" valign="top"><b>Description</b></td>
               <td align="left" valign="top">
                  <p>Indicates whether to include <b>Actions</b> in property tables:</p>
                  <ul>
                     <li><code>true</code>. (Default) Include <b>Actions</b> in property tables.</li>
                     <li><code>false</code>. Exclude <b>Actions</b> from property tables.</li>
                  </ul>
               </td>
            </tr>
            <tr>
               <td align="left" valign="top"><b>Output mode</b></td>
               <td align="left" valign="top"><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>.</td>
            </tr>
            <tr>
               <td align="left" valign="top"><b>Command-line equivalent</b></td>
               <td align="left" valign="top">None.</td>
            </tr>
         </tbody>
      </table>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="add_toc">
      <h3> add_toc</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>.</dd>
         <dt>Description</dt>
         <dd>String. Indicates whether to generate a table of contents (TOC):</dd>
         <dd>
            <ul>
               <li>
                  <p><code>true</code>. (Default) Generate a TOC and place it either at the beginning of the generated HTML file or in the <code>[add_toc]</code> location if that directive appears in the boilerplate intro or boilerplate postscript file.</p>
                  <p>By default, the table of contents (TOC) appears at the top of the HTML file. If the <code>[add_toc]</code> directive appears anywhere in the boilerplate intro or boilerplate postscript file, <code>add_toc</code> key is <code>true</code> by default.</p>
               </li>
               <li>
                  <p><code>false</code>. Do not generate a TOC.</p>
               </li>
            </ul>
         </dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="boilerplate_intro">
      <h3> boilerplate_intro</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the location of the HTML or Markdown file that contains the content to appear at the beginning of the document before the generated schema documentation. If a relative path, is relative to the location of the configuration file.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="boilerplate_postscript">
      <h3> boilerplate_postscript</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the location of the HTML or Markdown file that contains the content to appear at the end of the document after the generated schema documentation. If a relative path, is relative to the location of the configuration file.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="combine_multiple_refs">
      <h3> combine_multiple_refs</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Integer. Indicates whether, and at what threshold, to move references to the same object into <b>Property details</b> with a single-row listing for each object in the main table rather than expand in place:</dd>
         <dd>
            <ul>
               <li>Absent or <code>0</code>. No combining occurs.</li>
               <li><code>1</code>. Does not make sense. Not valid.</li>
               <li><code>2</code> or greater. Defines the number of references to the same object to combine and place into the <b>Property details</b> clause.</li>
            </ul>
         </dd>
         <dt>Example</dt>
         <dd>This example moves a referenced object to <b>Property details</b> when it is referred to three or more times:</dd>
         <dd>
            <pre lang="json">"combine_multiple_refs": 3</pre>
         </dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="content_supplement">
      <h3> content_supplement</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the location of the <a href="README-content-supplement-configuration-file.md#redfish-doc-generator-content-supplement-configuration-file-keys" title="README-content-supplement-configuration-file.md#redfish-doc-generator-content-supplement-configuration-file-keys">content supplement configuration file</a>, which is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. If a relative path, is relative to the location of the base configuration file.</dd>
         <dd>No default. Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--sup</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="description">
      <h3> description</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Provides description for the <code>config.json</code> file.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="description_overrides">
      <h3> description_overrides</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#property-index-mode" title="README.md#property-index-mode">Property index</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>. </dd>
         <dt>Description</dt>
         <dd>Object. Overrides descriptions for individual properties. Values are lists, which enable different overrides for the same property in different schemas. Each object in the list can have the following entries:</dd>
         <dd>
            <ul>
               <li><code>type</code>. Property type.</li>
               <li><code>schemas</code>. List of schemas to which this element applies.</li>
               <li><code>globalOverride</code>. Overrides the description for all instances of the property with the <code>overrideDescription</code>.</li>
               <li><code>description</code>. Description in the schema.<a href="#footnote1"><sup><b>[1]</b></sup></a></li>
               <li><code>knownException</code>. A variant description is expected.<a href="#footnote1"><sup><b>[1]</b></sup></a>.</li>
            </ul>
         </dd>
         <dd>
            <p id="footnote1"><sup><b>[1]</b></sup> The <code>description</code> and <code>knownException</code> keys are primarily for your own reference. When generating configuration output, the doc generator includes the description and sets <code>knownException</code> to <code>false</code>. You can edit the output to distinguish expected exceptions from those that need attention. Neither field affects the property index document itself.</p>
         </dd>
         <dd>
            <blockquote><b>Note:</b> Although <code>description_overrides</code> has a similar function to <code>property_description_overrides</code> in other output modes, it has a different structure.</blockquote>
         </dd>
         <dt>Examples</dt>
         <dd>
         <dd>
            <ul>
               <li>
                  <p>The following example changes the descriptions for all <code>EventType</code> property instances that have the <code>string</code> type to <code>"The type of an event recorded in this log."</code>:</p>
                  <pre lang="json">"EventType": [{
       "overrideDescription": "The type of an event recorded in this log.",
       "globalOverride": true,
       "type": "string"
    }]</pre>
               </li>
               <li id="description_overrides_example">
                  <p>The following example provides override descriptions for instances of <code>FirmwareVersion</code>:</p>
                  <pre lang="json">"FirmwareVersion": [{
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
    }]</pre>
                  <p>In the example:</p>
                  <ul>
                     <li>The first entry provides an override description for <code>FirmwareVersion</code> instances with the <code>Firmware version</code> description and the <code>string</code> type in the listed schemas.</li>
                     <li>The second entry provides an override description for <code>FirmwareVersion</code> instances with the <code>string</code> type in the listed schemas.</li>
                     <li>The third entry identifies a <code>FirmwareVersion</code> instance with the <code>The version of firmware for this PCIe device.</code> description and the <code>string</code> type, but does not provide an override description.</li>
                  </ul>
               </li>
            </ul>
         </dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="excluded_annotations">
      <h3> excluded_annotations</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Array of strings. Defines one or more annotation names to exclude from the generated documentation. For example, The <code>*</code> character at the beginning of a string is the wildcard character.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="excluded_pattern_properties">
      <h3> excluded_pattern_properties</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Array of strings. Defines a list of pattern properties to exclude from the generated documentation. In JSON, you must escape back slashes.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
         <dt>Example</dt>
         <dd><code>"\"</code> becomes <code>"\\"</code>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="excluded_properties">
      <h3> excluded_properties</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#csv-format" title="README.md#csv-format">CSV format</a>, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Array of strings. Defines property names to exclude from the generated documentation. The <code>*</code> character at the beginning of a string is the wildcard character.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
         <dt>Example</dt>
         <dd><code>"*odata.count"</code> matches <code>"Members\@odata.count"</code> and others.</dd>
         <dd>The following example omits any property name that ends with <code>"@odata.count"</code>:</dd>
         <dd>
            <pre lang="json">"excluded_properties": ["description",
   "Id", "@odata.context",
   "@odata.type", "@odata.id",
   "@odata.etag", "*@odata.count"
]</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="excluded_schemas">
      <h3> excluded_schemas</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Array of strings. Defines schema to exclude from the generated documentation.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="format">
      <h3> format</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#csv-format" title="README.md#csv-format">CSV format</a>, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the format of the generated documentation:</dd>
         <dd>
            <table>
               <thead>
                  <tr>
                     <th>Format</th>
                     <th>Description</th>
                  </tr>
               </thead>
               <tbody>
                  <tr>
                     <td><code>markdown</code></td>
                     <td>Markdown file targeted for the DMTF document publication process.</td>
                  </tr>
                  <tr>
                     <td><code>slate</code></td>
                     <td>(default) GitHub-flavored Markdown file targeted for the <a href="https://github.com/slatedocs/slate" title="https://github.com/slatedocs/slate">Slate API doc generator</a>. For Slate, place the <code>index.html.md</code> file in your Slate repository's source directory.</td>
                  </tr>
                  <tr>
                     <td><code>html</code></td>
                     <td>HyperText Markup Language (HTML) file.</td>
                  </tr>
                  <tr>
                     <td><code>csv</code></td>
                     <td>Comma-separated values (CSV) file.</td>
                  </tr>
               </tbody>
            </table>
         </dd>
         <dd>Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--format</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="html_title">
      <h3> html_title</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the HTML <code>title</code> element in the generated HTML file.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="import_from">
      <h3> import_from</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd>CSV format, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, property index, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, standard normative.</dd>
         <dt>Description</dt>
         <dd>String. Defines the file name or directory with the JSON schemas to process. Wild cards are acceptable.</dd>
         <dd>Default is <code>json-schema</code>. Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>import_from</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="normative">
      <h3> normative</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">Standard normative</a></dd>
         <dt>Description</dt>
         <dd>String. Indicates whether to generate normative, or developer-focused, documentation:</dd>
         <dd>
            <ul>
               <li><code>true</code>. Generate normative documentation.</li>
               <li><code>false</code>. (Default) Do not generate normative documentation.</li>
            </ul>
         </dd>
         <dd>Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--normative</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="object_reference_disposition">
      <h3> object_reference_disposition</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Object. Defines a data structure that specifies properties to move to the <b>Common objects</b> clause and/or objects that should be included in-line where they are referenced, to override default behavior.</dd>
         <dd>
            <p>This object includes either or both these fields:</p>
            <ul>
               <li><code>common_object</code>. List of property names. For example <code>"Redundancy"</code>.</li>
               <li><code>include</code>. List of properties by their full path.</li>
            </ul>
         </dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
         <dd><b>Example:</b>
            <pre lang="json">"object_reference_disposition": {
   "common_object": ["Redundancy"],
   "include": [
      "http://redfish.dmtf.org/schemas/v1/PCIeDevice.json#/definitions/PCIeInterface"
   ]
}</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="outfile">
      <h3> outfile</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#csv-format" title="README.md#csv-format">CSV format</a>, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the generated file. The output format determines the default generated file:</dd>
         <dd>
            <ul>
               <li>The <code>markdown</code> format generates <code>output.md</code>.</li>
               <li>The <code>html</code> format generates <code>index.html</code>.</li>
               <li>The <code>csv</code> format generates <code>output.csv</code>.</li>
            </ul>
         </dd>
         <dd>Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--out</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="payload_dir">
      <h3> payload_dir</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#standard-mode" title="README.md#standard-mode">Standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines the directory location for JSON payload and <b>Action</b> examples. Optional.</dd>
         <dd>If relative, is relative to the working directory in which the <code>doc_generator.py</code> script is run. Within the payload directory, use the following naming scheme for example files:</dd>
         <dd>
            <ul>
               <li><code>&lt;schema_name&gt;-v&lt;major_version&gt;-example.json</code> for JSON payload.</li>
               <li><code>&lt;schema_name&gt;-v&lt;major_version&gt;-action-&lt;action_name&gt;.json</code> for action examples.</li>
            </ul>
         </dd>
         <dd>No default. Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--payload_dir</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="profile_doc">
      <h3> profile_doc</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a></dd>
         <dt>Description</dt>
         <dd>String. Defines the path to a JSON profile document for profile documentation.</dd>
         <dd>No default. Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--profile</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="profile_terse">
      <h3> profile_terse</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a></dd>
         <dt>Description</dt>
         <dd>String. Indicates whether to generate <i>terse</i> profile documentation for service developers. Includes only the subset of properties with profile requirements. Meaningful only in profile mode when a profile document is also specified.</dd>
         <dd>
            <p>Value is:</p>
            <ul>
               <li><code>true</code>. Generates <i>terse</i> profile documentation.</li>
               <li><code>false</code>. (Default) Generates verbose profile documentation. Includes all properties regardless of profile requirements.</li>
            </ul>
         </dd>
         <dd>Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--terse</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="profile_uri_to_local">
      <h3> profile_uri_to_local</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>. </dd>
         <dt>Description</dt>
         <dd>Array of strings. For profile mode only, defines an object like <code>uri_mapping</code> for locations of profiles.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="property_index">
      <h3> property_index</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#property-index-mode" title="README.md#property-index-mode">Property index</a></dd>
         <dt>Description</dt>
         <dd>String. Generates <i>property index mode</i> documentation.</dd>
         <dd>No default.</dd>
         <dd>Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--property_index</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="registry_uri_to_local">
      <h3> registry_uri_to_local</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output mode</dt>
         <dd><a href="README.md#profile-mode" title="README.md#profile-mode">Profile</a>.</dd>
         <dt>Description</dt>
         <dd>String. For profile mode only, defines an object like <code>uri_mapping</code> for locations of registries.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="subset_doc">
      <h3> subset_doc</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a></dd>
         <dt>Description</dt>
         <dd>String. Defines the path to the JSON profile document that defines the schema subset that is used to generate schema&nbsp;subset documentation.</dd>
         <dd>No default. Command-line equivalent is <a href="README.md#usage" title="README.md#usage"><code>--subset</code></a>.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="suppress_version_history">
      <h3> suppress_version_history</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">Schema subset</a></dd>
         <dt>Description</dt>
         <dd>Boolean. Indicates whether to suppress the version history.</dd>
         <dd>
            <p>Value is:</p>
            <ul>
               <li><code>true</code>. (Default) Suppresses the version history.</li>
               <li><code>false</code>. Does not suppress the version history.</li>
            </ul>
         </dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="uri_mapping">
      <h3> uri_mapping</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#csv-format" title="README.md#csv-format">CSV format</a>, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>Object. Defines partial URL of schema repositories as attributes, and local directory paths as values.</dd>
         <dd>This object maps partial URIs, as found in the schemas, to local directories.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
         <dt>Example</dt>
         <dd>The partial URI should include the domain part of the URI but can omit the protocol (<code>http://</code> or <code>https://</code>).</dd>
         <dd>
            <pre lang="json">"uri_mapping": {
   "redfish.dmtf.org/schemas/v1": "./json-schema"
}</pre>
         </dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
   <dt id="version">
      <h3> version</h3>
   </dt>
   <dd>
      <dl>
         <dt>Output modes</dt>
         <dd><a href="README.md#csv-format" title="README.md#csv-format">CSV format</a>, <a href="README.md#profile-mode" title="README.md#profile-mode">profile</a>, <a href="README.md#property-index-mode" title="README.md#property-index-mode">property index</a>, <a href="README.md#schema-subset-mode" title="README.md#schema-subset-mode">schema subset</a>, <a href="README.md#standard-mode" title="README.md#standard-mode">standard</a>, <a href="README.md#standard-normative-mode" title="README.md#standard-normative-mode">standard normative</a>. </dd>
         <dt>Description</dt>
         <dd>String. Defines an optional version string, which might be meaningful in the future.</dd>
         <dt>Default</dt>
         <dd>None.</dd>
         <dt>Command-line equivalent</dt>
         <dd>None.</dd>
      </dl>
   </dd>
   <dd><a href="#configuration-keys">[Configuration keys]</a></dd>
</dl>
