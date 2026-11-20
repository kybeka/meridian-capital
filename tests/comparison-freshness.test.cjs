const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');
const source = fs.readFileSync('dist/challenge-performance.js','utf8');
const summary = source.slice(source.indexOf('    function updateSummary(view)'),source.indexOf('    function render()'));
test('headline follows the selected chart date and discloses a delayed comparison',()=>{
  const elements = {};
  const context = vm.createContext({document:{querySelector:s=>elements[s] ||= {}},
    first:{date:'2026-10-16',nav:1e8},last:{date:'2026-11-19'},peers:{},comparing:true,
    pct:n=>n.toFixed(2)+'%',dateLabel:d=>d,Intl});
  vm.runInContext(summary,context);
  const render=(date,value)=>{context.view={dates:[date],series:[{id:'meridian',values:[value]}]};vm.runInContext('updateSummary(view)',context);};
  render('2026-11-18',95.7);
  assert.equal(elements['#challenge-return'].textContent,'-4.30%');
  assert.match(elements['#challenge-asof'].textContent,/Valued 2026-11-18$/);
  assert.match(elements['#challenge-nav'].textContent,/95,700,000.00/);
  assert.equal(elements['#peer-availability'].hidden,false);
  assert.match(elements['#peer-availability'].textContent,/2026-11-19/);
  context.comparing=false;render('2026-11-19',94.8);
  assert.equal(elements['#challenge-return'].textContent,'-5.20%');
  assert.equal(elements['#peer-availability'].hidden,true);
  context.comparing=true;render('2026-11-19',94.8);
  assert.equal(elements['#peer-availability'].hidden,true);
});
