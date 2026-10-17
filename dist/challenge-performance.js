(() => {
  const panel = document.querySelector('#challenge-results');
  if (!panel) return;
  fetch('data/challenge-valuations.csv', {cache: 'no-cache'})
    .then(response => { if (!response.ok) throw Error('Valuations unavailable'); return response.text(); })
    .then(csv => {
      const rows = csv.trim().split(/\r?\n/).slice(1).filter(Boolean).map(line => {
        const [date, nav, source] = line.split(',');
        return {date, nav: Number(nav), source};
      });
      if (!rows.length) return;
      rows.forEach((row, i) => {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !Number.isFinite(row.nav) || row.nav <= 0 || !row.source || (i && row.date <= rows[i-1].date)) throw Error('Invalid valuation record');
      });
      const first = rows[0], last = rows.at(-1), values = rows.map(row => row.nav / first.nav * 100);
      const start = Date.parse(first.date), end = Date.parse(last.date);
      const x = i => rows.length === 1 ? 70 : 70 + (Date.parse(rows[i].date) - start) / (end - start) * 860;
      const min = Math.min(...values), max = Math.max(...values), pad = Math.max((max - min) * .15, .5);
      const low = min - pad, high = max + pad, y = v => 260 - (v-low)/(high-low)*220;
      const chart = document.querySelector('#challenge-chart');
      chart.innerHTML = [low,(low+high)/2,high].map(v => `<path d="M70 ${y(v)}H930" stroke="#d7d9d1"/><text x="55" y="${y(v)+4}" text-anchor="end">${v.toFixed(2)}</text>`).join('') +
        (rows.length > 1 ? `<path d="${values.map((v,i) => `${i ? 'L':'M'}${x(i)},${y(v)}`).join(' ')}" stroke="#173242" stroke-width="3" fill="none"/>` : '') +
        `<circle cx="${x(rows.length-1)}" cy="${y(values.at(-1))}" r="5" fill="#173242"/><text x="70" y="300">${first.date}</text>` + (rows.length > 1 ? `<text x="930" y="300" text-anchor="end">${last.date}</text>` : '');
      document.querySelector('#challenge-return').textContent = `${values.at(-1)-100 >= 0 ? '+':''}${(values.at(-1)-100).toFixed(2)}%`;
      document.querySelector('#challenge-asof').textContent = `Since ${first.date} · Valued ${last.date}`;
      document.querySelector('#challenge-nav').textContent = `${new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(last.nav)} portfolio value, including cash`;
      document.querySelector('#tracking-status').textContent = rows.length > 1 ? 'Recorded challenge performance' : 'Opening valuation recorded';
      document.querySelector('#tracking-empty').hidden = true;
      panel.hidden = false;
    }).catch(() => { document.querySelector('#tracking-status').textContent = 'Valuations unavailable'; });
})();
