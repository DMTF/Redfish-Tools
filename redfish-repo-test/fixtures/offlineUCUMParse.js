const request = require('request');
const xmljs = require('libxmljs');

let obj = {prefixes: [], units: []};

request({url: 'http://unitsofmeasure.org/ucum-essence.xml', timeout: 5000}, (error, response, body) => {
  let doc = xmljs.parseXml(body);
  let root = doc.root();
  let children = root.childNodes();
  let code;
  for(let i = 0; i < children.length; i++) {
    let name = children[i].name();
    switch(name) {
      case 'prefix':
        code = children[i].attr('Code');
        obj.prefixes.push(code.value());
        break;
      case 'base-unit':
      case 'unit':
        code = children[i].attr('Code');
        obj.units.push(code.value());
        break;
      default:
        break;
    }
  }
  console.log(JSON.stringify(obj));
});
