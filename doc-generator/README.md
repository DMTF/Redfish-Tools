# Redfish Documentation Generator

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

```
usage: doc_generator.py [-h] [-n] [--format {markdown,html}] [--out
OUTFILE]
                        [--sup SUPFILE] [--escape ESCAPE_CHARS]
                        [import_from]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process
  (wildcards are
                        acceptable). Default: json-schema

optional arguments:
  -h, --help            show this help message and exit
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,html}
                        Output format
  --out OUTFILE         Output file (default depends on output format:
                        output.md for markdown, index.html for html)
  --sup SUPFILE         Path to the supplemental material
  document. Default is
                        usersupplement.md for user-focused
                        documentation, and
                        devsupplement.md for normative documentation.
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated
                        markdown; e.g.,
                        --escape=@#. Use --escape=@ if strings with
                        embedded @
                        are being converted to mailto links.

Example:
   doc_generator.py --format=html
   doc_generator.py --format=html --out=/path/to/output/index.html /path/to/spmf/json-files
```

Normative output prefers longDescriptions to descriptions.

For Slate, place the output index.html.md in your Slate repository's source directory.
