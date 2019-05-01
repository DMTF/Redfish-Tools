// Copyright Notice:
// Copyright 2016-2019 DMTF. All rights reserved.
// License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/Redfish-Tools/blob/master/LICENSE.md

module.exports.execAll = function(regex, str) {
  var match = null;
  var matches = [];

   while (match = regex.exec(str)) {
     var matchArray = [];
     for (var i in match) {
       if (parseInt(i) == i) {
         matchArray.push(match[i].trim());
       }
     }
     matchArray.lineNumber = str.substr(0, match.index).split("\n").length + 1;
     matches.push(matchArray);
   }

   return matches.length > 0 ? matches : null;
}
