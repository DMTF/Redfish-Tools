# Travis Tests

Copyright 2016-2019 DMTF. All rights reserved.

## About

The Travis Tests contain a set of tests to verify schema and mockup files conform to rules specified by the Redfish specification.  A given Github project can be set up to run these tests for every commit to highlight errors before schema and mockup files are published.  The test framework is built on Node.js.

## Usage

The contents of this folder can be overlayed on the root directory of a project.  It also assumes that Travis has been enabled for the given project.

Some of the contents will require modification:
* package.json
    * `name`: Insert the name of the project
    * `repository/url`: Insert the .git URL of the project
    * `bugs/url`: Insert the URL for the project's issues
    * `homepage`: Insert the Git landing page for the project
* config/default.json
    * This file contains folder path definitions for schema and mockup files
