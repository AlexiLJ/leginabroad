const { test } = require('node:test');
const assert = require('node:assert/strict');
const { calculateBudget, scenarios } = require('../static/js/prague-budget.js');

test('solo preset totals and annual projection', () => {
  assert.deepEqual(calculateBudget(scenarios.single, 1), {
    total: 39550, balance: 10450, annual: 125400, perPerson: 39550, savingsRate: 20.9
  });
});

test('couple shares expenses and uses combined income', () => {
  const result = calculateBudget(scenarios.couple, 2);
  assert.equal(result.total, 55100);
  assert.equal(result.balance, 24900);
  assert.equal(result.perPerson, 27550);
  assert.equal(result.annual, 298800);
});

test('custom expenses and a deficit retain the negative annual balance', () => {
  const result = calculateBudget({ ...scenarios.single, income: 30000, rent: 25000 }, 1);
  assert.equal(result.total, 42550);
  assert.equal(result.balance, -12550);
  assert.equal(result.annual, -150600);
});

test('zero income and break-even budgets avoid invalid percentages', () => {
  const noIncome = calculateBudget({ ...scenarios.single, income: 0 }, 1);
  assert.equal(noIncome.savingsRate, null);
  assert.equal(noIncome.balance, -39550);
  const even = calculateBudget({ ...scenarios.single, income: 39550 }, 1);
  assert.equal(even.balance, 0);
  assert.equal(even.savingsRate, 0);
});
