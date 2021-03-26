const glob = require('glob');
const config = require('config');
const fs = require('fs');
const path = require('path');
const matchAll = require('match-all');

// TODO:
// - Support correcting @odata.id based on filepath
// - Support updating non-resource-examples
// - Support updating Contoso.com in public-oem-examples

let csdl_files = glob.sync(path.join(config.get('Redfish.CSDLDirectory'), '**', '*.xml'));
let mockup_files = glob.sync(path.join('mockups', '**', '{index.json,*v1-example.json}'));
let metadata_files = glob.sync(path.join('mockups', '**', 'index.xml'));

// Skip schemas for registries since registries are static, and skip schemas for control terms
const csdl_files_skip = [ 'Resource_v1.xml', 'MessageRegistry_v1.xml', 'PrivilegeRegistry_v1.xml', 'RedfishExtensions_v1.xml' ];

let namespaces = []
let copyright_str = config.get('Redfish.CopyrightStr');

// Build a list of the latest CSDL namespaces
csdl_files.forEach((file) => {
  if(csdl_files_skip.indexOf(file.split(path.sep).slice(-1)[0]) === -1) {
    // Read the file
    txt = fs.readFileSync(file);
    txt = txt.toString('utf-8');

    // Find the namespace instances and go to the latest namespace
    let namespace = '';
    let schema_namespaces = matchAll(txt, /<Schema xmlns="http:\/\/docs\.oasis-open\.org\/odata\/ns\/edm" Namespace="(.+)">/gi);
    for(schema_namespace = schema_namespaces.nextRaw(); schema_namespace != null; schema_namespace = schema_namespaces.nextRaw()) {
      namespace = schema_namespace[1];
    }

    // If versioned, add it to the namespace list
    if(namespace.indexOf('.') !== -1) {
      namespaces.push(namespace);
    }
  }
});

// Go through all of the mockup files and update them as needed
mockup_files.forEach((file) => {
  fs.readFile(file, (err, txt) => {
    if(err) {
      console.error('Unable to open file ' + file + ': ' + err);
      return;
    }
    txt = txt.toString('utf-8');
    let newTxt = txt.replace(/\r\n/gm, '\n');
    newTxt = newTxt.trim();

    // Update all @odata.type instances
    namespaces.forEach((namespace) => {
      let new_type = '"@odata.type": "#' + namespace + '.'
      let old_type = new RegExp('"@odata\\.type": "#' + namespace.split('.')[0] + '\\.v\\d+_\\d+_\\d+\\.', 'g');
      newTxt = newTxt.replace(old_type, new_type);
    });

    // Go through each line and update instances as needed
    let odata_id_str = undefined
    newTxt = newTxt.split('\n');
    for(let i = 0; i < newTxt.length; i++) {
      // Pull out @odata.context if this is not the odata file
      if(newTxt[i].indexOf('"@odata.context"') !== -1 && file.indexOf(path.sep + 'odata' + path.sep) === -1) {
        newTxt.splice(i, 1);
        i--;
      }
      // Pull out @odata.id so it can be placed at the end of the file
      else if(newTxt[i].startsWith('    "@odata.id"')) {
        odata_id_str = newTxt[i].replace(',', '');
        if(file.endsWith(path.sep + 'index.json')) {
          odata_id_str = odata_id_str + ','
        }
        newTxt.splice(i, 1);
        i--;
      }
      // Remove @Redfish.Copyright and the closing }
      else if(newTxt[i].indexOf('"@Redfish.Copyright"') !== -1 || newTxt[i] === '}') {
        newTxt.splice(i, 1);
        i--;
      }
    }
    if(odata_id_str !== undefined) {
      newTxt.push(odata_id_str);
    }
    if(file.endsWith('v1-example.json') === false) {
      newTxt.push('    "@Redfish.Copyright": "' + copyright_str + '"')
    }
    newTxt.push('}')
    newTxt = newTxt.join('\n');

    // Save the file
    if(newTxt !== txt) {
      fs.writeFile(file, newTxt, (err) => {
        if(err) {
          console.error('Unable to write file ' + file + ': ' + err);
        }
      });
    }
  });
});

// Go through all of the $metadata files and update them as needed
metadata_files.forEach((file) => {
  fs.readFile(file, (err, txt) => {
    if(err) {
      console.error('Unable to open file ' + file + ': ' + err);
      return;
    }
    txt = txt.toString('utf-8');
    let newTxt = txt.replace(/\r\n/gm, '\n');
    newTxt = newTxt.trim();

    // Update the copyright
    newTxt = newTxt.replace(/.+Copyright.+/gi, '<!-- ' + copyright_str + '-->');

    // Update all namespace references
    namespaces.forEach((namespace) => {
      let new_namespace = '<edmx:Include Namespace="' + namespace + '"/>'
      let old_namespace = new RegExp('<edmx:Include Namespace="' + namespace.split('.')[0] + '\\.v\\d+_\\d+_\\d+"/>', 'g');
      newTxt = newTxt.replace(old_namespace, new_namespace);

      let new_entitycontainer = '<EntityContainer Name="Service" Extends="' + namespace + '.ServiceContainer"/>'
      let old_entitycontainer = new RegExp('<EntityContainer Name="Service" Extends="' + namespace.split('.')[0] + '\\.v\\d+_\\d+_\\d+\\.ServiceContainer"/>', 'g');
      newTxt = newTxt.replace(old_entitycontainer, new_entitycontainer);
    });

    // Save the file
    if(newTxt !== txt) {
      fs.writeFile(file, newTxt, (err) => {
        if(err) {
          console.error('Unable to write file ' + file + ': ' + err);
        }
      });
    }
  });
});