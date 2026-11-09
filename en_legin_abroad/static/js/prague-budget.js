(function () {
  'use strict';

  const isNode = typeof module !== 'undefined' && module.exports;
  const data = isNode
    ? require('../../prague_budget.json')
    : JSON.parse(document.getElementById('budget-data').textContent);
  const scenarios = data.scenarios;
  const expenseKeys = data.expense_fields.map(field => field.key);

  function calculateBudget(values, people) {
    const total = expenseKeys.reduce((sum, key) => sum + values[key], 0);
    const balance = values.income - total;
    return { total, balance, annual: balance * 12, perPerson: total / people,
      savingsRate: values.income > 0 ? balance / values.income * 100 : null };
  }

  // Keep the arithmetic usable by the small Node regression suite as well.
  if (isNode) {
    module.exports = { calculateBudget, scenarios };
  }
  if (typeof document === 'undefined') return;
  const form = document.getElementById('budget-form');
  if (!form) return;
  const money = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });
  const amount = value => money.format(value) + ' Kč';
  const setText = (id, value) => { document.getElementById(id).textContent = value; };

  function update() {
    const inputs = [...form.querySelectorAll('input[type="number"]')];
    const valid = inputs.every(input => input.validity.valid && Number.isFinite(input.valueAsNumber));
    document.getElementById('budget-error').hidden = valid;
    document.getElementById('budget-results').hidden = !valid;
    if (!valid) return;
    const values = Object.fromEntries(inputs.map(input => [input.name, input.valueAsNumber]));
    const result = calculateBudget(values, scenarios[form.elements.scenario.value].people);
    const shortfall = result.balance < 0;
    setText('total', amount(result.total));
    setText('balance-label', shortfall ? 'Monthly shortfall' : 'Left to save each month');
    setText('balance', amount(Math.abs(result.balance)));
    document.getElementById('balance').classList.toggle('is-shortfall', shortfall);
    setText('balance-note', result.savingsRate === null ? 'Add income to calculate your savings rate.' :
      (shortfall ? 'Expenses exceed income by ' : '') + Math.abs(result.savingsRate).toFixed(1) + '% of your take-home income');
    setText('annual', amount(result.annual));
    setText('per-person', amount(result.perPerson));
    setText('summary-note', shortfall ? 'At this pace, the annual shortfall would be ' + amount(Math.abs(result.annual)) + '. Adjust costs or income to balance your budget.' :
      'A projection of 12 identical months, before unexpected costs or investment returns.');
  }

  function loadScenario() {
    const preset = scenarios[form.elements.scenario.value];
    ['income', ...expenseKeys].forEach(key => { form.elements[key].value = preset[key]; });
    update();
  }

  form.addEventListener('input', event => {
    if (event.target.name === 'scenario') loadScenario();
    else update();
  });
  form.addEventListener('reset', event => { event.preventDefault(); loadScenario(); });
  form.addEventListener('submit', event => { event.preventDefault(); update(); });
  update();
}());
