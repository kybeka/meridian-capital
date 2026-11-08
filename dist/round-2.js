const round2Data = JSON.parse(document.querySelector('#round2-data').textContent);
const percentage = (value, digits = 2) => `${(value * 100).toFixed(digits)}%`;
const dollars = value => value.toLocaleString('en-US', {style: 'currency', currency: 'USD'});
const displayDate = iso => new Intl.DateTimeFormat('en-GB', {
  day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'
}).format(new Date(`${iso}T12:00:00Z`));

function activateGroup(button, selector) {
  document.querySelectorAll(selector).forEach(item => {
    item.setAttribute('aria-pressed', String(item === button));
  });
}

document.querySelectorAll('[data-r2-allocation]').forEach(button => {
  button.addEventListener('click', () => {
    activateGroup(button, '[data-r2-allocation]');
    const measure = button.dataset.r2Allocation;
    document.querySelectorAll('.r2-allocation-row').forEach(row => {
      const value = Number(row.dataset[measure]);
      row.querySelector('.allocation-track span').style.width = `${value}%`;
      row.querySelector('strong').textContent = `${value.toFixed(2)}%`;
    });
    document.querySelector('#r2-allocation-description').textContent = measure === 'after'
      ? 'Whole-share weights at the 6 November close. Stocks are shown in navy.'
      : 'Original SAA target weights. This remains the benchmark for Round 2.';
  });
});

document.querySelectorAll('[data-r2-value]').forEach(button => {
  button.addEventListener('click', () => {
    activateGroup(button, '[data-r2-value]');
    const measure = button.dataset.r2Value;
    round2Data.valuations.forEach(stock => {
      const row = document.querySelector(`.r2-value-row[data-ticker="${stock.ticker}"]`);
      const value = stock[measure];
      const upside = value / stock.price - 1;
      const width = Math.max(0, Math.min(100, upside / .5 * 100));
      row.querySelector('.r2-value-line').style.width = `${width}%`;
      row.querySelector('i').style.left = `${width}%`;
      row.querySelector('.r2-value-reading strong').textContent = dollars(value);
      row.querySelector('.r2-value-reading span').textContent = `${percentage(upside)} upside`;
    });
    document.querySelector('#r2-value-description').textContent = measure === 'earnings'
      ? 'Earnings-based values used in the original selection. The left marker is each stock\'s entry price.'
      : 'Lower of the earnings and FCFF values. These are sensitivity checks at unchanged portfolio weights.';
  });
});

function drawReplay(regime) {
  const data = round2Data.replay[regime];
  const [lower, upper] = data.active_mean_ci_block;
  document.querySelector('#r2-active').textContent = percentage(data.mean_active, 3);
  document.querySelector('#r2-win').textContent = percentage(data.outperform_rate, 1);
  document.querySelector('#r2-samples').textContent = data.n_overlapping.toLocaleString('en-US');
  document.querySelector('#r2-replay-description').textContent = `${regime === 'post' ? 'After' : 'Before'} the methodology change: ${displayDate(data.start_first)} to ${displayDate(data.end_last)}. Zero trading fees.`;
  document.querySelector('#r2-interval-caption').textContent = `95% block-bootstrap interval for mean active return: ${percentage(lower)} to ${percentage(upper)}.`;
  const result = lower <= 0 && upper >= 0 ? 'The interval includes zero.' : 'The interval excludes zero in this historical replay.';
  document.querySelector('#r2-independent').textContent = `${data.n_overlapping.toLocaleString('en-US')} overlapping periods contain ${data.nonoverlap_n_min}–${data.nonoverlap_n_max} non-overlapping windows per starting offset. ${result} Today's stock choices and assumptions are reused throughout the history.`;

  const chart = document.querySelector('#r2-interval');
  const minimum = Math.min(-.02, lower - .002);
  const maximum = Math.max(.01, upper + .002);
  const x = value => 48 + (value - minimum) / (maximum - minimum) * 704;
  const namespace = 'http://www.w3.org/2000/svg';
  chart.replaceChildren();
  const add = (tag, attributes, text) => {
    const element = document.createElementNS(namespace, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
    if (text !== undefined) element.textContent = text;
    chart.append(element);
  };
  add('line', {x1: 48, y1: 72, x2: 752, y2: 72, class: 'r2-axis-line'});
  add('line', {x1: x(0), y1: 20, x2: x(0), y2: 94, class: 'r2-zero-line'});
  add('line', {x1: x(lower), y1: 56, x2: x(upper), y2: 56, class: 'r2-ci-line'});
  [lower, upper].forEach(value => add('line', {x1: x(value), y1: 47, x2: x(value), y2: 65, class: 'r2-ci-cap'}));
  add('circle', {cx: x(data.mean_active), cy: 56, r: 6, class: 'r2-mean-point'});
  [minimum, 0, maximum].forEach(value => add('text', {x: x(value), y: 113, 'text-anchor': 'middle'}, percentage(value)));
  add('text', {x: x(data.mean_active), y: 25, 'text-anchor': 'middle'}, `Mean ${percentage(data.mean_active, 3)}`);
  chart.setAttribute('aria-label', `Mean active return ${percentage(data.mean_active, 3)}; 95% interval ${percentage(lower)} to ${percentage(upper)}. Zero is the SAA comparison.`);
}

document.querySelectorAll('[data-r2-regime]').forEach(button => {
  button.addEventListener('click', () => {
    activateGroup(button, '[data-r2-regime]');
    drawReplay(button.dataset.r2Regime);
  });
});
drawReplay('post');
