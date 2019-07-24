const glob = require('glob');
const jsonlint = require('jsonlint');
const fs = require('fs');
const assert = require('assert');
const marked = require('marked');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const execAll = require('./helpers/utils').execAll;

describe('Markdown', () => {
  const files = glob.sync('*.md');

  files.forEach((file) => {
    describe(file, () => {
      let text = null;
      let examples = null;
      before((done) => {
        fs.readFile(file, 'utf-8', (err, data) => {
          if(err) {
            throw err;
          }
          text = data;
          examples = execAll(/(?:~~~|```)(json|http)([\s\S]*?)(?:~~~|```)/gim, data); 
          done();
        });
      });
      it('Examples are Valid JSON', () => {
        if(examples === null) {
          return;
        }
        examples.forEach((example) => {
          let json = example[1] === 'http' ? example[2].split("\n\n")[1] : example[2];

          if(!json) return;

          // Replace surrounding ellipsis with actual braces
          if (/^\.\.\./.test(json)) {
            json = json.replace(/^\.\.\./, '{').replace(/,?\s*\.\.\.$/, '}')
          }

          // Replace any ellipsis in the body with nothingness
          json = json.replace(/(["\]}]),?\s*\.\.\./, '$1');

          try {
            jsonlint.parse(json);
          } catch(e) {
            assert(false, 'Failed to parse\n' + e.message.replace(/(lines? )(\d+):/, function(_, l, m) {
              // Massage the error to be the actual line number in markdown
              return l + (example.lineNumber + parseInt(m, 10)) + ':';
            }));
          }
        });
      });
      it('Internal Links are consistent', function(done) {
        this.timeout(5000);
        marked(text, (err, html) => {
            let doc = new JSDOM(`<body>${html}</body>`);
            let $ = require('jquery')(doc.window);
            let targets = new Set();
            $('[id]').each((i, el) => {
              targets.add($(el).attr('id'));
            });

            $('a[href^="#"]').each((i, el) => {
              const $el = $(el);
              const link = $el.attr('href').slice(1);
              let parent = $el;
              do {
                parent = parent.parent();
              } while (!parent.parent().is('body'));
              const section = parent.prevAll('h1, h2, h3, h4, h5, h6').first().text();

              assert(targets.has(link), `Link "${$el.text()}" targets non-existant id "${link}" in document. Link is in section "${section}".`);
           });
           done();
        });
      });
    });
  });
});
