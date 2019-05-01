// Copyright Notice:
// Copyright 2016-2019 DMTF. All rights reserved.
// License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

'use strict';
var glob = require('glob');
var jsonlint = require('jsonlint');
var fs = require('fs');
var Validator = require('jsonschema').Validator;
const config = require('config');

function isValidJSON(txt)
{
    try{
        jsonlint.parse(txt.toString());
    }
    catch(e) {
        throw Error('Invalid JSON!\n' + e.message);
    }
}

function isValidSchema(schemaname, txt)
{
    var v = new Validator();
    var schema = JSON.parse(txt.toString());
    var parts = schemaname.split('/');
    var filename = parts[1];
    v.addSchema(schema, 'http://redfish.dmtf.org/schemas/v1/'+filename);
}

function isCorrectSchemaType(schemaname, txt)
{
    var schema = JSON.parse(txt.toString());
    if(schema['$schema'] === undefined) {
        throw new Error('Missing $schema property!');
    }
    if(schemaname.indexOf('redfish-schema')) {
        //Don't test redfish-schema files
        return;
    }
    var oldStyle = (schemaname.indexOf('1.0') !== -1);
    if(!oldStyle && schema['$schema'] !== 'http://redfish.dmtf.org/schemas/v1/redfish-schema.v1_1_0.json') {
        throw new Error('$schema property doesn\'t point to correct redfish schema!');
    }
    else if(oldStyle && schema['$schema'] !== 'http://redfish.dmtf.org/schemas/v1/redfish-schema.1.0.0.json') {
        throw new Error('$schema property doesn\'t point to correct redfish schema!');
    }
}

function testJSONSchema(schema)
{
  describe(schema, () => {
    let schemaTxt = null;
    before((done) => {
      fs.readFile(schema, (err, body) => {
        if(err) {
          throw err;
        }
        schemaTxt = body;
        done();
      });
    });
    it('Is Valid JSON', () => {isValidJSON(schemaTxt);});
    it('Is Valid JSON Schema', () => {isValidSchema(schema, schemaTxt);});
    it('Is Correct Schema Type', () => {isCorrectSchemaType(schema, schemaTxt);});
  }); 
}

describe('JSON Schema', function() {
  let schemas = glob.sync(config.get('Redfish.JsonSchemaFilePath'));
  schemas.forEach(testJSONSchema);
});

