const glob = require('glob');
const path = require('path');
const assert = require('assert');
const CSDL = require('CSDLParser');
const fs = require('fs');
const traverse = require('traverse');
const url = require('url');
const fuzzy = require('fuzzy');
const jptr = require('json8-pointer');
const published = require('./helpers/published_schema');
const ucum = require('./fixtures/units');
const config = require('config');

const PascalRegex = new RegExp('^([A-Z][a-z0-9]*)+$', 'm');

const syntaxBatch = {};
const overrideBatch = {};
const mockupsCSDL = {};
var options = {useLocal: [config.get('Redfish.CSDLDirectory'), path.normalize(__dirname+'/fixtures')],
               useNetwork: true};

if(config.has('Redfish.AdditionalSchemaDirs')) {
  options.useLocal = options.useLocal.concat(config.get('Redfish.AdditionalSchemaDirs'));
}

//Setup a global cache for speed
options.cache = new CSDL.cache(options.useLocal, options.useNetwork);

/***************** White lists ******************************/
//Units that don't exist in UCUM
const unitsWhiteList = ['RPM'];
//Enumeration Member names that are non-Pascal Cased
const NonPascalCaseEnumWhiteList = ['iSCSI', 'iQN', 'FC_WWN', 'TX_RX', 'EIA_310', 'string', 'number', 'NVDIMM_N', 
                                    'NVDIMM_F', 'NVDIMM_P', 'DDR4_SDRAM', 'DDR4E_SDRAM', 'LPDDR4_SDRAM', 'DDR3_SDRAM',
                                    'LPDDR3_SDRAM', 'DDR2_SDRAM', 'DDR2_SDRAM_FB_DIMM', 'DDR2_SDRAM_FB_DIMM_PROBE', 
                                    'DDR_SGRAM', 'DDR_SDRAM', 'SO_DIMM', 'Mini_RDIMM', 'Mini_UDIMM', 'SO_RDIMM_72b',
                                    'SO_UDIMM_72b', 'SO_DIMM_16b', 'SO_DIMM_32b', 'TPM1_2', 'TPM2_0', 'TCM1_0', 'iWARP',
                                    'RSA_2048Bit', 'RSA_3072Bit', 'RSA_4096Bit', 'EC_P256', 'EC_P384', 'EC_P521', 'EC_X25519', 'EC_X448', 'EC_Ed25519', 'EC_Ed448'];
//Properties names that are non-Pascal Cased
const NonPascalCasePropertyWhiteList = ['iSCSIBoot'];

const ODataSchemaFileList = [ 'Org.OData.Core.V1.xml', 'Org.OData.Capabilities.V1.xml', 'Org.OData.Measures.V1.xml' ];
const SwordfishSchemaFileList = [ 'HostedStorageServices_v1.xml', 'StorageServiceCollection_v1.xml', 'StorageSystemCollection_v1.xml', 'StorageService_v1.xml', 'Volume_v1.xml', 'VolumeCollection_v1.xml' ];
const ContosoSchemaFileList = [ 'ContosoExtensions_v1.xml', 'TurboencabulatorService_v1.xml' ];
const EntityTypesWithNoActions = [ 'ServiceRoot', 'ItemOrCollection', 'Item', 'ReferenceableMember', 'Resource', 'ResourceCollection', 'ActionInfo', 'TurboencabulatorService' ];
const OldRegistries = ['Base.1.0.0.json', 'ResourceEvent.1.0.0.json', 'TaskEvent.1.0.0.json', 'Redfish_1.0.1_PrivilegeRegistry.json', 'Redfish_1.0.2_PrivilegeRegistry.json'];
const NamespacesWithReleaseTerm = ['PhysicalContext', 'Protocol' ];
const NamespacesWithoutReleaseTerm = ['RedfishExtensions.v1_0_0', 'Validation.v1_0_0', 'RedfishError.v1_0_0', 'Schedule.v1_0_0', 'Schedule.v1_1_0' ];
const OverRideFiles = ['http://redfish.dmtf.org/schemas/swordfish/v1/Volume_v1.xml'];
/************************************************************/

describe('CSDL Tests', () => {
  const files = glob.sync(config.get('Redfish.CSDLFilePath'));
  let publishedSchemas = {};
  let overrideCSDLs = [];
  before(function(done){
    this.timeout(30000);
    let promise = csdlTestSetup();
    promise.then((res) => {
      publishedSchemas = res[0];
      overrideCSDLs = res.slice(1);
      done();
    }).catch((err) => {
      assert.equal(err, null);
    });
  });
  
  files.forEach((file) => {
    describe(file, () => {
      let fileName = file.substring(file.lastIndexOf('/')+1);
      let csdl = null;
      before(function(done) {
        this.timeout(60000);
        CSDL.parseMetadataFile(file, options, (err, data) => {
          if(err) {
            throw err;
          }
          csdl = data;
          done();
        });
      });
      it('Valid Syntax', () => {
        assert.notEqual(csdl, null);
      });
      //These tests are only valid for new format CSDL...
      if(file.indexOf('_v') !== -1) {
        it('Units are valid', () => {validUnitsTest(csdl);});
      }
      //Permissions checks are not valid on this file...
      if(file.includes('RedfishExtensions_v1.xml') === false) {
        it('Has Permission Annotations', () => {permissionsCheck(csdl);});
        it('Complex Types Should Not Have Permissions', () => {complexTypesPermissions(csdl);});
      }
      it('Descriptions have trailing periods', () => {descriptionPeriodCheck(csdl);});
      it('No Empty Schema Tags', () => {checkForEmptySchemas(csdl);});
      it('BaseTypes are valid', () => {checkBaseTypes(csdl);});
      it('All Annotation Terms are valid', () => {checkAnnotationTerms(csdl);});
      it('Enum Members are valid names', () => {checkEnumMembers(csdl);});
      //Don't do Pascal Case checking in the RedfishErrors file; the properties are dictated by the OData spec
      if(file.includes('RedfishError_v1.xml') === false) {
        it('Properties are Pascal-cased', () => {checkPropertiesPascalCased(csdl);});
      }
      it('Reference URIs are valid', () => {checkReferenceUris(csdl);});
      //skip the metadata mockup
      if(file.includes('$metadata') === false) {
        it('All References Used', () => {checkReferencesUsed(csdl);});
        it('All namespaces have OwningEntity', () => {schemaOwningEntityCheck(csdl);});
      }
      it('All EntityType defintions have Actions', () => {entityTypesHaveActions(csdl);});
      it('NavigationProperties for Collections cannot be Nullable', () => {navigationPropNullCheck(csdl);});
      it('All new schemas are one version off published', () => {schemaVersionCheck(csdl, publishedSchemas);});
      //Skip OEM extentions and metadata files
      if(ContosoSchemaFileList.indexOf(fileName) === -1 && fileName !== 'index.xml' && fileName !== 'Volume_v1.xml') {
        it('All definitions shall include Description and LongDescription annotations', () => {definitionsHaveAnnotations(csdl);});
        it('All versioned, non-errata namespaces have Release', () => {schemaReleaseCheck(csdl);});
      }
    });
  });
});

