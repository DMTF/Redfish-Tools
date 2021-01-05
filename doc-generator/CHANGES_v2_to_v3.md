[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="https://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

# What's new in Redfish doc generator v3

The Redfish doc generator v3 accepts different inputs than those that the Redfish doc generator v2 accepted.

> **Note:** To run the doc generator against existing configuration files and supplemental files use the Redfish [Doc Generator v2](https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0 "https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0") because these changes are not backward compatible.

## Table of contents

* [Changes to the base configuration file](#changes-to-the-base-configuration-file)
* [Changes to the supplemental material file](#changes-to-the-supplemental-material-file)
* [New content supplement configuration file](#new-content-supplement-configuration-file)
* [New boilerplate intro file](#new-boilerplate-intro-file)
* [New boilerplate postscript file](#new-boilerplate-postscript-file)

## Changes to the base configuration file

> **Note:** For complete information about the base configuration file, see [Base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file").

* These configuration keys have been moved from the base configuration file into the [new content supplement configuration file](#new-content-supplement-configuration-file):

    * <a href="README_config_files.md#property_description_overrides" title="README_config_files.md#property_description_overrides">property_description_overrides</a>
    * <a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides">property_fulldescription_overrides</a>
    * <a href="README_config_files.md#units_translation" title="README_config_files.md#units_translation">units_translation</a>

* [Table 1](#table-1--renamed-property-index-mode-keys "#table-1--renamed-property-index-mode-keys") describes the renamed property-index mode keys, which you define in the base configuration file:

   <b id="table-1--renamed-property-index-mode-keys">Table 1 &mdash; Renamed property-index mode keys</b>

   | Previous name          | Current name            | Notes                                         |
	 | :--------------------- | :---------------------- | :-------------------------------------------- |
	 | `ExcludedProperties`   | [excluded_properties](README_config_files.md#excluded_properties "README_config_files.md#excluded_properties")   | Other output modes already used the `excluded_properties` key. |
	 | `DescriptionOverrides` | [description_overrides](README_config_files.md#description_overrides "README_config_files.md#description_overrides") | Distinct from the [property_description_overrides](README_config_files.md#property_description_overrides "README_config_files.md#property_description_overrides") key in the content supplement configuration file for other output modes. Provided in the base configuration file rather than the content supplement configuration file. |

For examples of the base configuration file, see [Example base configuration files and command‑line invocations](README_config_files.md#example-base-configuration-files-and-command-line-invocations "README_config_files.md#example-base-configuration-files-and-command-line-invocations").

## Changes to the supplemental material file

Previously, you defined the supplemental material features in `devsupplement.md`.

* [Table 2](#table-2--changes-to-the-supplemental-material-file "#table-2--changes-to-the-supplemental-material-file") describes the new locations of the *supplemental material* Markdown file features:

  <table id="table-2--changes-to-the-supplemental-material-file">
     <caption><b>Table 2 &mdash; Changes to the supplemental material file</b></caption>
     <thead>
        <tr>
           <th align="left" valign="top">Feature</th>
           <th align="left" valign="top">Available in</th>
           <th align="left" valign="top">Description</th>
        </tr>
     </thead>
     <tbody>
        <tr>
           <td align="left" valign="top">Introduction</td>
           <td align="left" valign="top"><a href="#new-boilerplate-intro-file" title="#new-boilerplate-intro-file">New boilerplate intro file</a></td>
           <td align="left" valign="top">
              <p>The <a href="README_config_files.md#boilerplate_intro" title="README_config_files.md#boilerplate_intro">boilerplate_intro</a> key in the base configuration file defines the location of the boilerplate intro file.</p>
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">Postscript</td>
           <td align="left" valign="top"><a href="#new-boilerplate-postscript-file" title="#new-boilerplate-postscript-file">New boilerplate postscript file</a></td>
           <td align="left" valign="top">
              <p>The <a href="README_config_files.md#boilerplate_postscript" title="README_config_files.md#boilerplate_postscript">boilerplate_postscript</a> key in the base configuration file defines the location of the boilerplate postscript file.</p>
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">Keyword configuration</td>
           <td align="left" valign="top"><a href="README_config_files.md#base-configuration-file">Base&nbsp;configuration file</a></td>
           <td align="left" valign="top">
              <p>Use the <a href="README_config_files.md#actions_in_property_table" title="README_config_files.md#actions_in_property_table">actions_in_property_table</a>, <a href="README_config_files.md#add_toc" title="README_config_files.md#add_toc">add_toc</a>, and <a href="README_config_files.md#suppress_version_history" title="README_config_files.md#suppress_version_history">suppress_version_history</a> keys.
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">Description overrides</td>
           <td align="left" valign="top" rowspan="4"><a href="#new-content-supplement-configuration-file" title="#new-content-supplement-configuration-file">New&nbsp;content&nbsp;supplement&nbsp;configuration&nbsp;file</a></td>
           <td align="left" valign="top">
              <p>Use the <a href="README_config_files.md#property_description_overrides" title="README-configuration-and-supplemental-files.md#property_description_overrides">property_description_overrides</a> key.</p>
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">FullDescription&nbsp;overrides</td>
           <td align="left" valign="top">
              <p>Use the <a href="README_config_files.md#property_fulldescription_overrides" title="README-configuration-and-supplemental-files.md#property_fulldescription_overrides">property_fulldescription_overrides</a> key.</p>
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">Schema supplement</td>
           <td align="left" valign="top">
              <p>Use the <a href="README_config_files.md#schema_supplement" title="README-configuration-and-supplemental-files.md#schema_supplement">schema_supplement</a> key.</p>
              <p>The schema supplement no longer supports JSON payloads. To define the directory location for JSON payload and action examples, use the <a href="README_config_files.md#payload_dir" title="README_config_files.md#payload_dir">payload_dir</a> key in the base configuration file instead.</p>
           </td>
        </tr>
        <tr>
           <td align="left" valign="top">Schema documentation</td>
           <td align="left" valign="top">
              <p>Use the <a href="README_config_files.md#schema_link_replacements" title="README-configuration-and-supplemental-files.md#schema_link_replacements">schema_link_replacements</a> key.</p>
           </td>
        </tr>
     </tbody>
  </table>

* [Table 3](#table-3--supplemental-material-features "#table-3--supplemental-material-features") describes the supplemental material features, which have had analogs in the base configuration file for some time:

   <b id="table-3--supplemental-material-features">Table 3 &mdash; Supplemental material features</b>

   | Feature                    | Base configuration file key    |
   | :------------------------- | :----------------------------- |
   | Excluded annotations       | [excluded_annotations](README_config_files.md#excluded_annotations "README_config_files.md#excluded_annotations") |
   | Excluded patternProperties | [excluded_pattern_properties](README_config_files.md#excluded_pattern_properties "README_config_files.md#excluded_pattern_properties") |
   | Excluded properties        | [excluded_properties](README_config_files.md#excluded_properties "README_config_files.md#excluded_properties") |
   | Excluded schemas           | [excluded_schemas](README_config_files.md#excluded_schemas "README_config_files.md#excluded_schemas") |
   | Profile URI mapping        | [profile_uri_to_local](README_config_files.md#profile_uri_to_local "README_config_files.md#profile_uri_to_local") |
   | Registry URI mapping       | [registry_uri_to_local](README_config_files.md#registry_uri_to_local "README_config_files.md#registry_uri_to_local") |
   | Schema URI mapping         | [uri_mapping](README_config_files.md#uri_mapping "README_config_files.md#uri_mapping") |

* The `units_translation` key replaces the **Units Translation** table, which has been moved from the base configuration file to the [new content supplement configuration file](#new-content-supplement-configuration-file "#new-content-supplement-configuration-file").

## New content supplement configuration file

> **Note:** For complete information about the content supplement configuration file, see [Content supplement configuration file](README_config_files.md#content-supplement-configuration-file "README_config_files.md#content-supplement-configuration-file").

The content supplement configuration file is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. The base configuration file contains a pointer to this file. [Table 4](#table-4--new-and-changed-keys-in-the-content-supplement-configuration-file "#table-4--new-and-changed-keys-in-the-content-supplement-configuration-file") describes the new and changed keys in the content supplement configuration file:

<b id="table-4--new-and-changed-keys-in-the-content-supplement-configuration-file">Table 4 &mdash; New and changed keys in the content supplement configuration file</b>

| Configuration key | Change    |
| :---------------- | :-------- |
| [keywords](README_config_files.md##keywords "README_config_files.md##keywords") | New key. |
| <a href="README_config_files.md#property_description_overrides" title="README_config_files.md#property_description_overrides">property_description_overrides</a> | Moved from the [base configuration file](#changes-to-the-base-configuration-file). |
| <a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides">property_fulldescription_overrides</a> | Moved from the [base configuration file](#changes-to-the-base-configuration-file). |
| [schema_link_replacements](README_config_files.md/#schema_link_replacements "README_config_files.md/#schema_link_replacements") | New key. |
| [schema_supplement](README_config_files.md#schema_supplement "README_config_files.md#schema_supplement") | New key. |
| <a href="README_config_files.md#units_translation" title="README_config_files.md#units_translation">units_translation</a> | Moved from the [base configuration file](#changes-to-the-base-configuration-file). |

For examples of the content supplement configuration file, see [Example content supplement configuration files](README_config_files.md#example-content-supplement-configuration-files "README_config_files.md#example-content-supplement-configuration-files").

## New boilerplate intro file

See [Boilerplate intro file](README_config_files.md#boilerplate-intro-file "README_config_files.md#boilerplate-intro-file").

## New boilerplate postscript file

See [Boilerplate postscript file](README_config_files.md#boilerplate-postscript-file "README_config_files.md#boilerplate-postscript-file").
