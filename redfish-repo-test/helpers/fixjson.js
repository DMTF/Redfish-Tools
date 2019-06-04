const glob = require('glob');
const path = require('path');
const fs = require('fs');

let files = glob.sync(path.join('{mockups,registries}', '**', '*.json'));

files.forEach((file) => {
  fs.readFile(file, (err, txt) => {
    if(err) {
      console.error('Unable to open file '+file+': '+err);
      return;
    }
    txt = txt.toString('utf-8');
    let js = JSON.parse(txt);
    let newTxt = JSON.stringify(js, null, 4);
    windowsTxt = newTxt.replace(/\n/gm, '\r\n');
    trimmedTxt = txt.trim();
    if(newTxt !== txt && windowsTxt !== txt && newTxt !== trimmedTxt && windowsTxt !== trimmedTxt) {
      fs.writeFile(file, newTxt, (err) => {
        if(err) {
          console.error('Unable to write file '+file+': '+err);
        }
      });
    }
  });
});