function csdlTestSetup() {
  let arr = [];
  arr.push(published.getPublishedSchemaVersionList('http://redfish.dmtf.org/schemas/v1/'));
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

describe('Mockup Syntax Tests', () => {
  let mockupFiles = glob.sync(config.get('Redfish.MockupFilePath'));
  let linkCache = {};
  let txtCache = {};
  let jsonCache = {};

  before(function(done) {
    this.timeout(10000);
    //setup cache's
    let arr = [];
    mockupFiles.forEach((file) => {
      addFileToLinkCache(file, linkCache);
      arr.push(fileToCachePromise(file));
    });
    Promise.all(arr).then((data) => {
      for(let i = 0; i < data.length; i++) {
        let name = data[i].name;
        txtCache[name] = data[i].txt;
        jsonCache[name] = data[i].json;
      }
      done();
    });
  });

  mockupFiles.forEach((file) => {
    let fileName = file.substring(file.lastIndexOf('/')+1);
    //Just completely skip old files and the explorer config files...
    if(OldRegistries.includes(fileName) || file.includes('explorer_config.json')) {
      return;
    }
    describe(file, function() {
      let txt = null;
      let json = null;
      before(() => {
        txt = txtCache[file];
        //Free this memory up...
        delete txtCache[file];
        json = jsonCache[file];
      });
      it('Is UTF-8 Encoded', function() {
        let utf8 = txt.toString('utf-8');
        assert.ok(txt.equals(Buffer.from(utf8, 'utf-8')), 'contains invalid utf-8 byte code');
      });
      it('Is Valid JSON', function() {
        assert.notEqual(json, null);
      });
      //Don't worry about links in the non-resource-examples as they probably belong to other mockups
      //Also skip the DSP2046 examples as this isn't a full tree, but just individual examples
      if(file.includes('non-resource-examples') === false && file.includes('DSP2046-examples') === false) {
        it('Links are consistent', function() {
          let linkToFile = getCache(file, linkCache);
          let walker = traverse(json);
          walker.forEach(function() {
            if(!this.isLeaf) return;

            if(!isLink(this.key)) return;
            let link = url.parse(this.node); 
            let filepath = linkToFile[link.pathname];
            if(filepath === undefined && link.pathname.substr(link.pathname.length - 1) === '/') {
              //Try without the trailing slash...
              filepath = linkToFile[link.pathname.substr(0, link.pathname.length - 1)];
            }
            let refd = jsonCache[filepath];
            if(refd === undefined) {
              let split = path.normalize(file).split(path.sep).slice(0, 2);
              let mockupPath = split.join('/');
              let errorMsg = 'Invalid link in JSON at property /' + this.path.join('/') + ' with value ' + this.node + '. No such file exists in mockup at path.';
              let invalidPath = this.node.replace('/redfish/v1/', mockupPath).split('/');
              let files = Object.keys(linkToFile);
              let possible = fuzzy.filter(path.join(...invalidPath), files).map(x => path2Redfish(x.string, true));
              if(possible.length) {
                errorMsg += `\nPerhaps you meant one of:\n${possible.join('\n')}`;
              }
              assert.fail(errorMsg);
            }
            if(link.hash) {
              refd = jptr.find(refd, link.hash.slice(1));
              assert(refd !== undefined, 'invalid fragment component in JSON at property /' + this.path.join('/') + ' with fragment value ' + link.hash);
            }
          });
        });
      }
      //Only do Metadata <=> Mockup tests on master branch or local dev test
      if(process.env.TRAVIS === undefined || process.env.TRAVIS_BRANCH === 'master') {
        //Ignore the paging file and the external error example
        if(file.includes('$ref') === false && file.includes('/ExtErrorResp') === false && file.includes('/ConstrainedCompositionCapabilities') === false) {
          it('Is Valid Type', function() {
            validCSDLTypeInMockup(json, file);
          });
        }
      }
    });
  });
});

function fileToCachePromise(file) {
  return new Promise((resolve, reject) => {
    fs.readFile(file, (err, data) => {
      if(err) {
        resolve({name: file, txt: null, json: null});
        return;
      }
      resolve({name: file, txt: data, json: JSON.parse(data.toString('utf-8'))});
    });
  });
}

function path2Redfish(p, removeIndex) {
  let myP = path.normalize(p);
  const link = myP.split(path.sep).slice(2, removeIndex ? -1 : void 0);
  link.unshift('', 'redfish', 'v1', '');
  //Need unix style pathing...
  return path.posix.normalize(link.join('/'));
}

function addFileToLinkCache(filename, cache) {
  let split = path.normalize(filename).split(path.sep);
  if(split[0] === 'mockups') {
    let mockupName = split[1];
    if(cache[mockupName] === undefined) {
      cache[mockupName] = {};
    }
    split = split.slice(2, -1); 
    split.unshift('redfish', 'v1');
    let link = '/'+split.join('/');
    cache[mockupName][link] = filename;
  }
}

function getCache(filename, cache) {
  let split = path.normalize(filename).split(path.sep);
  if(split[0] === 'mockups') {
    return cache[split[1]];
  }
}

const LinkProperties = [
  /^@odata\.id$/,
  /^[^@]*@odata\.navigationLink$/,
  /^[^@]*@odata\.nextLink$/
]

function isLink(key) {
  for (var i = 0, llen = LinkProperties.length - 1; i < llen; i++) {
    if (LinkProperties[i].test(key)) return true
  }
}

function validUnitsTest(csdl) {
  let measures = CSDL.search(csdl, 'Annotation', 'Measures.Unit');
  if(measures.length === 0) {
    return;
  }
  for(let i = 0; i < measures.length; i++) {
    let unitName = measures[i].String;
    if(unitsWhiteList.indexOf(unitName) !== -1) {
      continue;
    }
    let pos = unitName.indexOf('/s');
    if(pos !== -1) {
      unitName = unitName.substring(0, pos);
    }
    if(ucum.units.includes(unitName)) {
      //Have unit, all good...
      return;
    }
    else if(ucum.prefixes.includes(unitName[0]) && ucum.units.includes(unitName.substring(1))) {
      //Have prefix and unit, all good...
      return;
    }
    else if(ucum.prefixes.includes(unitName.substring(0,2)) && ucum.units.includes(unitName.substring(2))) {
      //Have prefix and unit, all good...
      return;
    }
    throw new Error('Unit name '+unitName+' is not a valid UCUM measure');
  }
}

function permissionsCheck(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  if(schemas.length === 0) {
    return;
  }
  for(let i = 0; i < schemas.length; i++) {
    if(schemas[i]._Name.startsWith('Org.OData') || schemas[i]._Name.startsWith('RedfishExtensions')) {
      continue;
    }
    checkPermissionsInSchema(schemas[i], csdl);
  }
}

function checkPermissionsInSchema(schema, csdl) {
  let properties = CSDL.search(schema, 'Property');
  if(properties.length === 0) {
    return;
  }
  for(let i = 0; i < properties.length; i++) {
    let permissions = CSDL.search(properties[i], 'Annotation', 'OData.Permissions');
    if(permissions.length === 0) {
      let propType = properties[i].Type;
      if(propType.startsWith('Collection(')) {
        propType = propType.substring(11, propType.length-1);
      }
      let type = CSDL.findByType(csdl, propType);
      if(type === null || type === undefined) {
        if(overrideCSDLs.length > 0) {
          for(let j = 0; j < overrideCSDLs.length; j++) {
            type = CSDL.findByType(overrideCSDLs[j], propType);
            if(type !== null && type !== undefined) {
              break;
            }
          }
        }
        if(type === null || type === undefined) {
          throw new Error('Unable to locate type "'+propType+'"');
        }
      }
      else {
        if(type.constructor.name !== 'ComplexType') {
          throw new Error('Property '+properties[i].Name+' in Schema '+schema._Name+' of '+propType+' lacks permission!');
        }
      }
    }
  }
}

function complexTypesPermissions(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  if(schemas.length === 0) {
    return;
  }
  for(let i = 0; i < schemas.length; i++) {
    if(schemas[i]._Name.startsWith('Org.OData') || schemas[i]._Name.startsWith('RedfishExtensions')) {
      continue;
    }
    checkComplexTypePermissionsInSchema(schemas[i], csdl);
  }
}

function checkComplexTypePermissionsInSchema(schema, csdl) {
  let properties = CSDL.search(schema, 'Property');
  if(properties.length === 0) {
    return;
  }
  for(let i = 0; i < properties.length; i++) {
    let permissions = CSDL.search(properties[i], 'Annotation', 'OData.Permissions');
    if(permissions.length !== 0) {
      let propType = properties[i].Type;
      if(propType.startsWith('Collection(')) {
        propType = propType.substring(11, propType.length-1);
      }
      let type = CSDL.findByType(csdl, propType);
      if(type === null || type === undefined) {
        throw new Error('Unable to locate type "'+propType+'"');
      }
      else {
        if(type.constructor.name === 'ComplexType') {
          throw new Error('Property '+properties[i].Name+' in Schema '+schema._Name+' of '+propType+' has permissions!');
        }
      }
    }
  }
}

function descriptionPeriodCheck(csdl) {
  let descriptions = CSDL.search(csdl, 'Annotation', 'OData.Description');
  if(descriptions.length !== 0) {
    for(let i = 0; i < descriptions.length; i++) {
      descriptionEndsInPeriod(descriptions[i]);
    }
  }
  let long_descriptions = CSDL.search(csdl, 'Annotation', 'OData.LongDescription');
  if(long_descriptions.length !== 0) {
    for(let i = 0; i < long_descriptions.length; i++) {
      descriptionEndsInPeriod(long_descriptions[i]);
    }
  }
}

function descriptionEndsInPeriod(desc) {
  let str = desc.String;
  if(str.slice(-1) !== '.') {
    throw new Error('"' + str + '" does not end in a period!');
  }
}

function checkForEmptySchemas(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  if(schemas.length === 0) {
    return;
  }
  for(let i = 0; i < schemas.length; i++) {
    if(schemas[i]._Name.startsWith('Org.OData')) {
      continue;
    }
    if(this.context.name.includes('mockups')) {
      continue;
    }
    var properties = Object.keys(schemas[i]).filter(function(value) {
      if(value[0] === '_') {
        return false;
      }
      return true;
    });
    if(properties.length === 0) {
      throw new Error('Schema '+schemas[i]._Name+' is empty!');
    }
    if(properties.length === 1 && schemas[i].Annotations !== undefined) {
      trivialNamespaceCheck(schemas[i]);
    }
  }
}

function trivialNamespaceCheck(schema) {
  if(Object.keys(schema.Annotations).length === 0) {
    throw new Error('Schema '+schema._Name+' lacks Annotations!');
  }
  if(schema.Annotations['OData.Description'] === undefined) {
    throw new Error('Schema '+schema._Name+' lacks OData.Description!');
  }
}

function checkBaseTypes(csdl) {
  let entityTypes =  CSDL.search(csdl, 'EntityType');
  for(let i = 0; i < entityTypes.length; i++) {
    verifyBaseType(entityTypes[i], csdl);
  }
  let complexTypes =  CSDL.search(csdl, 'ComplexType');
  for(let i = 0; i < complexTypes.length; i++) {
    verifyBaseType(complexTypes[i], csdl);
  }
}

function verifyBaseType(entityType, csdl) {
  if(entityType.BaseType === undefined) {
    /*No base type. This is valid.*/
    return;
  }
  let baseType = CSDL.findByType(csdl, entityType.BaseType);
  if(baseType === null) {
    throw new Error('Unable to locate type "'+entityType.BaseType+'"');
  }
}

function checkAnnotationTerms(csdl) {
  let annotations = CSDL.search(csdl, 'Annotation');
  for(let i = 0; i < annotations.length; i++) {
    let type = CSDL.findByType(csdl, annotations[i].Name);
    if(type === null) {
      throw new Error('Unable to locate annotation term "'+annotations[i].Name+'"');
    }
  }
}

function checkEnumMembers(csdl) {
  let enums = CSDL.search(csdl, 'EnumType');
  for(let i = 0; i < enums.length; i++) {
    let keys = Object.keys(enums[i].Members);
    for(let j = 0; j < keys.length; j++) {
      if(keys[j].match(PascalRegex) === null && NonPascalCaseEnumWhiteList.indexOf(keys[j]) === -1) {
        throw new Error('Enum member "'+keys[j]+'" of EnumType '+enums[i].Name+' is invalid!');
      }
    }
  }
}

function checkPropertiesPascalCased(csdl) {
  let properties = CSDL.search(csdl, 'Property');
  for(let i = 0; i < properties.length; i++) {
    if(properties[i].Name.match(PascalRegex) === null && NonPascalCasePropertyWhiteList.indexOf(properties[i].Name) === -1) {
      throw new Error('Property Name "'+properties[i].Name+'" is not Pascal-cased');
    }
  }
  let navproperties = CSDL.search(csdl, 'NavigationProperty');
  for(let i = 0; i < navproperties.length; i++) {
    if(navproperties[i].Name.match(PascalRegex) === null) {
      throw new Error('Property Name "'+navproperties[i].Name+'" is not Pascal-cased');
    }
  }
}

function checkReferenceUris(csdl) {
    // Find all external schema references
    let references = CSDL.search(csdl, 'Reference', undefined, true);

    // Go through each reference
    for(let i = 0; i < references.length; i++) {
        // Find the last / character to break apart the file name from its directory
        let uri_index = references[i].Uri.lastIndexOf('/');
        if(uri_index === -1) {
            // Should never happen; all URIs need to have some / characters
            throw new Error('Reference "'+references[i].Uri+'" does not contain any / characters');
        }

        // Break the string apart
        let file_name = references[i].Uri.substring(uri_index+1);
        if(file_name === '') {
            throw new Error('Reference "'+references[i].Uri+'" has an empty file name');
        }
        let directory = references[i].Uri.substring(0, uri_index);
        if(directory === '') {
            throw new Error('Reference "'+references[i].Uri+'" has an empty directory');
        }

        // Check the directory against what it should be
        if(ODataSchemaFileList.indexOf(file_name) !== -1) {
            if(directory !== 'http://docs.oasis-open.org/odata/odata/v4.0/errata03/csd01/complete/vocabularies') {
                throw new Error('Reference "'+references[i].Uri+'" does not point to OData schema directory');
            }
        }
        else if(SwordfishSchemaFileList.indexOf(file_name) !== -1) {
            if(directory !== 'http://redfish.dmtf.org/schemas/swordfish/v1') {
                throw new Error('Reference "'+references[i].Uri+'" does not point to Swordfish schema directory');
            }
        }
        else if(ContosoSchemaFileList.indexOf(file_name) !== -1) {
            // These files are for OEM examples and don't need to resolve to anything; they are never published
        }
        else {
            if(directory !== 'http://redfish.dmtf.org/schemas/v1') {
                throw new Error('Reference "'+references[i].Uri+'" does not point to DMTF schema directory');
            }
        }
    }
}

function checkReferencesUsed(err, csdl) {
    if(this.context.name.includes('$metadata')) {
      //Skip $metadata docs. They should include everything...
      return;
    }

    let schemas = CSDL.search(csdl, 'Schema');

    let nameSpaceAliases = [];

    // Find all external schema references
    let references = CSDL.search(csdl, 'Reference', undefined, true);
    for(let i = 0; i < references.length; i++) {
        nameSpaceAliases = nameSpaceAliases.concat(Object.keys(references[i].Includes));
    }
    nameSpaceAliases.sort(function (a,b) {
        if(a.length > b.length) {
            return -1;
        }
        else if(b.length > a.length) {
            return 1;
        }
        return a.localeCompare(b);
    });

    for(let i = 0; i < schemas.length; i++) {
        if(nameSpaceAliases.length === 0) {
            break;
        }
        for(let propName in schemas[i]) {
            if(propName === '_Name') {
                continue;
            }
            else if(propName === 'Annotations') {
                nameSpaceAliases = annotationsHaveNamespace(schemas[i].Annotations, nameSpaceAliases);
            }
            else if(propName === 'Service') {
                for(let j = 0; j < nameSpaceAliases.length; j++) {
                    if(schemas[i].Service.Extends.startsWith(nameSpaceAliases[j])) {
                        nameSpaceAliases.splice(j, 1);
                        break;
                    }
                }
            }
            else {
                let entity = schemas[i][propName];
                switch(entity.constructor.name) {
                    case 'EntityType':
                        nameSpaceAliases = entityTypeHasNamespace(entity, nameSpaceAliases);
                        break;
                    case 'EntityContainer':
                        if(entity.Extends !== undefined) {
                          for(let j = 0; j < nameSpaceAliases.length; j++) {
                            if(entity.Extends.startsWith(nameSpaceAliases[j])) {
                              nameSpaceAliases.splice(j, 1);
                              break;
                            }
                          }
                        }
                        break;
                    case 'EnumType':
                        nameSpaceAliases = annotationsHaveNamespace(entity.Annotations, nameSpaceAliases);
                        for(let memberName in entity.Members) {
                           let member = entity.Members[memberName];
                           if(member.Annotations !== undefined) {
                             nameSpaceAliases = annotationsHaveNamespace(member.Annotations, nameSpaceAliases);
                           }
                        }
                        break;
                    case 'ComplexType':
                        nameSpaceAliases = complexTypeHasNamespace(entity, nameSpaceAliases);
                        break;
                    case 'TypeDefinition':
                        nameSpaceAliases = annotationsHaveNamespace(entity.Annotations, nameSpaceAliases);
                        if(entity.UnderlyingType !== undefined) {
                          for(let j = 0; j < nameSpaceAliases.length; j++) {
                            if(entity.UnderlyingType.startsWith(nameSpaceAliases[j])) {
                              nameSpaceAliases.splice(j, 1);
                              break;
                            }
                          }
                        }
                        break;
                    case 'Action':
                        nameSpaceAliases = annotationsHaveNamespace(entity.Annotations, nameSpaceAliases);
                        nameSpaceAliases = propertiesHaveNamespace(entity.Parameters, nameSpaceAliases);
                        if(entity.ReturnType !== null) {
                          for(let j = 0; j < nameSpaceAliases.length; j++) {
                            if(entity.ReturnType.Type.startsWith(nameSpaceAliases[j])) {
                              nameSpaceAliases.splice(j, 1);
                              break;
                            }
                          }
                        }
                        break;
                    case 'Term':
                        nameSpaceAliases = annotationsHaveNamespace(entity.Annotations, nameSpaceAliases);
                        if(entity.Type !== null) {
                          for(let j = 0; j < nameSpaceAliases.length; j++) {
                            if(entity.Type.startsWith(nameSpaceAliases[j]) || entity.Type.startsWith('Collection('+nameSpaceAliases[j])) {
                              nameSpaceAliases.splice(j, 1);
                              break;
                            }
                          }
                        }
                        break;
                    default:
                        break;
                }
            }
        }
    }

    if(nameSpaceAliases.length > 0) {
        // TODO: This is a workaround until we process annotations on members
        // within enums (some use Redfish.Deprecated)
        if(nameSpaceAliases.toString() !== 'Redfish') {
            throw new Error('Namespaces '+nameSpaceAliases.toString()+' are unused!');
        }
    }
}

function entityTypeHasNamespace(entityType, nameSpaceAliases) {
    if(entityType.BaseType !== undefined) {
        for(let i = 0; i < nameSpaceAliases.length; i++) {
            if(entityType.BaseType.startsWith(nameSpaceAliases[i])) {
                nameSpaceAliases.splice(i, 1);
                break;
            }
        }
    }
    nameSpaceAliases = annotationsHaveNamespace(entityType.Annotations, nameSpaceAliases);
    nameSpaceAliases = propertiesHaveNamespace(entityType.Properties, nameSpaceAliases);
    return nameSpaceAliases;
}

function complexTypeHasNamespace(complexType, nameSpaceAliases) {
    if(complexType.BaseType !== undefined) {
        for(let i = 0; i < nameSpaceAliases.length; i++) {
            if(complexType.BaseType.startsWith(nameSpaceAliases[i])) {
                nameSpaceAliases.splice(i, 1);
                break;
            }
        }
    }
    nameSpaceAliases = annotationsHaveNamespace(complexType.Annotations, nameSpaceAliases);
    nameSpaceAliases = propertiesHaveNamespace(complexType.Properties, nameSpaceAliases);
    return nameSpaceAliases;
}

function annotationsHaveNamespace(annotations, nameSpaceAliases) {
  if(annotations.length === 0) {
    return nameSpaceAliases;
  }
  let annotationIDs = Object.keys(annotations);
  for(let j = 0; j < annotationIDs.length; j++) {
    for(let k = 0; k < nameSpaceAliases.length; k++) {
      if(annotationIDs[j].startsWith(nameSpaceAliases[k])) {
        nameSpaceAliases.splice(k, 1);
        break;
      }
    }
  }
  return nameSpaceAliases;
}

function propertiesHaveNamespace(props, nameSpaceAliases) {
  let propKeys = Object.keys(props);
  for(let i = 0; i < propKeys.length; i++) {
    let prop = props[propKeys[i]];
    nameSpaceAliases = annotationsHaveNamespace(prop.Annotations, nameSpaceAliases);
    for(let k = 0; k < nameSpaceAliases.length; k++) {
      if(prop.Type.startsWith(nameSpaceAliases[k]) || prop.Type.startsWith('Collection('+nameSpaceAliases[k])) {
        nameSpaceAliases.splice(k, 1);
        break;
      }
    }
  }
  return nameSpaceAliases;
}

function entityTypesHaveActions(csdl) {
    let entityTypes = CSDL.search(csdl, 'EntityType');
    for(let i = 0; i < entityTypes.length; i++) {
      let entityType = entityTypes[i];
      if(entityType.Properties['Actions'] !== undefined) {
        continue;
      }
      //Exclude collction types...
      if(entityType.BaseType === 'Resource.v1_0_0.ResourceCollection') {
        continue;
      }
      if(EntityTypesWithNoActions.indexOf(entityType.Name) !== -1) {
        continue;
      }
      let sameNames = CSDL.search(csdl, 'EntityType', entityType.Name);
      if(sameNames.length > 1) {
        let found = false;
        for(let j = 0; j < sameNames.length; j++) {
          if(sameNames[j].Properties['Actions'] !== undefined) {
            found = true;
            break;
          }
        }
        if(found) {
          continue;
        }
      }
      throw new Error('Entity Type "'+entityType.Name+'" does not contain an Action');
    }
}

function navigationPropNullCheck(csdl) {
    let navProps = CSDL.search(csdl, 'NavigationProperty');
    for(let i = 0; i < navProps.length; i++) {
      let navProp = navProps[i];
      if(navProp.Type.startsWith('Collection(') && navProp.Nullable !== undefined) {
        throw new Error('NavigationProperty "'+navProp.Name+'" is Nullable and should not be!');
      }
    }
}

function schemaVersionCheck(csdl, publishedSchemas) {
  let schemas = CSDL.search(csdl, 'Schema');
  for(let i = 0; i < schemas.length; i++) {
    let schema = schemas[i];
    if(schema._Name.indexOf('.v') === -1) {
      //Unversioned schema skip...
      continue;
    }
    let parts = schema._Name.split('.');
    let publishedEntry = publishedSchemas[parts[0]];
    if(publishedEntry === undefined) {
      //No published schemas of this namespace... Skip...
      continue;
    }
    checkVersionInPublishedList(parts[1], publishedEntry, schema._Name);
  }
}

function checkVersionInPublishedList(version, publishedList, schemaName) {
  let parts = version.split('_');
  if(publishedList[parts[0]] === undefined) {
    //Major version not present... TODO
    throw new Error('Test does not currently handle major version change detected in Schema '+schemaName);
  }
  let major = publishedList[parts[0]];
  if(major[parts[1]] === undefined) {
    //Minor version not present...
    if(parts[2] !== '0') {
      throw new Error('Schema version '+parts[0]+'_'+parts[1]+' is not published, but minor version other than 0 exists in '+schemaName);
    }
    let prevMinor = ((parts[1]*1)-1)+'';
    if(major[prevMinor] === undefined) {
      throw new Error('Schema version '+parts[0]+'_'+parts[1]+' is not published and neither is '+parts[0]+'_'+prevMinor+' in '+schemaName);
    }
    return;
  }
  let minor = major[parts[1]];
  if(minor.indexOf(parts[2]) === -1) {
    let prevMaint = ((parts[2]*1)-1)+'';
    if(minor.indexOf(prevMaint) === -1) {
      throw new Error('Schema version '+parts[0]+'_'+parts[1]+'_'+parts[2]+' is not published and neither is '+parts[0]+'_'+parts[1]+'_'+prevMaint+' in '+schemaName);
    }
  }
}

function definitionsHaveAnnotations(csdl) {
  let entityTypes = CSDL.search(csdl, 'EntityType');
  for(let i = 0; i < entityTypes.length; i++) {
    let entityType = entityTypes[i];
    if(entityType.Abstract === true) {
      continue;
    }

    typeOrBaseTypesHaveAnnotations(entityType, ['OData.Description', 'OData.LongDescription'], entityType.Name, 'EntityType', csdl);
  }

  let complexTypes = CSDL.search(csdl, 'ComplexType');
  for(let i = 0; i < complexTypes.length; i++) {
    let complexType = complexTypes[i];
    if(complexType.Abstract === true) {
      continue;
    }

    typeOrBaseTypesHaveAnnotations(complexType, ['OData.Description', 'OData.LongDescription'], complexType.Name, 'ComplexType', csdl);
  }

  let properties = CSDL.search(csdl, 'Property');
  for(let i = 0; i < properties.length; i++) {
    let property = properties[i];
    if(property.Name === "Id" || property.Name === "Name" || property.Name === "Description") {
      // Special case for properties that reference TypeDefinitions; annotations get carried over in these cases, and these ones already have descriptions
      continue;
    }

    typeOrBaseTypesHaveAnnotations(property, ['OData.Description', 'OData.LongDescription'], property.Name, 'Property' , csdl);
  }

  let navProperties = CSDL.search(csdl, 'NavigationProperty');
  for(let i = 0; i < navProperties.length; i++) {
    let navProperty = navProperties[i];

    typeOrBaseTypesHaveAnnotations(navProperty, ['OData.Description', 'OData.LongDescription'], navProperty.Name, 'NavigationProperty', csdl);
  }

  let actions = CSDL.search(csdl, 'Action');
  for(let i = 0; i < actions.length; i++) {
    let action = actions[i];

    typeOrBaseTypesHaveAnnotations(action, ['OData.Description', 'OData.LongDescription'], action.Name, 'Action', csdl);
  }

  let parameters = CSDL.search(csdl, 'Parameter');
  for(let i = 0; i < parameters.length; i++) {
    let parameter = parameters[i];
    if(parameter.Type.endsWith('.Actions')) {
      // This is the binding parameter; no descriptions needed since it's not part of the client's payload
      continue;
    }

    typeOrBaseTypesHaveAnnotations(parameter, ['OData.Description', 'OData.LongDescription'], parameter.Name, 'Parameter', csdl);
  }
}

function typeOrBaseTypesHaveAnnotations(type, annotations, typeName, typeType, csdl) {
  let unfound = annotations;
  for(let i = 0; i < annotations.length; i++) {
    if(type.Annotations[annotations[i]] === undefined) {
      if(type.BaseType === undefined) {
        throw new Error(typeType+' "'+typeName+'" lacks an '+annotations[i]+' Annotation!');
      }
    }
    else {
      unfound = unfound.filter(function(value, index, arr){ return (value !== annotations[i]);});
    }
  }
  if(unfound.length > 0) {
    let baseType = CSDL.findByType(csdl || {_options: options}, type.BaseType);
    typeOrBaseTypesHaveAnnotations(baseType, unfound, typeName, typeType, csdl);
  }
}

function validCSDLTypeInMockup(json, file) { 
  if(json["$schema"] !== undefined) {
    //Ignore JSON schema files
    return;
  }
  if(json['@odata.type'] === undefined) {
    if(json['v1'] !== undefined) {
      /*This is probably a root json, ignore it*/
      return;
    }
    if(json['@odata.context'] === '/redfish/v1/$metadata') {
      /*This is an Odata service doc, ignrore it*/
      return;
    }
    throw new Error('No Type defined!');
  }
  let type = json['@odata.type'].substring(1);
  let CSDLType = CSDL.findByType({_options: options}, type);
  if(CSDLType === null) {
    throw new Error('Could not locate type '+type);
  }
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
      throw new Error('Unknown property "'+propName+'" in type '+type);
    }
    if(CSDLProperty.Type.startsWith('Collection(')) {
      if(!Array.isArray(json[propName])) {
        throw new Error('Property "'+propName+'" is a collection, but the value in the mockup is not a valid JSON array.');
      }
      let typeLookup = CSDLProperty.Type.substring(11);
      typeLookup = typeLookup.substring(0, typeLookup.length-1);
      let namespaceIndex = typeLookup.indexOf('.');
      if(namespaceIndex === -1) {
        throw new Error('Cannot get namespace of "' + typeLookup + '"');
      }
      let namespace = typeLookup.substring(0, namespaceIndex);
      if(namespace === '') {
        throw new Error('Cannot get namespace of "' + typeLookup + '"');
      }
      if(namespace === 'Resource' || namespace === 'IPAddresses' || namespace === 'VLanNetworkInterface' || namespace === 'Schedule' || namespace === 'PCIeDevice' || namespace === 'Message') {
        let typeNameIndex = typeLookup.lastIndexOf('.');
        if(typeNameIndex === -1) {
          throw new Error('Cannot get type of "' + typeLookup + '"');
        }
        let typeName = typeLookup.substring(typeNameIndex+1);
        if(namespace === '') {
          throw new Error('Cannot get type of "' + typeLookup + '"');
        }
        typeLookup = getLatestTypeVersion(typeLookup, namespace, typeName, 1, 15)
      }
      let propType = CSDL.findByType({_options: options}, typeLookup);
      if(propType === null || propType === undefined) {
        throw new Error('Cannot locate property type '+typeLookup+'.');
      }
      for(let i = 0; i < json[propName].length; i++) {
        let propValue = json[propName][i];
        if(typeof propType === 'string') {
          simpleTypeCheck(propType, propValue, CSDLProperty, propName);
        }
        else {
          if(propType.constructor.name === 'EnumType') {
            enumTypeCheck(propType, propValue, CSDLProperty, propName);
          }
          else if(propType.constructor.name === 'TypeDefinition') {
            simpleTypeCheck(propType.UnderlyingType, propValue, CSDLProperty, propName)
          }
          else if(propType.constructor.name === 'ComplexType') {
            if(typeof propValue !== 'object') {
              throw new Error('Property "'+propName+'" is a ComplexType, but the value in the mockup is not a valid JSON object.');
            }
            //Ignore Oem and Actions types...
            if(propType.Name === 'Actions') {
              validateActions(propValue);
            }
            else if(propType.Name !== 'Oem') {
              complexTypeCheck(propType, propValue, propName+'['+i.toString()+']', type);
            }
          }
          else if(propType.constructor.name === 'EntityType') {
            if(typeof propValue !== 'object') {
              throw new Error('Property "'+propName+'" is an EntityType, but the value in the mockup is not a valid JSON object.');
            }
            //This should be a NavigationProperty pointing to an EntityType, make sure it is a link...
            if(propValue['@odata.id'] === undefined) {
              if(!file.includes('non-resource-examples')) {
                throw new Error('Property "'+propName+'" is an EntityType, but the value does not contain an @odata.id!');
              }
            }
          }
        }
      }
    }
    else {
      let typeLookup = CSDLProperty.Type
      let namespaceIndex = typeLookup.indexOf('.');
      if(namespaceIndex === -1) {
        throw new Error('Cannot get namespace of "' + typeLookup + '"');
      }
      let namespace = typeLookup.substring(0, namespaceIndex);
      if(namespace === '') {
        throw new Error('Cannot get namespace of "' + typeLookup + '"');
      }
      if(namespace === 'Resource' || namespace === 'IPAddresses' || namespace === 'VLanNetworkInterface' || namespace === 'Schedule' || namespace === 'PCIeDevice') {
        let typeNameIndex = typeLookup.lastIndexOf('.');
        if(typeNameIndex === -1) {
          throw new Error('Cannot get type of "' + typeLookup + '"');
        }
        let typeName = typeLookup.substring(typeNameIndex+1);
        if(namespace === '') {
          throw new Error('Cannot get type of "' + typeLookup + '"');
        }
        typeLookup = getLatestTypeVersion(typeLookup, namespace, typeName, 1, 15)
      }
      let propType = CSDL.findByType({_options: options}, typeLookup);
      let propValue = json[propName];
      if(propType === null || propType === undefined) {
        throw new Error('Cannot locate property type '+typeLookup+'.');
      }
      else if(typeof propType === 'string') {
        simpleTypeCheck(propType, propValue, CSDLProperty, propName);
      }
      else {
        if(propType.constructor.name === 'EnumType') {
          enumTypeCheck(propType, propValue, CSDLProperty, propName);
        }
        else if(propType.constructor.name === 'TypeDefinition') {
          simpleTypeCheck(propType.UnderlyingType, propValue, CSDLProperty, propName)
        }
        else if(propType.constructor.name === 'ComplexType') {
          if(typeof propValue !== 'object') {
            throw new Error('Property "'+propName+'" is a ComplexType, but the value in the mockup is not a valid JSON object.');
          }
          //Ignore Oem and Actions types...
          if(propType.Name === 'Actions') {
            validateActions(propValue);
          }
          else if(propType.Name !== 'Oem') {
            complexTypeCheck(propType, propValue, propName, type);
          }
        }
        else if(propType.constructor.name === 'EntityType') {
          if(typeof propValue !== 'object') {
            throw new Error('Property "'+propName+'" is an EntityType, but the value in the mockup is not a valid JSON object.');
          }
          //This should be a NavigationProperty pointing to an EntityType, make sure it is a link...
          if(propValue['@odata.id'] === undefined) {
            throw new Error('Property "'+propName+'" is an EntityType, but the value does not contain an @odata.id!');
          }
        }
      }
    }
  }
}

