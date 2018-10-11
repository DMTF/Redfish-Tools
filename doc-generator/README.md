# Redfish Documentation Generator

Copyright 2016-2018 Distributed Management Task Force, Inc. All rights reserved.

## About

The `doc_generator` is a Python tool that parses a set of JSON schema files (typically the entire set for a version) and generates a Markdown document.

Output is GitHub-flavored Markdown targeted for the [Slate API docs generator](https://github.com/tripit/slate).

## Installation

1. Install the following required software on the machine from which you will run the `doc_generator`: 

    | Software | Description | Download |
    |----------|-------------|----------|
    | Python 3 | For Markdown output, install only the standard library. | [https://www.python.org/downloads/](https://www.python.org/downloads/) |
    | Python&#8209;Markdown | Required for HTML output. | [https://python-markdown.github.io/install/](https://python-markdown.github.io/install/) |
    | Pygments | Required for HTML output. | [http://pygments.org/](http://pygments.org/) |

1. Verify the installation of requirements. If you use `pip`:
 
    ```
    % cd doc-generator
    % pip install -r requirements.txt
    ```

## Usage

By default, `doc_generator` looks for a `json-schema` directory and
supplement file in the directory from where you run it. Alternatively,
you can specify the locations of the `json-schema` directory and
supplement file on the command line.

You must also specify a mapping from schema URIs to local directories.
The `doc_generator` tool uses this information to determine whether to get
referenced data from local files or over the Internet. See [The Supplemental Material Document](#the-supplemental-material-document).

```
usage: doc_generator.py [-h] [-n] [--format {markdown,html}] [--out OUTFILE]
                        [--sup SUPFILE] [--profile PROFILE_DOC] [-t]
                        [--escape ESCAPE_CHARS]
                        [import_from [import_from ...]]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process (wild cards are
                        acceptable). Default: json-schema

optional arguments:
  -h, --help            Show this help message and exit
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,html}
                        Output format
  --out OUTFILE         Output file (default depends on output format:
                        output.md for Markdown, index.html for HTML)
  --sup SUPFILE         Path to the supplemental material document. Default is
                        usersupplement.md for user-focused documentation, and
                        devsupplement.md for normative documentation.
  --profile PROFILE_DOC
                        Path to a JSON profile document, for profile output.
  -t, --terse           Terse output (meaningful only with --profile). By
                        default, profile output is verbose and includes all
                        properties regardless of profile requirements. "Terse"
                        output is intended for use by service developers,
                        including only the subset of properties with profile
                        requirements.
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated Markdown. For example,
                        --escape=@#. Use --escape=@ if strings with embedded @
                        are being converted to mailto links.

Example:
   doc_generator.py --format=html
   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files
```

Normative output prefers long descriptions to descriptions.

For Slate, place the `index.html.md` output in your Slate repository's source directory.

## The Supplemental Material Document

The `doc-generator/sample_inputs/excerpt/usersupplement.md` file is an example of a supplemental material document. It describes each information type that you can include in the supplement.

The most important section of this document is *Schema URI Mapping*, which describes how to map schema URIs to local files. You define and map partial URIs to local directories. The `doc_generator` uses the specified local files, if any. Otherwise, the `doc_generator` follows the full URI, including data from remote files, if possible.
