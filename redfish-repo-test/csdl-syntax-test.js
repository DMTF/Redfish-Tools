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

var skipVersionTest = false;
if(config.has('Redfish.BypassVersionCheck')) {
  skipVersionTest = config.get('Redfish.BypassVersionCheck');
}

var skipCheckSchemaList = [];
if(config.has('Redfish.ExternalOwnedSchemas')) {
  skipCheckSchemaList = config.get('Redfish.ExternalOwnedSchemas');
}

/***************** Allow lists ******************************/
//Units that don't exist in UCUM
const unitsAllowList = ['RPM', 'V.A', '{tot}', '1/s/TBy', 'W.h', 'A.h', 'kV.A.h', '{rev}/min'];
//Enumeration Member names that are non-Pascal Cased
let NonPascalCaseEnumAllowList   = ['iSCSI', 'iQN', 'cSFP', 'FC_WWN', 'TX_RX', 'EIA_310', 'string', 'number', 'NVDIMM_N',
                                    'NVDIMM_F', 'NVDIMM_P', 'DDR4_SDRAM', 'DDR4E_SDRAM', 'LPDDR4_SDRAM', 'DDR3_SDRAM',
                                    'LPDDR3_SDRAM', 'DDR2_SDRAM', 'DDR2_SDRAM_FB_DIMM', 'DDR2_SDRAM_FB_DIMM_PROBE',
                                    'DDR_SGRAM', 'DDR_SDRAM', 'SO_DIMM', 'Mini_RDIMM', 'Mini_UDIMM', 'SO_RDIMM_72b',
                                    'SO_UDIMM_72b', 'SO_DIMM_16b', 'SO_DIMM_32b', 'TPM1_2', 'TPM2_0', 'TCM1_0', 'iWARP',
                                    'RSA_2048Bit', 'RSA_3072Bit', 'RSA_4096Bit', 'EC_P256', 'EC_P384', 'EC_P521',
                                    'EC_X25519', 'EC_X448', 'EC_Ed25519', 'EC_Ed448', 'NEMA_5_15P', 'NEMA_L5_15P',
                                    'NEMA_5_20P', 'NEMA_L5_20P', 'NEMA_L5_30P', 'NEMA_6_15P', 'NEMA_L6_15P',
                                    'NEMA_6_20P', 'NEMA_L6_20P', 'NEMA_L6_30P', 'NEMA_L14_20P', 'NEMA_L14_30P',
                                    'NEMA_L15_20P', 'NEMA_L15_30P', 'NEMA_L21_20P', 'NEMA_L21_30P', 'NEMA_L22_20P',
                                    'NEMA_L22_30P', 'California_CS8265', 'California_CS8365', 'IEC_60320_C14',
                                    'IEC_60320_C13', 'IEC_60320_C19', 'IEC_60320_C20', 'IEC_60309_316P6', 'IEC_60309_332P6',
                                    'IEC_60309_363P6', 'IEC_60309_516P6', 'IEC_60309_532P6', 'IEC_60309_563P6',
                                    'IEC_60309_460P9', 'IEC_60309_560P9', 'Field_208V_3P4W_60A', 'Field_400V_3P5W_32A',
                                    'NEMA_5_15R', 'NEMA_5_20R', 'NEMA_L5_20R', 'NEMA_L5_30R', 'NEMA_L6_20R',
                                    'NEMA_L6_30R', 'CEE_7_Type_E', 'CEE_7_Type_F', 'SEV_1011_TYPE_12',
                                    'SEV_1011_TYPE_23', 'BS_1363_Type_G', 'TLS_SSL', 'CRAM_MD5', 'HMAC_MD5', 'HMAC_SHA96',
                                    'CBC_DES', 'CFB128_AES128', 'EC_X25519', 'EC_X448', 'EC_Ed25519', 'EC_Ed448',
                                    'NFSv4_0', 'NFSv4_1', 'SMBv3_0', 'SMBv2_1', 'SMBv2_0', 'SMBv3_1_1',
                                    'SMBv3_0_2', 'Bits_0', 'Bits_128', 'Bits_192', 'Bits_256', 'Bits_112',
                                    'ISO8859_1', 'UTF_8', 'UTF_16', 'UCS_2', 'RPCSEC_GSS', 'HMAC128_SHA224',
                                    'HMAC192_SHA256', 'HMAC256_SHA384', 'HMAC384_SHA512', 'TLS_PSK', 'TLS_AES_128_GCM_SHA256',
                                    'TLS_AES_256_GCM_SHA384'];