function getLatestTypeVersion(defaultType, namespace, type, majorVersion, minorVersion) {
  let schemas = options.cache.getSchemasThatStartWith(namespace+'.');
  schemas.sort((a, b) => {
    if(a._Name > b._Name) {
      return -1;
    }
    else if(a._Name < b._Name) {
      return 1;
    }
    return 0;
  });
  for(let i = 0; i < schemas.length; i++) {
    if(schemas[i][type] !== undefined) {
      return schemas[i]._Name+'.'+type;
    }
  }
  return defaultType;
}

function complexTypeCheck(propType, propValue, propName, type) {
  let realType = propType;
  if(propValue['@odata.type'] === undefined) {
    //Need to calculate the odata.type value...
    realType = constructODataType(propType, type);
  }
  else {
    realType = CSDL.findByType({_options: options}, propValue['@odata.type'].substring(1));
  }
  for(let childPropName in propValue) {
    if(childPropName[0] === '@') {
      continue;
    }
    if(childPropName.indexOf('@Redfish.AllowableValues') !== -1) {
      //TODO Make sure all AllowableValues are valid
    }
    else if(childPropName.indexOf('@Redfish.') !== -1) {
      //TODO Check other annotations; for now, just let them pass
    }
    else {
      checkProperty(childPropName, realType, propValue[childPropName], type, propName);
    }
  }
}

