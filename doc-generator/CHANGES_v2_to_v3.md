[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

# Redfish doc generator v3 changes

## Contents

* [About](#about)
* [Configuration files](#configuration-files)
* [Supplemental files](#supplemental-files)

## About

The Redfish doc generator v3 accepts different inputs than those that the Redfish doc generator v2 accepted.

> **Note:** These changes are not backward compatible so use the Redfish [Doc Generator v2](https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0 "https://github.com/DMTF/Redfish-Tools/releases/tag/doc_gen_v2.0.0") to run the tool against an existing set of configuration files and supplemental files.

## Configuration files

* [Changes to the base configuration file](#changes-to-the-base-configuration-file)
* [Unchanged schema subset configuration file](#unchanged-schema-subset-configuration-file)
* [New content supplement configuration file](#new-content-supplement-configuration-file)

### Changes to the base configuration file

> **Note:** For complete information about the base configuration file, see [Base configuration file](README_config_files.md#base-configuration-file "README_config_files.md#base-configuration-file") and [Configuration keys](README-base-configuration-file.md#configuration-keys "README-base-configuration-file.md#configuration-keys").

The base configuration file is `config.json`. Use the `--config` command-line argument to specify the base configuration file.

* These configuration keys have been moved from the base configuration file into the [new content supplement configuration file](#new-content-supplement-configuration-file):

    * <a href="README_config_files.md#property_description_overrides" title="README_config_files.md#property_description_overrides"><code>property_description_overrides</code></a>
    * <a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides"><code>property_fulldescription_overrides</code></a>
    * <a href="README_config_files.md#units_translation" title="README_config_files.md#units_translation"><code>units_translation</code></a>

* These property index mode keys, which you define in the base configuration file, have been renamed:

	| Previous name          | Current name            | Notes                                         |
	| :--------------------- | :---------------------- | :-------------------------------------------- |
	| `ExcludedProperties`   | [`excluded_properties`](README-base-configuration-file.md#excluded_properties "README-base-configuration-file.md#excluded_properties")   | As in other modes.                            |
	| `DescriptionOverrides` | [`description_overrides`](README-base-configuration-file.md#description_overrides "README-base-configuration-file.md#description_overrides") | Distinct from the `property_description_overrides` in the content supplement for other modes, and is provided in the base configuration file rather than the content supplement. |

**Example base configuration file:** <a href="sample_inputs/standard_html/config.json#L1" title="sample_inputs/standard_html/config.json#L1"><code>sample_inputs/standard_html/config.json</code></a>

### Unchanged schema subset configuration file

The schema subset configuration file, which is a version of the base configuration file, is a JSON file that defines the schema subset profile. This file is unchanged for v3.

For a description of and an example schema subset configuration file, see <a href="README-base-configuration-file.md#schema-subset-mode-in-html-format" title="README-base-configuration-file.md#schema-subset-mode-in-html-format">Schema subset mode in HTML format</a>.

### New content supplement configuration file

> **Note:** For complete information about the content supplement configuration file, see [Content supplement configuration file](README_config_files.md#content-supplement-configuration-file "README_config_files.md#content-supplement-configuration-file").

The content supplement configuration file is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. The base configuration file contains a pointer to this file.

| Configuration key | Change    |
| :---------------- | :-------- |
| <a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides"><code>property_description_overrides</code></a> | Moved from [base configuration file](#changes-to-the-base-configuration-file). |
| <a href="README_config_files.md#property_fulldescription_overrides" title="README_config_files.md#property_fulldescription_overrides"><code>property_fulldescription_overrides</code></a> | Moved from [base configuration file](#changes-to-the-base-configuration-file). |
| `schema_link_replacements` | New [`schema_link_replacements` key](README_config_files.md/#schema_link_replacements "README_config_files.md/#schema_link_replacements"). |
| <a href="README_config_files.md#units_translation" title="README_config_files.md#units_translation"><code>units_translation</code></a> | Moved from [base configuration file](#changes-to-the-base-configuration-file). |

For an example of the content supplement configuration file, see <a href="sample_inputs/standard_html/content_supplement.json#L1" title="sample_inputs/standard_html/content_supplement.json#L1"><code>sample_inputs/standard_html/content_supplement.json</code></a>.

## Supplemental files

* [Changes to the supplemental material file](#changes-to-the-supplemental-material-file)
* [New boilerplate intro file](#new-boilerplate-intro-file)
* [New boilerplate postscript file](#new-boilerplate-postscript-file)

### Changes to the supplemental material file

The *supplemental material* Markdown file, `devsupplement.md`, features are now available elsewhere:

<table>
   <thead>
      <tr>
         <th align="left" valign="top">Feature</th>
         <th align="left" valign="top">Available in</th>
         <th align="left" valign="top">Details</th>
      </tr>
   </thead>
   <tbody>
      <tr>
         <td align="left" valign="top">Introduction</td>
         <td align="left" valign="top"><a href="README_config_files.md#boilerplate-intro-file" title="README_config_files.md#boilerplate-intro-file">Boilerplate intro file</a></td>
         <td align="left" valign="top">
            <p>Use the <a href="README-base-configuration-file.md#boilerplate_intro" title="README-base-configuration-file.md#boilerplate_intro"><code>boilerplate_intro</code></a> key in the base configuration file to specify the location of the boilerplate intro file. Format of the file is unchanged.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">Postscript</td>
         <td align="left" valign="top"><a href="README_config_files.md#boilerplate-postscript-file" title="README_config_files.md#boilerplate-postscript-file">Boilerplate postscript file</a></td>
         <td align="left" valign="top">
            <p>Use the <a href="README-base-configuration-file.md#boilerplate_postscript" title="README-base-configuration-file.md#boilerplate_postscript"><code>boilerplate_postscript</code></a> key in the base configuration file to specify the location of the boilerplate postscript file. Format of the file is unchanged.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">Keyword configuration</td>
         <td align="left" valign="top"><a href="README_config_files.md#base-configuration-file">Base&nbsp;configuration file</a></td>
         <td align="left" valign="top">
            <p>Use these keys:</p>
            <ul>
               <li><a href="README-base-configuration-file.md#actions_in_property_table" title="README-base-configuration-file.md#actions_in_property_table"><code>actions_in_property_table</code></a></li>
               <li><a href="README-base-configuration-file.md#add_toc" title="README-base-configuration-file.md#add_toc"><code>add_toc</code></a></li>
               <li><a href="README-base-configuration-file.md#omit_version_in_headers" title="README-base-configuration-file.md#omit_version_in_headers"><code>omit_version_in_headers</code></a></li>
               <li><a href="README-base-configuration-file.md#suppress_version_history" title="README-base-configuration-file.md#suppress_version_history"><code>suppress_version_history</code></a></li>
            </ul>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">Description overrides</td>
         <td align="left" valign="top" rowspan="4"><a href="README_config_files.md#content-supplement-configuration-file">Content&nbsp;supplement&nbsp;configuration&nbsp;file</a></td>
         <td align="left" valign="top">
            <p>Use the <a href="README_config_files.md#property_description_overrides" title="README-configuration--and-supplemental-files.md#property_description_overrides"><code>property_description_overrides</code></a> key.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">FullDescription&nbsp;overrides</td>
         <td align="left" valign="top">
            <p>Use the <a href="README_config_files.md#property_fulldescription_overrides" title="README-configuration--and-supplemental-files.md#property_fulldescription_overrides"><code>property_fulldescription_overrides</code></a> key.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">Schema supplement</td>
         <td align="left" valign="top">
            <p>Use the <a href="README_config_files.md#schema_supplement" title="README-configuration--and-supplemental-files.md#schema_supplement"><code>schema_supplement</code></a> key.</p>
            <p>The schema supplement no longer supports JSON payloads. To define the directory location for JSON payload and action examples, use the <a href="README-base-configuration-file.md#payload_dir" title="README-base-configuration-file.md#payload_dir"><code>payload_dir</code></a> key instead.</p>
         </td>
      </tr>
      <tr>
         <td align="left" valign="top">Schema documentation</td>
         <td align="left" valign="top">
            <p>Use the <a href="README_config_files.md#schema_link_replacements" title="README-configuration--and-supplemental-files.md#schema_link_replacements"><code>schema_link_replacements</code></a> key.</p>
         </td>
      </tr>
   </tbody>
</table>

The following supplemental material features have had analogs in the base configuration file for some time:

| Feature                    | Base configuration file key    |
| :------------------------- | :----------------------------- |
| Excluded annotations       | [`excluded_annotations`](README-base-configuration-file.md#excluded_annotations "README-base-configuration-file.md#excluded_annotations") |
| Excluded patternProperties | [`excluded_pattern_properties`](README-base-configuration-file.md#excluded_pattern_properties "README-base-configuration-file.md#excluded_pattern_properties") |
| Excluded properties        | [`excluded_properties`](README-base-configuration-file.md#excluded_properties "README-base-configuration-file.md#excluded_properties") |
| Excluded schemas           | [`excluded_schemas`](README-base-configuration-file.md#excluded_schemas "README-base-configuration-file.md#excluded_schemas") |
| Profile URI mapping        | [`profile_uri_to_local`](README-base-configuration-file.md#profile_uri_to_local "README-base-configuration-file.md#profile_uri_to_local") |
| Registry URI mapping       | [`registry_uri_to_local`](README-base-configuration-file.md#registry_uri_to_local "README-base-configuration-file.md#registry_uri_to_local") |
| Schema URI mapping         | [`uri_mapping`](README-base-configuration-file.md#uri_mapping "README-base-configuration-file.md#uri_mapping") |

The `units_translation` key replaces the **Units Translation** table, which has been moved from the base configuration file to the content supplement configuration file.

| Feature            | Content supplement configuration file key |
| :----------------- | :--------------------------------------- |
| Units translation  | [`units_translation`](README_config_files.md#units_translation "README_config_files.md#units_translation") |

### New boilerplate intro file

See [Boilerplate intro file](README_config_files.md#boilerplate-intro-file "README_config_files.md#boilerplate-intro-file").

### New boilerplate postscript file

See [Boilerplate postscript file](README_config_files.md#boilerplate-postscript-file "README_config_files.md#boilerplate-postscript-file").