//Properties names that are non-Pascal Cased
const NonPascalCasePropertyWhiteList = ['iSCSIBoot'];
//Properties that have units but don't have the unit names in them
const PropertyNamesWithoutCorrectUnits = ['AccountLockoutCounterResetAfter', 'AccountLockoutDuration', 'Accuracy', 'AdjustedMaxAllowableOperatingValue', 'AdjustedMinAllowableOperatingValue', 'CapableSpeedGbs', 'Duration',
                                          'Latitude', 'Longitude', 'LowerThresholdCritical', 'LowerThresholdFatal', 'LowerThresholdNonCritical', 'LowerThresholdUser', 'MaxAllowableOperatingValue', 'MaxBytesPerSecond',
                                          'MaxFrameSize', 'MaxIOOperationsPerSecondPerTerabyte', 'MaxReadingRange', 'MaxReadingRangeTemp', 'MaxSamplePeriod', 'MaxSupportedBytesPerSecond', 'MinAllowableOperatingValue',
                                          'MinReadingRange', 'MinReadingRangeTemp', 'MinSamplePeriod', 'NegotiatedSpeedGbs', 'NonIORequests', 'OperatingSpeedMhz', 'PercentComplete', 'PercentOfData', 'PercentOfIOPS',
                                          'PercentSynced', 'PercentageComplete', 'ReactiveVAR', 'ReadHitIORequests', 'ReadIORequests', 'RecoveryTimeObjective', 'SessionTimeout', 'UpperThresholdCritical',
                                          'UpperThresholdFatal', 'UpperThresholdNonCritical', 'UpperThresholdUser', 'WhenActivated', 'WhenDeactivated', 'WhenEstablished', 'WhenSuspended', 'WhenSynchronized',
                                          'WriteHitIORequests', 'WriteIORequests','NumberLBAFormats','ReactivekVARh'];
//Values that have other acceptable Unit nomenclature
const AlternativeUnitNames = {'mm': 'Mm', 'kg': 'Kg', 'A': 'Amps', 'Cel': 'Celsius', 'Hz': 'Hz', 'GiBy': 'GiB', 'Gbit/s': 'Gbps', 'KiBy': 'KiBytes', 'Mbit/s': 'Mbps', 'MiBy': 'MiB', 'min': 'Min', 'MHz': 'MHz', 'ms': 'Ms',
                              '%': 'Percentage', 'V': 'Voltage', 'V.A': 'VA', 'W': 'Wattage', '[IO]/s': 'IOPS', 'mA': 'MilliAmps', 'W.h': 'WattHours', 'A.h': 'AmpHours', 'kV.A.h': 'kVAh', '{rev}/min': 'RPM', 'KiBy': 'KiB'};

const ODataSchemaFileList = [ 'Org.OData.Core.V1.xml', 'Org.OData.Capabilities.V1.xml', 'Org.OData.Measures.V1.xml' ];
const SwordfishSchemaFileList = [ 'Capacity_v1.xml',
                                  'CapacitySourceCollection_v1.xml',
                                  'ClassOfService_v1.xml',
                                  'ClassOfServiceCollection_v1.xml', 'ConsistencyGroup_v1.xml', 'ConsistencyGroupCollection_v1.xml',
                                  'DataProtectionLineOfService_v1.xml', 'DataProtectionLoSCapabilities_v1.xml', 'DataSecurityLineOfService_v1.xml',
                                  'DataSecurityLoSCapabilities_v1.xml', 'DataStorageLineOfService_v1.xml', 'DataStorageLoSCapabilities_v1.xml',
                                  'FeaturesRegistry_v1.xml', 'FeaturesRegistryCollection_v1.xml',
                                  'FeaturesRegistryService_v1.xml', 'FileShare_v1.xml', 'FileShareCollection_v1.xml', 'FileSystem_v1.xml', 'FileSystemCollection_v1.xml',
                                  'HostedStorageServices_v1.xml',
                                  'IOConnectivityLineOfService_v1.xml', 'IOConnectivityLoSCapabilities_v1.xml', 'IOPerformanceLineOfService_v1.xml',
                                  'IOPerformanceLoSCapabilities_v1.xml', 'IOStatistics_v1.xml', 'LineOfService_v1.xml', 'LineOfServiceCollection_v1.xml',
                                  'NVMeDomain_v1.xml',
                                  'NVMeDomainCollection_v1.xml',
                                  'SpareResourceSet_v1.xml', 'StorageGroup_v1.xml', 'StorageGroupCollection_v1.xml', 'StoragePool_v1.xml', 'StoragePoolCollection_v1.xml',
                                  'StorageReplicaInfo_v1.xml', 'StorageServiceCollection_v1.xml', 'StorageSystemCollection_v1.xml', 'StorageService_v1.xml', 'Volume_v1.xml',
                                  'VolumeCollection_v1.xml' ];
