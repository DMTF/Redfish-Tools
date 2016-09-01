# Redfish Documentation Generator

## About

The Documentation Generator is a python tool that parses a set of JSON schema files (typically the entire set for a version) and generates a markdown document.

Output is GitHub-flavored markdown targeted for the Slate documentation tool (https://github.com/tripit/slate).

## Usage

* Ensure that the machine running the tool has python3 installed. For markdown output, only the standard library is required. For HTML output, python-markdown must also be installed: https://pythonhosted.org/Markdown/install.html

* Identify the location of the JSON schema file(s) on your local system.

```
usage: doc_generator.py [-h] [-n] [--format {markdown,html}] [--out OUTFILE]
                        [--sup SUPFILE] [--escape ESCAPE_CHARS]
                        import_from [import_from ...]

Generate documentation for Redfish JSON schema files.

positional arguments:
  import_from           Name of a file or directory to process (wildcards are
                        acceptable)

optional arguments:
  -h, --help            show this help message and exit
  -n, --normative       Produce normative (developer-focused) output
  --format {markdown,html}
                        Output format
  --out OUTFILE         Output file (default depends on output format)
  --sup SUPFILE         Path to the supplemental material document. Default is
                        usersupplement.md for user-focused documentation, and
                        devsupplement.md for normative documentation.
  --escape ESCAPE_CHARS
                        Characters to escape (\) in generated markdown; e.g.,
                        --escape=@#. Use --escape=@ if strings with embedded @
                        are being converted to mailto links.
```

Normative output prefers longDescriptions to descriptions.

For Slate, place the output index.html.md in your Slate repository's source directory.
