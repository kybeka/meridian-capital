const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {test} = require('node:test');
const source = fs.readFileSync('dist/challenge-performance.js', 'utf8');
// Exercise the chart's actual selection and sorting after crossing the rebalance.
const declaration = source.match(/const holdingTickers = .*;/)[0];
const selection = source.match(/const visibleTickers = .*;/)[0];
const sorting = source.match(/visibleTickers\.sort\([^;]+?\)\.forEach/)[0].replace(/\.forEach$/, ';');
const context = vm.createContext({});
vm.runInContext(`${declaration}
function inspect(date, values) {
  const data = {dates: [date]}, selected = 0;
  ${selection}
  ${sorting}
  return visibleTickers;
}`, context);
test('Round 2 inspection cannot change the historical ETF list', () => {
  const expected = ['SPY','EEMV','DBC','VGSH','SCHD','STIP'];
  const values = {KR:10,BMY:9,HRL:8,ADBE:7,XOM:6,HPQ:5,SPY:-1,EEMV:-2,DBC:-3,VGSH:0,SCHD:1,STIP:2};
  context.values = values;
  for (let i=0;i<3;i++) {
    assert.equal(vm.runInContext("inspect('2026-11-09', values).length", context),12);
    for (const date of ['2026-10-26','2026-11-06']) {
      context.date=date;
      const shown=Array.from(vm.runInContext('inspect(date, values)',context));
      assert.deepEqual(shown.sort(),[...expected].sort());
    }
  }
  assert.deepEqual(Array.from(vm.runInContext('holdingTickers.slice(0,6)',context)),expected);
});