const ContosoSchemaFileList = [ 'ContosoAccountService_v1.xml', 'ContosoServiceRoot_v1.xml', 'TurboencabulatorService_v1.xml' ];
const EntityTypesWithNoActions = [ 'ServiceRoot', 'ItemOrCollection', 'Item', 'ReferenceableMember', 'Resource', 'ResourceCollection', 'ActionInfo', 'TurboencabulatorService', 'LineOfService' ];
const WhiteListMockupLinks = [ "https://10.23.11.12/redfish/v1/StorageServices/X/StorageGroups/10", "https://10.23.11.12/redfish/v1/Systems/FileServer/StorageServices/X/StorageGroups/10", "https://10.1.1.13/redfish/v1/StorageServices/A/Volume/ABC", "https://10.1.22.18/redfish/v1/StorageServices/X/Volume/A1x2", "https://10.1.22.18/redfish/v1/StorageServices/X/Volumes/A1x2", "http://hf.contoso.org/redfish/v1/Systems/FileServer/StorageServices/2/StorageGroups/2","https://10.12.1.12/redfish/v1/StorageServices/2/Volumes/5"];
const OldRegistries = ['Base.1.0.0.json', 'ResourceEvent.1.0.0.json', 'TaskEvent.1.0.0.json', 'Redfish_1.0.1_PrivilegeRegistry.json', 'Redfish_1.0.2_PrivilegeRegistry.json'];
const NamespacesWithReleaseTerm = ['PhysicalContext', 'Protocol' ];
const NamespacesWithoutReleaseTerm = ['RedfishExtensions.v1_0_0', 'Validation.v1_0_0', 'RedfishError.v1_0_0', 'Schedule.v1_0_0', 'Schedule.v1_1_0' ];
const NamespacesWithGlobalTypes = ['Resource', 'IPAddresses', 'VLanNetworkInterface', 'Schedule', 'PCIeDevice', 'Message', 'Redundancy', 'Manifest' ]
const OverRideFiles = ['http://redfish.dmtf.org/schemas/swordfish/v1/Volume_v1.xml'];
const NoUriAllowList = ['ActionInfo', 'MessageRegistry', 'AttributeRegistry', 'PrivilegeRegistry', 'FeaturesRegistry', 'Event'];
const PluralSchemaAllowList = ['ChassisCollection', 'ElectricalBusCollection', 'MemoryChunksCollection', 'TriggersCollection'];
let   PluralEntitiesAllowList = ['Actions', 'AlarmTrips', 'Attributes', 'Bios', 'BootProgress', 'CertificateLocations', 'Chassis', 'CompositionStatus', 'CurrentSensors', 
                                 'DeepOperations', 'ElectricalBus', 'EnergySensors', 'HostedServices', 'HttpPushUriOptions', 'IPTransportDetails', 'Links', 'OemActions', 'MultiplePaths', 
                                 'NVMeControllerAttributes', 'NVMeSMARTCriticalWarnings', 'Parameters', 'PCIeSlots', 'PowerSensors', 'Rates', 'RedfishErrorContents', 
                                 'RegistryEntries', 'ResourceBlockLimits', 'Status', 'Thresholds', 'UpdateParameters', 'VoltageSensors'];
//All of the entries in the following object were errors and should only be allowed in the file they are currently present in
const PluralEntitiesBadAllow = {
  'AttributeRegistry_v1.xml': ['Dependencies', 'Menus', 'SupportedSystems'],
  'ComputerSystem_v1.xml': ['TrustedModules'],
  'Drive_v1.xml': ['Operations'],
  'MemoryChunks_v1.xml': ['MemoryChunks'],
  'NetworkAdapter_v1.xml': ['Controllers'],
  'NetworkDeviceFunction_v1.xml': ['BootTargets'],
  'StorageController_v1.xml': ['ANACharacteristics'],
  'Triggers_v1.xml': ['Triggers']
};
/************************************************************/

if(config.has('Redfish.ExtraPluralAllowed')) {
  PluralEntitiesAllowList = PluralEntitiesAllowList.concat(config.get('Redfish.ExtraPluralAllowed'));
}
if(config.has('Redfish.ExtraNonPascalEnumAllowed')) {
  NonPascalCaseEnumAllowList = NonPascalCaseEnumAllowList.concat(config.get('Redfish.ExtraNonPascalEnumAllowed'));
}


