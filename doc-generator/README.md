# Redfish Documentation Generator

Copyright 2016 Distributed Management Task Force, Inc. All rights reserved.

## About

The Documentation Generator is a python tool that parses a set of JSON schema files (typically the entire set for a version) and generates a markdown document.

Output is GitHub-flavored markdown targeted for the Slate documentation tool (https://github.com/tripit/slate).

## Installation

* Ensure that the machine running the tool has python3 installed. For markdown output, only the standard library is required.
* For HTML output, python-markdown and Pygments must also be installed:
  * python-markdown: https://pythonhosted.org/Markdown/install.html
  * Pygments: http://pygments.org/

If you are using pip:

```
% pip install -r requirements.txt
```

## Usage

By default, doc_generator will look for a json-schema directory and
supplement file in the directory from which it is run. Alternatively,
you can specify these locations on the command line.

You must also specify a mapping from schema URIs to local directories.
The doc_generator tool uses this information to determine whether to get
referenced data from local files, or to attempt to retrieve it over the
internet. See "The Supplemental File," below.

```
usage: doc_generator.py [-h] [-n] [--format {markdown,html}] [--out OUTFILE]
                        [--sup SUPFILE] [--profile PROFILE_DOC] [-t]
                        [--escape ESCAPE_CHARS]
                        [import_from [import_from ...]]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process (wildcards are
                        acceptable).Default: json-schema

optional arguments:
  -h, --help            show this help message and exit
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,html}
                        Output format
  --out OUTFILE         Output file (default depends on output format:
                        output.md for markdown, index.html for html)
  --sup SUPFILE         Path to the supplemental material document. Default is
                        usersupplement.md for user-focused documentation, and
                        devsupplement.md for normative documentation.
  --profile PROFILE_DOC
                        Path to a JSON profile document, for profile output
  -t, --terse           Terse output (meaningful only with --profile). By
                        default,profile output is verbose, including all
                        properties regardless ofprofile requirements. "Terse"
                        output is intended for use byService developers,
                        including only the subset of properties withprofile
                        requirements.
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated markdown; e.g.,
                        --escape=@#. Use --escape=@ if strings with embedded @
                        are being converted to mailto links.

Example:
   doc_generator.py --format=html
   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files
```

Normative output prefers longDescriptions to descriptions.

For Slate, place the output index.html.md in your Slate repository's source directory.

## The Supplemental Material Document

usersupplement.md in this directory is an example of a supplemental
material document. It includes explanations of each type of
information you can include in the supplement.

The most important element of the supplemental document is the *Schema
URI Mapping* section. In this section, you identify partial URIs that
map to local directories, directing the doc_generator to look in the
specified local directory when following references in a schema.