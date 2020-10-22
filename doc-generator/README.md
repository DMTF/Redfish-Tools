# Redfish Documentation Generator

Copyright 2016-2020 Distributed Management Task Force, Inc. All rights reserved.

## About

The `doc_generator.py` is a Python tool that parses a set of JSON schema files (typically the entire set for a version) and generates a formatted documentation.

The default output is GitHub-flavored Markdown targeted for the [Slate API docs generator](https://github.com/tripit/slate). Other options include markdown tuned to the DMTF document publication process, HTML, "property index" documentation, and CSV.


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

By default, `doc_generator.py` looks for a `json-schema` directory and
supplement file in the directory from where you run it. Alternatively,
you can specify the locations of the `json-schema` directory and
supplement file when you run `doc_generator.py`.

You must also specify a mapping from schema URIs to local directories.
The `doc_generator.py` tool uses this information to determine whether to get
referenced data from local files or over the Internet. See [The Supplemental Material Document](#the-supplemental-material-document).

The --config option specifies a file in which you can specify many of the command-line
options described here, as well as some parameters, such as URI mappings, that
would otherwise be included in the Supplemental Material Document. See
[Config Files](README_config_files.md).

```
usage: doc_generator.py [-h] [--config CONFIG_FILE] [-n]
                        [--format {slate,markdown,html,csv}] [--out OUTFILE]
                        [--sup SUPFILE] [--payload_dir payload_dir]
                        [--profile PROFILE_DOC] [-t] [--subset SUBSET_DOC]
                        [--property_index]
                        [--property_index_config_out CONFIG_FILE_OUT]
                        [--escape ESCAPE_CHARS]
                        [import_from [import_from ...]]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process (wild cards are
                        acceptable). Default: json-schema

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  Path to a config file, containing configuration in
                        JSON format.
  -n, --normative       Produce normative (developer-focused) output
  --format {slate,markdown,html,csv}
                        Output format
  --out OUTFILE         Output file (default depends on output format:
                        output.md for Markdown, index.html for HTML,
                        output.csv for CSV
  --sup SUPFILE         Path to the supplemental material document. Default is
                        usersupplement.md for user-focused documentation, and
                        devsupplement.md for normative documentation.
  --payload_dir payload_dir
                        Directory location for JSON payload and Action
                        examples. Optional.Within this directory, use the
                        following naming scheme for example files:
                        <schema_name>-v<major_version>-example.json for JSON
                        payloads, <schema_name-v<major_version>-action-<action
                        _name>.json for action examples.
  --profile PROFILE_DOC
                        Path to a JSON profile document, for profile output.
  -t, --terse           Terse output (meaningful only with --profile). By
                        default, profile output is verbose and includes all
                        properties regardless of profile requirements. "Terse"
                        output is intended for use by Service developers,
                        including only the subset of properties with profile
                        requirements.
  --subset SUBSET_DOC   Path to a JSON profile document. Generates "Schema
                        subset" output, with the subset defined in the JSON
                        profile document.
  --property_index      Produce Property Index output.
  --property_index_config_out CONFIG_FILE_OUT
                        Generate updated config file, with specified filename
                        (property_index mode only).
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated Markdown. For
                        example, --escape=@#. Use --escape=@ if strings with
                        embedded @ are being converted to mailto links.

Example:
   doc_generator.py --format=html
   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files
```

Refer to README_Property_Index.md for documentation on Property Index mode.

Normative output prefers long descriptions to descriptions.

For Slate, place the `index.html.md` output in your Slate repository's source directory.

## The Supplemental Material Document

The `doc-generator/sample_inputs/usersupplement.md` file is an example of a supplemental material document. It describes each information type that you can include in the supplement.

The most important section of this document is *Schema URI Mapping*, which describes how to map schema URIs to local files. You define and map partial URIs to local directories. The `doc_generator.py` uses the specified local files, if any. Otherwise, the `doc_generator.py` follows the full URI, including data from remote files, if possible.