describe('CSDL Tests', () => {
  const files = glob.sync(config.get('Redfish.CSDLFilePath'));
  let publishedSchemas = {};
  let overrideCSDLs = [];
  before(function(done){
    this.timeout(60000);
    let promise = csdlTestSetup();
    promise.then((res) => {
      publishedSchemas = res[0];
      overrideCSDLs = res.slice(1);
      done();
    }).catch((err) => {
      done(err);
    });
  });

  files.forEach((file) => {
    describe(file, () => {
      let fileName = file.substring(file.lastIndexOf('/')+1);
      let csdl = null;
      let isYang = false;
      before(function(done) {
        this.timeout(120000);
        CSDL.parseMetadataFile(file, options, (err, data) => {
          if(err) {
            throw err;
          }
          csdl = data;
          isYang = ifYangSchema(data);
          done();
        });
      });
      it('Valid Syntax', () => {
        assert.notEqual(csdl, null);
      });
      if(skipCheckSchemaList.indexOf(fileName) !== -1) {
        return;
      }
      //These tests are only valid for new format CSDL...
      if(file.indexOf('_v') !== -1) {
        it('Units are valid', () => {validUnitsTest(csdl);});
      }
      //Permissions checks are not valid on this file...
      if(file.includes('RedfishExtensions_v1.xml') === false) {
        it('Has Permission Annotations', () => {permissionsCheck(csdl);});
        it('Complex Types Should Not Have Permissions', () => {complexTypesPermissions(csdl);});
      }
      it('Descriptions have trailing periods', () => {if (!isYang) descriptionPeriodCheck(csdl);});
      if(!config.has('Redfish.SwordfishTest')) {
        //it('Long Descriptions do not contain may', () => {if (!isYang) descriptionMayCheck(csdl);});
        it('Long Descriptions do not contain must', () => {if (!isYang) descriptionMustCheck(csdl);});
      }
      it('No Empty Schema Tags', () => {checkForEmptySchemas(csdl);});
      it('No plural Schemas', () => {noPluralSchemas(csdl);});
      it('No plural Entities', () => {noPluralEntities(csdl, fileName);});
      it('BaseTypes are valid', () => {checkBaseTypes(csdl);});
      it('Types are not repeated', () => {repeatedTypeNameCheck(csdl);});
      it('All Annotation Terms are valid', () => {checkAnnotationTerms(csdl);});
      if (!file.includes('RedfishYangExtensions')) {
        it('Enum Members are valid names', () => {if (!isYang) checkEnumMembers(csdl);});
      }
      //Don't do Pascal Case checking in the RedfishErrors file or Yang files; the properties are dictated by the OData spec
      if(file.includes('RedfishError_v1.xml') === false) {
        it('Properties are Pascal-cased', () => {if (!isYang) checkPropertiesPascalCased(csdl);});
      }
      it('Reference URIs are valid', () => {checkReferenceUris(csdl);});
      //skip the metadata mockup
      if(file.includes('$metadata') === false) {
        it('All References Used', () => {checkReferencesUsed(csdl);});
        it('All namespaces have OwningEntity', () => {schemaOwningEntityCheck(csdl);});
      }
      it('All EntityType defintions have Actions', () => {if (!isYang) entityTypesHaveActions(csdl);});
      it('NavigationProperties for Collections cannot be Nullable', () => {navigationPropNullCheck(csdl);});
      if(!skipVersionTest) {
        it('All new schemas are one version off published', () => {schemaVersionCheck(csdl, publishedSchemas);});
      }
      //Skip OEM extentions and metadata files
      if(ContosoSchemaFileList.indexOf(fileName) === -1 && fileName !== 'index.xml' && fileName !== 'Volume_v1.xml') {
        it('All definitions shall include Description and LongDescription annotations', () => {definitionsHaveAnnotations(csdl);});
        it('All versioned, non-errata namespaces have Release', () => {schemaReleaseCheck(csdl);});
        it('Resources specify capabilities', () => {resourcesSpecifyCapabilities(csdl);});
      }
      it('Property Names have correct units', () => {propertyNameUnitCheck(csdl);});
      it('Updatable restrictions for read/write props', () => {updatableReadWrite(csdl);});
      it('Insert restrictions only on collections', () => {insertCollections(csdl);});
      //Pendantic tests...
      if(process.env.PEDANTIC == 1) {
        it('Descriptions have double space after periods', () => {if (!isYang) descriptionSpaceCheck(csdl);});
      }
    });
  });
});