function getNextLowerVersion(version) {
  let versionParts = version.split('_');
  if(versionParts[2] === '0') {
    if(versionParts[1] === '0') {
      return 'v1_0_0';
    }
    else {
      versionParts[1] = ((versionParts[1]*1)-1)+'';
    }
  }
  else {
    versionParts[2] = ((versionParts[2]*1)-1)+'';
  }
  return versionParts.join('_');
}

function constructODataType(propType, type) {
  let index = type.lastIndexOf('.');
  if(index === -1) {
    throw new Error('');
  }
  let parentNamespace = type.substring(0, index);
  if(parentNamespace === '') {
    throw new Error('');
  }
  let testType = CSDL.findByType({_options: options}, parentNamespace+'.'+propType.Name);
  if(testType !== null && testType !== undefined) {
    return testType;
  }
  index = parentNamespace.lastIndexOf('.');
  let version = parentNamespace.substring(index+1);
  if(version === 'v1_0_0') {
    return propType;
  }
  parentNamespace = parentNamespace.substring(0, index);
  return constructODataType(propType, parentNamespace+'.'+getNextLowerVersion(version)+'.');
}

function simpleTypeCheck(propType, propValue, CSDLProperty, propName) {
  switch(propType) {
    case 'Edm.Boolean':
      if(typeof propValue !== 'boolean' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.Boolean, but the value in the mockup is not a valid JSON boolean.');
      }
      break;
    case 'Edm.DateTimeOffset':
      if(typeof propValue !== 'string' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.DateTimeOffset, but the value in the mockup is not a valid JSON string.');
      }
      if(propValue.match('[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]') === null) {
        throw new Error('Property "'+propName+'" is an Edm.DateTimeOffset, but the value in the mockup does not conform to the correct syntax.');
      }
      break;
    case 'Edm.Decimal':
    case 'Edm.Double':
      if(typeof propValue !== 'number' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an floating point type, but the value in the mockup is not a valid JSON number.');
      }
      break;
    case 'Edm.Guid':
      if(typeof propValue !== 'string' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.Guid, but the value in the mockup is not a valid JSON string.');
      }
      if(propValue.match('([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})') === null) {
        throw new Error('Property "'+propName+'" is an Edm.Guid, but the value in the mockup does not conform to the correct syntax.');
      }
      break;
    case 'Edm.Int64':
      if(typeof propValue !== 'number' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.Int64, but the value in the mockup is not a valid JSON number.');
      }
      if(!Number.isInteger(propValue) && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.Int64, but the value in the mockup is not an integer.');
      }
      break;
    case 'Edm.String':
      if(typeof propValue !== 'string' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.String, but the value in the mockup is not a valid JSON string.');
      }
      if(CSDLProperty.Annotations['Validation.Pattern'] && propValue !== null) {
        let regex = CSDLProperty.Annotations['Validation.Pattern'].String;
        if(regex[0] === '/') {
          regex = regex.substring(1);
        }
        if(propValue.match(regex) === null) {
          throw new Error('Property "'+propName+'" is an Edm.String, but the value in the mockup does not match the pattern.');
        }
      }
      break;
    case 'Edm.Duration':
      if(typeof propValue !== 'string' && propValue !== null) {
        throw new Error('Property "'+propName+'" is an Edm.Duration, but the value in the mockup is not a valid JSON string.');
      }
      break;
    default:
      throw new Error('Property "'+propName+'" is type "'+propType+'" which is not allowed by the Redfish spec.');
  }
}

