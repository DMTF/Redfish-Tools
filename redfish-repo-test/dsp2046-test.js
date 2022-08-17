const glob = require('glob');
const config = require('config');
const path = require('path');
const fs = require("fs");
//We're doing a quicker XML only parsing here to make this quicker than full CSDL parsing...
const et = require('elementtree');

describe('DSP2046 Tests', () => {
    if(!config.has('Redfish.DSP2046Files')) {
        //No DSP2046 files configured. Skip tests.
        return;
    }
    const csdlFiles = glob.sync(config.get('Redfish.NormativeCSDLPath'));
    const noDSP2046Files = config.get('Redfish.NoDSP2046Files');
    let dspFiles = glob.sync(config.get('Redfish.DSP2046Files'));
    if(dspFiles.length === 0) {
        throw new Error('No DSP2046 Files found!');
    }

    csdlFiles.forEach((csdlFile) => {
        let baseCSDLFileName = path.basename(csdlFile, '.xml');
        if(baseCSDLFileName.endsWith('Collection_v1')) {
            //Skip collections, they don't have examples.
            return;
        }
        if(noDSP2046Files.includes(baseCSDLFileName)) {
            //Explicitly told to skip this file.
            return;
        }
        it('Has Resource Example JSON: '+baseCSDLFileName, (done) => {hasResourceExampleJson(csdlFile, dspFiles, done);});
        it('Has Action examples: '+baseCSDLFileName, (done) => {hasActionExampleJson(csdlFile, dspFiles, done);});
    });
});

function hasResourceExampleJson(csdlFile, dspFiles, done) {
    const dspBasePath = path.dirname(dspFiles[0]);
    let baseCSDLFileName = path.basename(csdlFile, '.xml');
    let csdlDSPName = dspBasePath+'/'+baseCSDLFileName.replace('_', '-')+'-example.json';
    if(!dspFiles.includes(csdlDSPName)) {
        //Make sure we actually need an example, i.e. the file contains at least one EntityType entry...
        fs.readFile(csdlFile, (err, buff) => {
            if(err) {
                done(err);
            }
            let etree = et.parse(buff.toString());
            let nodes = etree.findall('.//EntityType');
            if(nodes.length > 0) {
                done(new Error('Missing DSP2046 file for CSDL '+baseCSDLFileName));
                return;
            }
            done();
        });
    } else {
        done();
    }
}

function hasActionExampleJson(csdlFile, dspFiles, done) {
    const dspBasePath = path.dirname(dspFiles[0]);
    let baseCSDLFileName = path.basename(csdlFile, '.xml');
    fs.readFile(csdlFile, (err, buff) => {
        if(err) {
            done(err);
        }
        let etree = et.parse(buff.toString());
        let nodes = etree.findall('.//Action');
        for(let i = 0; i < nodes.length; i++) {
            let node = nodes[i];
            let params = node.findall('.//Parameter');
            if(params.length === 1) {
                //This action only has the target and therefore doesn't need an example
                continue;
            }
            let actionName = node.get('Name');
            let csdlDSPName = dspBasePath+'/'+baseCSDLFileName.replace('_', '-')+'-'+actionName+'-request-example.json';
            if(!dspFiles.includes(csdlDSPName)) {
                done(new Error('Missing DSP2046 file for Action '+actionName+' in CSDL '+baseCSDLFileName));
                return;
            }
        }
        done();
    });
}