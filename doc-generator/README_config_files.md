[![Build Status](https://travis-ci.com/DMTF/Redfish-Tools.svg?branch=master)](https://travis-ci.com/github/DMTF/Redfish-Tools)
<p align="center">
  <img src="http://redfish.dmtf.org/sites/all/themes/dmtf2015/images/dmtf-redfish-logo.png" alt="DMTF Redfish" width=180></p>

Copyright © 2016-2021 DMTF. All rights reserved.

[[Redfish doc generator README]](README.md#redfish-doc-generator "README.md#redfish-doc-generator")

#  Redfish doc generator configuration and supplemental files

## Contents

* [About](#about)
* [Base configuration file](#base-configuration-file)
* [Content supplement configuration file](#content-supplement-configuration-file)
* [Boilerplate intro file](#boilerplate-intro-file)
* [Boilerplate postscript file](#boilerplate-postscript-file)

## About

You define configuration keys in the [base configuration file](#base-configuration-file "#base-configuration-file") and, optionally, in the content supplement configuration file. The base configuration file can include pointers to the optional [content supplement configuration file](#content-supplement-configuration-file "#content-supplement-configuration-file") and the [boilerplate intro](#boilerplate-intro-file "#boilerplate-intro-file") and [boilerplate postscript](#boilerplate-postscript-file "#boilerplate-postscript-file") supplemental files.

You can specify some configuration information through configuration keys only and not through command-line arguments. Conversely, you can specify some configuration information through command-line arguments only and not through configuration keys.

<dl>
   <dt id="base-configuration-file"><h2>Base configuration file</h2></dt>
   <dd>
      <dl>
         <dt>Description</dt>
         <dd>The base configuration file is a JSON file that configures the generated documentation and can include pointers to the <a href="#content-supplement-configuration-file" title="#content-supplement-configuration-file">content supplement configuration file</a> and the <a href="#boilerplate-intro-file" title="#boilerplate-intro-file">boilerplate intro</a> and <a href="#boilerplate-postscript-file" title="#boilerplate-postscript-file">boilerplate postscript</a> supplemental files.</dd>
         <dd>Use the <a href="README.md#usage" title="README.md#usage"><code>--config</code> command-line argument</a> to specify the base configuration file.</dd>
         <dd>Several flavors of the base configuration file are available.</dd>
         <dd>The doc generator reads configuration keys from the base configuration file. If the base configuration file includes a pointer to the <a href="#content-supplement-configuration-file">content supplement configuration file</a>, the doc generator also reads configuration keys from it.</dd>
         <dd>Additionally, if the base configuration file includes pointers to the <a href="#boilerplate-intro-file" title="#boilerplate-intro-file">boilerplate intro</a> and <a href="#boilerplate-postscript-file" title="#boilerplate-postscript-file">boilerplate postscript</a> supplemental files, the doc generator includes content from these files in the generated documentation.</dd>
         <dd>Depending on the <a href="README.md#output-modes" title="README.md#output-modes">output mode</a>, the configuration keys in the base configuration file can change.</dd>
         <dd>
            <p>To include supplemental files and the content supplement configuration file:</p>
            <ol>
               <li>Add a pointer to these files at the bottom of the base configuration file:
                  <pre lang="json">{
        ...
        "boilerplate_intro": "./intro.md",
        "boilerplate_postscript": "./postscript.md", 
        "content_supplement": "./content_supplement.json"
    }</pre>
               </li>
            </ol>
         </dd>
         <dt>More information</dt>
         <dd><a href="README-base-configuration-file.md#redfish-doc-generator-base-configuration-file-keys" title="README-base-configuration-file.md#redfish-doc-generator-base-configuration-file-keys">Redfish doc generator: Base configuration file keys</a></dd>
      </dl>
   </dd>
   <dt id="content-supplement-configuration-file"><h2>Content supplement configuration file</h2></dt>
   <dd>
      <dl>
         <dt>Description</dt>
         <dd>The content supplement configuration file is a JSON file that defines text overrides for property descriptions, replacements for unit abbreviations, and schema-specific content to apply to the generated schema documentation. The base configuration file contains a pointer to this file.</dd>
         <dt>More information</dt>
         <dd><a href="README-content-supplement-configuration-file.md#redfish-doc-generator-content-supplement-configuration-file-keys" title="README-content-supplement-configuration-file.md#redfish-doc-generator-content-supplement-configuration-file-keys">Redfish doc generator: Content supplement configuration file keys</a></dd>
      </dl>
   </dd>
   <dt id="boilerplate-intro-file"><h2>Boilerplate intro file</h2></dt>
   <dd>
      <dl>
         <dt>Sample file</dt>
         <dd><a href="sample_inputs/standard_html/intro.md#L1" title="sample_inputs/standard_html/intro.md#L1"><code>intro.md</code></a></dd>
         <dt>Description</dt>
         <dd>The boilerplate intro file is a Markdown or HTML file that contains supplementary content to include in the output before the generated documentation.</dd>
         <dd>This file can include an <code>[add_toc]</code> directive that specifies location for the table of contents.</dd>
      </dl>
   </dd>
   <dt id="boilerplate-postscript-file"><h2>Boilerplate postscript file</h2></dt>
   <dd>
      <dl>
         <dt>Sample file</dt>
         <dd><a href="sample_inputs/standard_html/postscript.md#L1" title="sample_inputs/standard_html/postscript.md#L1"><code>postscript.md</code></a></dd>
         <dt>Description</dt>
         <dd>The boilerplate postscript file is a Markdown or HTML file that contains supplementary content to include in the output after the generated documentation.</dd>
         <dd> This file can include an <code>[add_toc]</code> directive that specifies location for the table of contents.</dd>
      </dl>
   </dd>
</dl>
