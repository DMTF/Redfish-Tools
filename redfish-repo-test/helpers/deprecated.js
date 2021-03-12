const glob = require('glob');
const path = require('path');
const assert = require('assert');
const fs = require('fs').promises;
const config = require('config');
const process = require('process');
const CSDL = require('CSDLParser');

var options = {useLocal: [config.get('Redfish.CSDLDirectory'), path.normalize(__dirname+'/fixtures')],
               useNetwork: true};

if(config.has('Redfish.AdditionalSchemaDirs')) {
  options.useLocal = options.useLocal.concat(config.get('Redfish.AdditionalSchemaDirs'));
}

const OldRegistries = ['Base.1.0.0.json', 'ResourceEvent.1.0.0.json', 'TaskEvent.1.0.0.json', 'Redfish_1.0.1_PrivilegeRegistry.json', 'Redfish_1.0.2_PrivilegeRegistry.json'];

//Setup a global cache for speed
options.cache = new CSDL.cache(options.useLocal, options.useNetwork);

const OverRideFiles = ['http://redfish.dmtf.org/schemas/swordfish/v1/Volume_v1.xml'];


var gDeprecatedCount = 0;
var gDeprecatedMap = {};

var args = process.argv.slice(2);

const files = glob.sync(config.get('Redfish.CSDLFilePath'));
const mockupFiles = glob.sync(config.get('Redfish.MockupFilePath'));
let publishedSchemas = {};
let overrideCSDLs = [];
let promise = csdlTestSetup();
promise.then((res) => {
  publishedSchemas = res[0];
  overrideCSDLs = res.slice(1);
  let promises = [];
  let promises2 = [];

  files.forEach((file) => {
    let fileName = file.substring(file.lastIndexOf('/')+1);
    promises.push(new Promise((resolve, reject) => {
        CSDL.parseMetadataFile(file, options, (err, data) => {
            if(err) {
                reject(err);
            }
            resolve(true);
        });
    }));
  });
  Promise.allSettled(promises).then(() => {
    mockupFiles.forEach((file) => {
        let fileName = file.substring(file.lastIndexOf('/')+1);
        //Just completely skip old files, the explorer config files, and second pages...
        if(OldRegistries.includes(fileName) || file.includes('explorer_config.json') || file.includes('$ref') || file.includes('/ExtErrorResp')) {
          return;
        }
        promises2.push(new Promise((resolve, reject) => {
            fs.readFile(file, 'utf-8').then((buff) => {
                let str = buff.toString();
                let json = JSON.parse(str);
                if(json["$schema"] !== undefined) {
                    //Ignore JSON schema files
                    resolve([]);
                    return;
                }
                if(json['@odata.type'] === undefined) {
                    if(json['v1'] !== undefined) {
                      /*This is probably a root json, ignore it*/
                      resolve([]);
                      return;
                    }
                    if(json['@odata.context'] === '/redfish/v1/$metadata') {
                      /*This is an Odata service doc, ignrore it*/
                      resolve([]);
                      return;
                    }
                    resolve([file+': No @odata.type']);
                    return;
                }
                let type = json['@odata.type'].substring(1);
                let CSDLType = CSDL.findByType({_options: options}, type);
                if(CSDLType === null) {
                    resolve([file+': Could not locate type '+type]);
                    return;
                }
                let errs = [];
                for(let propName in json) {
                    if(propName[0] === '@' || propName === 'Members@odata.count' || propName === 'Members@odata.nextLink') {
                      continue;
                    }
                    else if(propName.indexOf('@Redfish.') !== -1) {
                        //TODO Check other annotations; for now, just let them pass
                        continue;
                    }
                    let CSDLProperty = getCSDLProperty(propName, CSDLType);
                    if(CSDLProperty === undefined) {
                        errs.push(file+': Unknown property "'+propName+'" in type '+type);
                        continue;
                    }
                    if(CSDLProperty.Annotations['Redfish.Deprecated'] !== undefined) {
                        errs.push(file+' : Property "'+propName+'" is deprectated. "'+CSDLProperty.Annotations['Redfish.Deprecated'].String+'"');
                    }
                    if(CSDLProperty.Annotations['Redfish.Revisions'] !== undefined && CSDLProperty.Annotations['Redfish.Revisions'].Collection.Records.length > 0) {
                        for(let i = 0; i < CSDLProperty.Annotations['Redfish.Revisions'].Collection.Records.length; i++) {
                            if(CSDLProperty.Annotations['Redfish.Revisions'].Collection.Records[i].PropertyValues.Kind !== undefined && CSDLProperty.Annotations['Redfish.Revisions'].Collection.Records[i].PropertyValues.Kind.EnumMember !== undefined) {
                                errs.push(file+' : Property "'+propName+'" is deprectated. "'+CSDLProperty.Annotations['Redfish.Revisions'].Collection.Records[i].PropertyValues.Description.String+'"');
                            }
                        }
                    }
                }
                resolve(errs);
            }).catch(reject);
        }));
    });
    Promise.allSettled(promises2).then((results) => {
        results.forEach((result) => {
            let value = result.value;
            //Skip files with no issues...
            if(value.length > 0) {
                value.forEach((error) => {
                    console.log(error);
                });
            }
        });
    });
  });
}).catch((err) => {
  console.log(err.message, err.stack);
  process.exit(1)
});


function csdlTestSetup() {
    let arr = [];
    OverRideFiles.forEach((file) => {
      arr.push(new Promise((resolve, reject) => {
        CSDL.parseMetadataUri(file, options, (err, csdl) => {
          if(err) {
            reject(err);
            return;
          }
          assert.notEqual(csdl, null);
          resolve(csdl);
        });
      }));
    });
    return Promise.all(arr);
}

function searchInParentTypes(type, propName) {
    /* We do resource a little oddly in that we reference the Abstrct type everywhere that \
     * doesn't have Id, Name, or Description*/
    if(propName === 'Id' || propName === 'Name' || propName === 'Description') {
      type = CSDL.findByType({_options: options}, 'Resource.v1_0_0.Resource');
      return type.Properties[propName];
    }
    let parentType = CSDL.findByType({_options: options}, type.BaseType);
    if(parentType.Properties[propName] !== undefined) {
      return parentType.Properties[propName];
    }
    if(parentType.BaseType !== undefined) {
      return searchInParentTypes(parentType, propName);
    }
    return undefined;
  }
  
  function getCSDLProperty(propName, CSDLType) {
    let CSDLProperty = CSDLType.Properties[propName];
    if(CSDLProperty === undefined) {
      if(CSDLType.BaseType !== undefined) {
        CSDLProperty = searchInParentTypes(CSDLType, propName);
      }
    }
    return CSDLProperty;
  }