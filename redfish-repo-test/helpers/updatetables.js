const glob = require('glob');
const config = require('config');
const fs = require('fs');
const matchAll = require('match-all');

let files = config.get('Redfish.TableNumberingDocs');

files.forEach((file) => {
  fs.readFile(file, (err, txt) => {
    if(err) {
      console.error('Unable to open file '+file+': '+err);
      return;
    }
    txt = txt.toString('utf-8');

    // Find all of the table references
    // Group 1: The table label
    // Group 2: The table number
    // Group 3: The table name
    // Group 4: The unique reference tag
    let tables = matchAll(txt, /(: \*\*Table (\d+) &mdash; (.+)\*\*<a id="(.+)"><\/a>)/gi);

    // Go through each match and update all of the table numbers
    for(let i = 1, table = tables.nextRaw(); table != null; i++, table = tables.nextRaw()) {
      // Build the old labels and references
      let old_label = table[1]
      let old_reference = new RegExp('\\[Table \\d+\\]\\(#' + table[4] + '\\)', 'gi');

      // Build the new labels and references
      let new_label = ': **Table ' + i.toString() + ' &mdash; ' + table[3] + '**<a id="' + table[4] + '"></a>';
      let new_reference = '[Table ' + i.toString() + '](#' + table[4] + ')'

      // Update labels and references
      txt = txt.replace(old_label, new_label);
      txt = txt.replace(old_reference, new_reference);
    }

    // Save the file
    fs.writeFile(file, txt, (err) => {
      if(err) {
        console.error('Unable to write file '+file+': '+err);
      }
    });
  });
});
