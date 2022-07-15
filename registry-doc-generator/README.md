# Registry Doc Generator

Copyright 2022 DMTF. All rights reserved.

## About

The Registry Doc Generator is a Python3 tool that processes Redfish message registry files and converts them to a Markdown document.

## Requirements

External modules:
* packaging: https://pypi.python.org/pypi/packaging

You may install the external modules by running:

`pip install -r requirements.txt`

## Usage

Example: `python3 registry-doc-generator.py --input <Regisistry-Dir> --output <Output-File>`

The tool will process all files found in the folder specified by the *input* argument.  It will process the folder contents, build a Markdown document, and save it to the file specified by the *output* argument.

### Options

```
usage: registry-doc-generator.py [-h] --input INPUT --output OUTPUT
                                 [--intro INTRO] [--postscript POSTSCRIPT]

A tool to build a document for message registries

required arguments:
  --input INPUT, -I INPUT
                        The folder containing the registry files to convert
  --output OUTPUT, -O OUTPUT
                        The output Markdown file to generate

optional arguments:
  -h, --help            show this help message and exit
  --intro INTRO, -intro INTRO
                        File containing intro text to insert at the beginning
                        of the document
  --postscript POSTSCRIPT, -postscript POSTSCRIPT
                        File containing postscript text to insert at the end
                        of the document
```
