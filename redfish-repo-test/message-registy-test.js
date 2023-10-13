const glob = require('glob');
const path = require('path');
const fs = require('fs');
const config = require('config');

describe('Message Registry Tests', () => {
  let mockupFiles = glob.sync(config.get('Redfish.MockupFilePath'));
  let latestFiles = {};
  mockupFiles.forEach((file) => {
    if(file.includes('DSP2046')) {
      //Skip the examples cause the file names aren't in the expected format
      return;
    }
    let basename = path.basename(file);
    let split = basename.split('.');
    if(latestFiles[split[0]] === undefined) {
      latestFiles[split[0]] = {base: basename, full: file};
    } else if(latestFiles[split[0]].base.localeCompare(basename) < 0) {
      latestFiles[split[0]] = {base: basename, full: file};
    }
  });

  for(let prop in latestFiles) {
    describe(prop, () => {
      let filename = latestFiles[prop].full;
      let txt = fs.readFileSync(filename, 'utf8');
      let json = JSON.parse(txt);
      delete txt;
      if(json !== null && json['@odata.type'] !== undefined && json['@odata.type'].includes('#MessageRegistry')) {
        //For message registries we need to make sure the id matches the file name and the RegistryPrefix and RegistryVersion is the same as in the id.
        it('Registry Valid Check', () => {registryCheck(json, filename);});
      }
    });
  }
});

function registryCheck(json, file) {
  //Id should be RegistryPrefix + '.' + RegistryVersion
  let myId = json.RegistryPrefix + '.' + json.RegistryVersion;
  if(myId !== json.Id) {
    throw new Error(file+': Found mismatched registry id. Found '+json.Id+' expected '+myId);
  }
  let fileName = path.basename(file);
  if(fileName != (myId + '.json')) {
    throw new Error(file+': Found mismatched registry filename. Found '+fileName+' expected '+myId+'.json');
  }
}
/* vim: set tabstop=2 shiftwidth=2 expandtab: */