function enumTypeCheck(propType, propValue, CSDLProperty, propName) {
  if(typeof propValue !== 'string' && propValue !== null) {
    throw new Error('Property "'+propName+'" is an EnumType, but the value in the mockup is not a valid JSON string.');
  }
  if(propValue !== null && propType.Members[propValue] === undefined) {
    throw new Error('Property "'+propName+'" is an EnumType, but the value in the mockup "'+propValue+'" is not a valid member of the enum.');
  }
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

function checkProperty(propName, CSDLType, propValue, parentType, parentPropName) {
  let CSDLProperty = getCSDLProperty(propName, CSDLType);
  if(CSDLProperty === undefined) {
    if((CSDLType.Annotations['OData.AdditionalProperties'] !== undefined && CSDLType.Annotations['OData.AdditionalProperties'].Bool === true) ||
        CSDLType.Annotations['Redfish.DynamicPropertyPatterns'] !== undefined) {
      return;
    }
    else {
      let string = 'Unknown property "'+propName+'" in type '+CSDLType.Name;
      if(parentPropName) {
        string+=' under parent property "'+parentPropName+'"';
      }
      throw new Error(string);
    }
  }
  if(CSDLProperty.Type.startsWith('Collection(')) {
    if(!Array.isArray(propValue)) {
      throw new Error('Property "'+propName+'" is a collection, but the value in the mockup is not a valid JSON array.');
    }
    //TODO do a check for each entry in the array...
  }
  else {
    let typeLookup = CSDLProperty.Type
    let namespaceIndex = typeLookup.indexOf('.');
    if(namespaceIndex === -1) {
      throw new Error('Cannot get namespace of "' + typeLookup + '"');
    }
    let namespace = typeLookup.substring(0, namespaceIndex);
    if(namespace === '') {
      throw new Error('Cannot get namespace of "' + typeLookup + '"');
    }
    if(namespace === 'Resource' || namespace === 'IPAddresses' || namespace === 'VLanNetworkInterface' || namespace === 'Schedule' || namespace === 'PCIeDevice') {
      let typeNameIndex = typeLookup.lastIndexOf('.');
      if(typeNameIndex === -1) {
        throw new Error('Cannot get type of "' + typeLookup + '"');
      }
      let typeName = typeLookup.substring(typeNameIndex+1);
      if(namespace === '') {
        throw new Error('Cannot get type of "' + typeLookup + '"');
      }
      typeLookup = getLatestTypeVersion(typeLookup, namespace, typeName, 1, 15)
    }
    let propType = CSDL.findByType({_options: options}, typeLookup);
    if(typeof propType === 'string') {
      simpleTypeCheck(propType, propValue, CSDLProperty, propName);
    }
    else if(propType.constructor.name === 'EnumType') {
      enumTypeCheck(propType, propValue, CSDLProperty, propName);
    }
    else if(propType.constructor.name === 'TypeDefinition') {
      simpleTypeCheck(propType.UnderlyingType, propValue, CSDLProperty, propName)
    }
    else if(propType.constructor.name === 'ComplexType') {
      if(typeof propValue !== 'object') {
        throw new Error('Property "'+propName+'" is a ComplexType, but the value in the mockup is not a valid JSON object.');
      }
      //Ignore Oem and Actions types...
      if(propType.Name !== 'Oem' && propType.Name !== 'Actions') {
        complexTypeCheck(propType, propValue, propName, parentType);
      }
    }
    else if(propType.constructor.name === 'EntityType') {
      if(Array.isArray(propValue) || typeof propValue !== 'object') {
        throw new Error('Property "'+propName+'" is an EntityType, but the value in the mockup is not a valid JSON object.');
      }
      //This should be a NavigationProperty pointing to an EntityType, make sure it is a link...
      if(propValue['@odata.id'] === undefined && Object.keys(propValue).length > 0) {
        throw new Error('Property "'+propName+'" is an EntityType, but the value does not contain an @odata.id!');
      }
    }
  }
}

function validateActions(actions) {
 for(let propName in actions) {
   if(propName === 'Oem') {
     continue;
   }
   if(propName === '@odata.type') {
     continue;
   }
   let actionType = CSDL.findByType({_options: options}, propName.substring(1));
   if(actionType === undefined || actionType === null) {
     throw new Error('Action "'+propName+'" is not present in the CSDL');
   }
   if(actionType.constructor.name !== 'Action') {
     throw new Error('Action "'+propName+'" is not an action in the CSDL');
   }
   let action = actions[propName];
   if(action['Target'] !== undefined) {
     throw new Error('Action "'+propName+'" has invalid property "Target"');
   }
 } 
}

function schemaOwningEntityCheck(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  for(let i = 0; i < schemas.length; i++) {
    let owningEntity = CSDL.search(schemas[i], 'Annotation', 'Redfish.OwningEntity');
    if(owningEntity.length === 0) {
      let owningEntity = CSDL.search(schemas[i], 'Annotation', 'RedfishExtensions.v1_0_0.OwningEntity');
      if(owningEntity.length === 0) {
        throw new Error('Namespace '+schemas[i]._Name+' lacks OwningEntity!');
      }
    }
  }
}

function schemaReleaseCheck(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  for(let i = 0; i < schemas.length; i++) {
    let release = CSDL.search(schemas[i], 'Annotation', 'Redfish.Release');
    if(NamespacesWithReleaseTerm.indexOf(schemas[i]._Name) !== -1) {
      // These namespaces do not follow the normal rules and require the Release term
      if(release.length === 0) {
        throw new Error('Namespace '+schemas[i]._Name+' lacks Release term!');
      }    
    }
    else if(NamespacesWithoutReleaseTerm.indexOf(schemas[i]._Name) !== -1) {
      // These namespaces do not follow the normal rules and do not use the Release term
      if(release.length !== 0) {
        throw new Error('Namespace '+schemas[i]._Name+' contains an unexpected Release term!');
      }    
    }
    else {
      // All other namespaces require the Release term if it's versioned and non-errata
      if((release.length === 0) && schemas[i]._Name.endsWith('_0')) {
        throw new Error('Namespace '+schemas[i]._Name+' lacks Release term!');
      }
      if((release.length !== 0) && !schemas[i]._Name.endsWith('_0')) {
        throw new Error('Namespace '+schemas[i]._Name+' contains an unexpected Release term!');
      }
    }
  }
}
/* vim: set tabstop=2 shiftwidth=2 expandtab: */
