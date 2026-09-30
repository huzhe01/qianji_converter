const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const cases = require('./date-cases.json');
const app = vm.createContext({
  document: { getElementById: () => ({ addEventListener() {} }) },
});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../docs/app.js'), 'utf8'), app);

test('normalizes BEA and HSBC dates without swapping year and day', () => {
  for (const [input, expected] of cases.valid) {
    assert.equal(app.parseDate(input), expected, input);
  }
  for (const input of cases.invalid) {
    assert.equal(app.parseDate(input), null, input);
  }
});

test('BEA CSV round trip preserves dates, amounts and income/expense', () => {
  const input = '\uFEFF記賬日期,交易日期,賬項說明,金額\r\n2026/09/28,2026/09/28,Example shop,76.17\r\n2026/09/05,2026/09/05,Example refund,-16.8';
  const output = app.parseCsv(app.buildCsv(app.convertBea(app.rowsToObjects(app.parseCsv(input)))));
  assert.equal(output.length, 3);
  assert.equal(output[1][0], '2026/09/28 00:00');
  assert.equal(output[2][0], '2026/09/05 00:00');
  assert.equal(output[1][2], '支出');
  assert.equal(output[1][3], '76.17');
  assert.equal(output[2][2], '收入');
  assert.equal(output[2][3], '16.8');
});

test('HSBC conversion keeps its day-first interpretation', () => {
  const input = 'Transaction date,Billing amount,Description,Merchant name\n05/09/2026,-26.8,Example,Example';
  const output = app.convertHsbc(app.rowsToObjects(app.parseCsv(input)));
  assert.equal(output[1][0], '2026/09/05 00:00');
  assert.equal(output[1][2], '支出');
  assert.equal(output[1][3], 26.8);
});
