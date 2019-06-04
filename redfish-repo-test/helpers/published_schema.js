const request = require('request');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

module.exports.getPublishedSchemaVersionList = function(uri) {
  return new Promise((resolve, reject) => {
    request({url: uri, timeout: 5000}, (error, response, body) => {
      if(error) {
        reject(error);
        return;
      }
      if(response.statusCode !== 200) {
        reject(new Error('Failed to get '+uri+' HTTP Status = '+response.statusCode));
        return;
      }
      let doc = new JSDOM(body);
      let $ = require('jquery')(doc.window);
      let links = $('a');
      let list = {};
      for(let i = 0; i < links.length; i++) {
        if(links[i].href.indexOf('.json') !== -1 && links[i].href.indexOf('.v') !== -1) {
          let parts = links[i].href.split('.');
          if(list[parts[0]] === undefined) {
            list[parts[0]] = {};
          }
          addVersionToList(list[parts[0]], parts[1]);
        }
      }
      resolve(list);
    });
  });
}

function addVersionToList(listEntry, version) {
  let parts = version.split('_');
  if(listEntry[parts[0]] === undefined) {
    listEntry[parts[0]] = {};
  }
  let subEntry = listEntry[parts[0]];
  if(subEntry[parts[1]] === undefined) {
    subEntry[parts[1]] = [];
  }
  subEntry[parts[1]].push(parts[2]+'');
}
/* vim: set tabstop=2 shiftwidth=2 expandtab: */
