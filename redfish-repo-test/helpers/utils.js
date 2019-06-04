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