function ifYangSchema(csdl) {
    // Detect if a certain file is Yang.
    // Find all external schema references
    let references = CSDL.search(csdl, 'Reference', undefined, true);

    // Go through each reference
    for(let i = 0; i < references.length; i++) {
      if(references[i].Uri.includes('RedfishYang')) return true
    }
    return false
}

function csdlTestSetup() {
  let arr = [];
  if(config.has('Redfish.PublishedSchemaUri')) {
    arr.push(published.getPublishedSchemaVersionList(config.get('Redfish.PublishedSchemaUri')));
  }
  else {
    arr.push(published.getPublishedSchemaVersionList('http://redfish.dmtf.org/schemas/v1/'));
  }
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
  let extraCSDLs = [];
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
      if(config.has('Redfish.AdditionalCSDL')) {
        extraCSDLs = config.get('Redfish.AdditionalCSDL');
        let tmpArr = [];
        for(let i = 0; i < extraCSDLs.length; i++) {
          tmpArr.push(options.cache.getMetadata(extraCSDLs[i]));
        }
        tmpArr.push(options.cache.waitForCoherent());
        Promise.all(tmpArr).then(() => {
          done();
        }).catch((e) => {
          console.log(e);
          done();
        });
      }
      else {
        done();
      }
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
        assert.notEqual(json, null, 'JSON in file is not valid please run it through jsonlint to determine the actual fault');
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
            if(link.protocol !== null) {
              //Skip non-relative (i.e. external links)
              return;
            }
            let filepath = linkToFile[link.pathname];
            if(filepath === undefined && link.pathname.substr(link.pathname.length - 1) === '/') {
              //Try without the trailing slash...
              filepath = linkToFile[link.pathname.substr(0, link.pathname.length - 1)];
            }
            let refd = jsonCache[filepath];
            if(config.has('Redfish.SwordfishTest')) {
              if(WhiteListMockupLinks.includes(this.node) ) {
                return;
              }
            }
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
        //Ignore the paging file, the external error example, contrained composition request, and action requests/responses
        if(file.includes('$ref') === false && file.includes('/ExtErrorResp') === false && file.includes('/ConstrainedCompositionCapabilities') === false &&
           file.includes('Request.json') === false && file.includes('Response.json') === false && file.includes("-request") === false && file.includes("-response") === false) {
          it('Is Valid Type', function() {
            validCSDLTypeInMockup(json, file);
          });
          if(file.includes('non-resource-examples') === false && file.includes ('Contoso') === false) {
            it('Is Valid URI', function() {
              isValidURI(json, file);
            });
          }
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
      let json = null;
      try {
        json = JSON.parse(data.toString('utf-8'));
      } catch(err) {
        //reject(file+": JSON Error: "+err.message);
      }
      resolve({name: file, txt: data, json: json});
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
    if(unitsAllowList.indexOf(unitName) !== -1) {
      continue;
    }
    let pos = unitName.indexOf('/s');
    if(pos !== -1) {
      unitName = unitName.substring(0, pos);
    }
    if(Object.keys(ucum.units).includes(unitName)) {
      //Have unit, all good...
      return;
    }
    else if(Object.keys(ucum.prefixes).includes(unitName[0]) && Object.keys(ucum.units).includes(unitName.substring(1))) {
      //Have prefix and unit, all good...
      return;
    }
    else if(Object.keys(ucum.prefixes).includes(unitName.substring(0,2)) && Object.keys(ucum.units).includes(unitName.substring(2))) {
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

function descriptionMayCheck(csdl) {
  let long_descriptions = CSDL.search(csdl, 'Annotation', 'OData.LongDescription');
  if(long_descriptions.length !== 0) {
    for(let i = 0; i < long_descriptions.length; i++) {
      let str = long_descriptions[i].String;
      if(str.includes(" may ") || str.includes("May ")) {
        throw new Error('"' + str + '" includes the ISO unallowed word "may"!');
      }
    }
  }
}

function descriptionMustCheck(csdl) {
  let long_descriptions = CSDL.search(csdl, 'Annotation', 'OData.LongDescription');
  if(long_descriptions.length !== 0) {
    for(let i = 0; i < long_descriptions.length; i++) {
      let str = long_descriptions[i].String;
      if(str.includes(" must ") || str.includes("Must ")) {
        throw new Error('"' + str + '" includes the ISO unallowed word "must"!');
      }
    }
  }
}

function descriptionSpaceCheck(csdl) {
  let descriptions = CSDL.search(csdl, 'Annotation', 'OData.Description');
  if(descriptions.length !== 0) {
    for(let i = 0; i < descriptions.length; i++) {
      descriptionPeriodSpace(descriptions[i]);
    }
  }
  let long_descriptions = CSDL.search(csdl, 'Annotation', 'OData.LongDescription');
  if(long_descriptions.length !== 0) {
    for(let i = 0; i < long_descriptions.length; i++) {
      descriptionPeriodSpace(long_descriptions[i]);
    }
  }
}

function descriptionEndsInPeriod(desc) {
  let str = desc.String;
  if(str.slice(-1) !== '.') {
    throw new Error('"' + str + '" does not end in a period!');
  }
}

function descriptionPeriodSpace(desc) {
  let str = desc.String;
  const regex = /\D\.\s\S/g;
  if(str.match(regex)) {
    throw new Error('"' + str + '" is not double spaced!');
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

function noPluralSchemas(csdl) {
  let schemas = CSDL.search(csdl, 'Schema');
  if(schemas.length === 0) {
    return;
  }
  for(let i = 0; i < schemas.length; i++) {
    if(schemas[i]._Name.startsWith('Org.OData')) {
      continue;
    }
    if(PluralSchemaAllowList.indexOf(schemas[i]._Name) !== -1) {
      continue;
    }
    if(schemas[i]._Name.includes('sCollection') || schemas[i]._Name.includes('s_v1')) {
      throw new Error('Schema '+schemas[i]._Name+' is plural!');
    }
  }
}

function noPluralEntities(csdl, fileName) {
  let entityTypes =  CSDL.search(csdl, 'EntityType');
  for(let i = 0; i < entityTypes.length; i++) {
    entityPluralCheck(entityTypes[i], 'Entity', fileName);
  }
  let complexTypes =  CSDL.search(csdl, 'ComplexType');
  for(let i = 0; i < complexTypes.length; i++) {
    entityPluralCheck(complexTypes[i], 'Complex', fileName);
  }
}

function entityPluralCheck(entity, type, fileName) {
  if(PluralEntitiesAllowList.includes(entity.Name)) {
    return;
  }
  if(PluralEntitiesBadAllow[fileName] !== undefined && PluralEntitiesBadAllow[fileName].includes(entity.Name)) {
    return;
  }
  if(entity.Name.endsWith('Metrics') || entity.Name.endsWith('Settings') || entity.Name.endsWith('Capabilities') || 
     entity.Name.endsWith('Actions') || entity.Name.endsWith('Properties') || entity.Name.endsWith('Address') ||
     entity.Name.endsWith('Links')) {
    //Allow these endings regardless of the front part...
    return;
  }
  if(entity.Name.endsWith('s')) {
    throw new Error(type+' Type Name '+entity.Name+' is plural!');
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

function repeatedTypeNameCheck(csdl) {
  let obj = {};
  let schemas =  CSDL.search(csdl, 'Schema');
  for(let i = 0; i < schemas.length; i++) {
    schemaRepeatedTypeCheck(schemas[i], obj, csdl);
  }
}

function schemaRepeatedTypeCheck(schema, list, csdl) {
  let baseName = schema._Name.split('.')[0];
  if(baseName === 'Resource') {
    //Skip base types
    return;
  }
  if(list[baseName] === undefined) {
    list[baseName] = {};
  }
  for(const prop in schema) {
    if(prop === 'Annotations' || prop === '_Name') {
      continue;
    }
    //Exclude ServiceContainers...
    if(schema[prop].Name !== undefined && schema[prop].Name === 'ServiceContainer') {
      continue;
    }
    if(list[baseName][prop] === undefined) {
      list[baseName][prop] = getMostBasicType(schema[prop], csdl);
    } else {
      let baseType = getMostBasicType(schema[prop], csdl);
      if(list[baseName][prop] !== baseType) {
        throw new Error('Schema '+baseName+' contains two conflicting types named '+prop);
      }
    }
  }
}

function getMostBasicType(type, csdl) {
  if(type.BaseType === undefined) {
    return type;
  }
  if(type.BaseType.startsWith('Resource.')) {
    return type;
  }
  let baseType = CSDL.findByType(csdl, type.BaseType);
  if(baseType === null) {
    return type;
  }
  return getMostBasicType(baseType, csdl);
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
      if(keys[j].match(PascalRegex) === null && NonPascalCaseEnumAllowList.indexOf(keys[j]) === -1) {
        throw new Error('Enum member "'+keys[j]+'" of EnumType '+enums[i].Name+' is not Pascal Cased!');
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
      if(NamespacesWithGlobalTypes.indexOf(namespace) !== -1) {
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
            if(propValue['@odata.id'] === undefined && !('Redfish.ExcerptCopy' in CSDLProperty.Annotations)) {
              if(!file.includes('non-resource-examples') && !file.includes('Event-v1-example.json')) {
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
      if(NamespacesWithGlobalTypes.indexOf(namespace) !== -1) {
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
          if(propValue['@odata.id'] === undefined && !('Redfish.ExcerptCopy' in CSDLProperty.Annotations)) {
            throw new Error('Property "'+propName+'" is an EntityType, but the value does not contain an @odata.id!');
          }
        }
      }
    }
  }
}

function isValidURI(json, file) {
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
    return;
  }
  let type = json['@odata.type'].substring(1);
  let CSDLType = CSDL.findByType({_options: options}, type);
  if(CSDLType === null) {
    throw new Error('Could not locate type '+type);
  }
  CSDLType = getCSDLWithUri(CSDLType);
  if(CSDLType === null) {
    throw new Error('Unable to locate Uri annotation for type '+type);
  }
  if(CSDLType.Annotations === undefined || CSDLType.Annotations['Redfish.Uris'] === undefined) {
    return;
  }
  let id = json['@odata.id'];
  if(id === undefined) {
    return;
  }
  let uris = CSDLType.Annotations['Redfish.Uris'].Collection.Strings;
  let pass = false;
  let extra = [];
  for(let i = 0; i < uris.length; i++) {
    let ret = isIdInUri(id, uris[i]);
    if(ret === true) {
      pass = true;
      break;
    }
    if(ret !== false) {
      extra.push(ret);
    }
  }
  if(pass === false) {
    let msg = 'Unable to locate URI for id '+id+' that matches Uri pattern for type '+type;
    if(extra.length > 0) {
      msg+='\nFound URIs where id is longer:\n';
      for(let i = 0; i < extra.length; i++) {
        msg += 'Uri: '+extra[i].uri+' Extra: '+extra[i].extra+'\n';
      }
    }
    throw new Error(msg);
  }
}

function getCSDLWithUri(type) {
  if(type.Annotations !== undefined && type.Annotations['Redfish.Uris'] !== undefined) {
    return type;
  }
  if(NoUriAllowList.indexOf(type.Name) !== -1) {
    return type;
  }
  if(type.BaseType) {
    return getCSDLWithUri(CSDL.findByType({_options: options}, type.BaseType));
  }
  return null;
}

function isIdInUri(id, uri) {
  let split = uri.split(/{\w*}/);
  let elem = split.shift();
  let index = id.indexOf(elem);
  if(index !== 0) {
    return false;
  }
  let rest = id.substring(elem.length);
  while(split.length) {
    elem = split.shift();
    if(elem === '') {
      index = rest.indexOf('/');
      if(index === -1 && split.length === 0) {
        return true;
      }
      rest = rest.substring(index);
    }
    else {
      index = rest.indexOf(elem);
      if(index === -1) {
        return false;
      }
      rest = rest.substring(elem.length+index);
    }
  }
  if(rest.length === 0 || rest === '/' || rest === '/SD' || rest === '/Settings') {
    return true;
  }
  return {uri: uri, extra: rest};
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
      if(propValue.match('([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') === null) {
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
      if(propValue.match('-?P(\\d+D)?(T(\\d+H)?(\\d+M)?(\\d+(.\\d+)?S)?)?') === null) {
        throw new Error('Property "'+propName+'" is an Edm.Duration, but the value in the mockup does not conform to the correct syntax.');
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
    if(NamespacesWithGlobalTypes.indexOf(namespace) !== -1) {
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
      if(propValue['@odata.id'] === undefined && Object.keys(propValue).length > 0 && !('Redfish.ExcerptCopy' in CSDLProperty.Annotations)) {
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

function propertyNameUnitCheck(csdl) {
  let props = CSDL.search(csdl, 'Property');
  if(props.length === 0) {
    return;
  }
  for(let i = 0; i < props.length; i++) {
    if(props[i].Annotations !== undefined && props[i].Annotations['Measures.Unit'] !== undefined) {
      let propName = props[i].Name;
      if(PropertyNamesWithoutCorrectUnits.includes(propName)) {
        //Skip this property
        continue;
      }
      let unitCode = props[i].Annotations['Measures.Unit'].String;
      let originalCode = unitCode;
      let pos = unitCode.indexOf('/s');
      if(pos !== -1) {
        unitCode = unitCode.substring(0, pos);
      }
      if(Object.keys(AlternativeUnitNames).includes(originalCode) && propName.endsWith(AlternativeUnitNames[originalCode])) {
        continue;
      }
      if(unitsAllowList.includes(unitCode)) {
        if(Object.keys(AlternativeUnitNames).includes(originalCode) && propName.endsWith(AlternativeUnitNames[originalCode])) {
          continue;
        }
        if(propName.endsWith(unitCode)) {
          continue;
        }
      }
      let unit = ucum.units[unitCode];
      if(unit === undefined) {
        let prefix = ucum.prefixes[unitCode[0]]
        unit = ucum.units[unitCode.substring(1)];
        if(unit === undefined) {
          prefix = ucum.prefixes[unitCode.substring(0,2)]
          unit = ucum.units[unitCode.substring(2)];
          if(unit === undefined) {
            throw new Error('Unknown unit code '+unitCode+' for property '+propName);
          }
        }
        unit = unit.charAt(0).toUpperCase()+unit.substring(1);
        unit = prefix+unit
      }
      unit = unit.charAt(0).toUpperCase()+unit.substring(1);
      if(!propName.endsWith(unit) && !propName.toLowerCase().endsWith(unit.toLowerCase())) {
        if(!propName.endsWith(unit+'s') && !propName.toLowerCase().endsWith(unit.toLowerCase()+'s')) {
          if(Object.keys(AlternativeUnitNames).includes(originalCode) && propName.endsWith(AlternativeUnitNames[originalCode])) {
            continue;
          }
          throw new Error('Property '+propName+' has unit '+unit+' but does not end with that name.');
        }
      }
    }
  }
}

function resourcesSpecifyCapabilities(csdl) {
  let entities = CSDL.search(csdl, 'EntityType');
  for(let i = 0; i < entities.length; i++) {
    if(entities[i].BaseType === 'Resource.v1_0_0.ResourceCollection' || entities[i].BaseType === 'Resource.v1_0_0.Resource') {
      // Base definition of a resource; check that it contains InsertRestrictions, UpdateRestrictions, and DeleteRestrictions
      let insertRes = CSDL.search(entities[i], 'Annotation', 'Capabilities.InsertRestrictions');
      if(insertRes.length === 0) {
        throw new Error(entities[i].Name+' does not specify InsertRestrictions.');
      }
      let updateRes = CSDL.search(entities[i], 'Annotation', 'Capabilities.UpdateRestrictions');
      if(updateRes.length === 0) {
        throw new Error(entities[i].Name+' does not specify UpdateRestrictions.');
      }
      let deleteRes = CSDL.search(entities[i], 'Annotation', 'Capabilities.DeleteRestrictions');
      if(deleteRes.length === 0) {
        throw new Error(entities[i].Name+' does not specify DeleteRestrictions.');
      }
    }
  }
}

function updatableReadWrite(csdl) {
  let updateRes = CSDL.search(csdl, 'Annotation', 'Capabilities.UpdateRestrictions');
  if(updateRes.length === 0) {
    return;
  }
  let updatable = updateRes[0].Record.PropertyValues.Updatable.Bool;
  let perms = CSDL.search(csdl, 'Annotation', 'OData.Permissions');
  let found = false;
  for(let i = 0; i < perms.length; i++) {
    let perm = perms[i].EnumMember;
    if(perm == 'OData.Permission/ReadWrite' && !updatable) {
      throw new Error('CSDL is not updatable but has read/write properties!');
    } else if(perm == 'OData.Permission/ReadWrite') {
      found = true;
    }
  }
  if(!found && updatable) {
    throw new Error('CSDL is updatable but has no read/write properties!');
  }
}

function insertCollections(csdl) {
  let insertRes = CSDL.search(csdl, 'Annotation', 'Capabilities.InsertRestrictions');
  if(insertRes.length === 0) {
    return;
  }
  let insertable = insertRes[0].Record.PropertyValues.Insertable.Bool;
  let entities = CSDL.search(csdl, 'EntityType');
  for(let i = 0; i < entities.length; i++) {
    if(entities[i].BaseType === 'Resource.v1_0_0.ResourceCollection' && !insertable) {
      //throw new Error('CSDL is not insertable but this is a resource collection!');
      //This is pretty common, let's not allow list it... just allow it
    } else if(entities[i].BaseType !== 'Resource.v1_0_0.ResourceCollection' && insertable) {
      throw new Error('CSDL is insertable but this is not a resource collection!');
    }
  }
}
/* vim: set tabstop=2 shiftwidth=2 expandtab: */
