(async () => {
  const panel = document.querySelector('#challenge-results');
  if (!panel) return;
  const get = async (url, json = false) => {
    const response = await fetch(url, {cache: 'no-cache'});
    if (!response.ok) throw Error('Valuations unavailable');
    return json ? response.json() : response.text();
  };
  const pct = value => `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(2)}%`;
  const dateLabel = date => new Date(`${date}T12:00:00Z`).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
  const colours = ['#173242', '#927d56', '#527b70', '#82708c', '#a6644e'];
  const patterns = ['', '8 4', '3 4', '12 4 3 4', '2 5'];
  try {
    const [ownResult, peerResult] = await Promise.allSettled([get('data/challenge-valuations.csv'), get('data/peer-valuations.json', true)]);
    if (ownResult.status !== 'fulfilled') throw Error('Valuations unavailable');
    const rows = ownResult.value.trim().split(/\r?\n/).slice(1).filter(Boolean).map(line => {
      const [date, nav, source] = line.split(',');
      return {date, nav: Number(nav), source};
    });
    rows.forEach((row, i) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !Number.isFinite(row.nav) || row.nav <= 0 || !row.source || (i && row.date <= rows[i-1].date)) throw Error('Invalid valuation record');
    });
    if (!rows.length) throw Error('Empty valuations');
    const first = rows[0], last = rows.at(-1);
    const own = {dates: rows.map(r => r.date), series: [{id:'meridian', name:'Meridian Capital', values:rows.map(r => r.nav / first.nav * 100)}]};
    let peers = peerResult.status === 'fulfilled' ? peerResult.value : null;
    if (peers && (!Array.isArray(peers.dates) || !peers.dates.length || !Array.isArray(peers.series) || peers.series.length !== 5 || peers.dates.some((d,i) => !/^\d{4}-\d{2}-\d{2}$/.test(d) || (i && d <= peers.dates[i-1])) || peers.series.some(s => s.values.length !== peers.dates.length || s.values.some(v => !Number.isFinite(v) || v <= 0) || Math.abs(s.values[0]-100) > .0001))) peers = null;
    const peerLabels = {sixfold: 'Team A', swissstreet: 'Team B', matterhorn: 'Team C', rivemont: 'Team D'};
    if (peers) peers.series = peers.series.map(series => ({...series, name: peerLabels[series.id] || series.name}));
    document.querySelector('#challenge-return').textContent = pct(last.nav / first.nav * 100 - 100);
    document.querySelector('#challenge-asof').textContent = `Meridian · Since ${dateLabel(first.date)} · Valued ${dateLabel(last.date)}`;
    document.querySelector('#challenge-nav').textContent = `${new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(last.nav)} portfolio value, including cash and dividend receivables`;
    document.querySelector('#tracking-status').textContent = 'Public-price estimate';
    const chart = document.querySelector('#challenge-chart');
    chart.setAttribute('viewBox','0 0 1000 350');
    chart.insertAdjacentHTML('beforebegin', `<div class="peer-toolbar"><div class="peer-modes" role="group" aria-label="Portfolio chart view"><button type="button" aria-pressed="true" data-view="own">Meridian</button><button type="button" aria-pressed="false" data-view="peers" ${peers ? '' : 'disabled'}>Compare teams</button></div><span class="peer-chart-basis">Value of 100 · USD</span></div><p id="peer-availability" class="source-note" ${peers ? 'hidden' : ''}>Peer comparison is temporarily unavailable. Meridian’s tracker is shown below.</p><div id="peer-legend" class="peer-legend" role="group" aria-label="Portfolios shown" hidden></div>`);
    chart.insertAdjacentHTML('afterend', `<div class="peer-date-control"><label for="peer-date">Explore a date <strong id="peer-selected-date"></strong></label><input id="peer-date" type="range" min="0" step="1" aria-label="Chart valuation date"><p class="source-note">Hover or tap the chart, or use the slider to compare a close.</p></div><div id="peer-readout" class="peer-readout"></div><div id="peer-method" class="peer-method" hidden><p>We use each team’s published Round 1 shares and cash, with the same daily USD closing-price source and dividend treatment as our tracker. Each portfolio starts at 100 on 16 October.</p><details><summary>Comparison method</summary><p>These estimates hold the published opening shares unchanged and include dividends as receivables from the ex-date, without reinvesting them. Cash earns no interest; trading fees and taxes are excluded. Each line is divided by its own opening basket value. One portfolio’s published cash is rounded to whole dollars, leaving an $0.08 opening difference.</p><p>Peer holdings checked on 29 October 2026. This comparison stops at the 6 November Round 1 close until we verify the teams’ later trades. These are our reconstructions of published holdings; official results come from Bloomberg and the course team.</p><p>The other teams are labelled A–D throughout this chart.</p></details><p id="peer-through" class="source-note"></p></div>`);
    const legend = document.querySelector('#peer-legend'), range = document.querySelector('#peer-date');
    const enabled = new Set(peers ? peers.series.map(s => s.id) : ['meridian']);
    let comparing = false, data = own, selected = own.dates.length - 1, x, y, shown;
    if (peers) {
      peers.series.forEach((s, i) => {
        const label = document.createElement('label');
        const input = document.createElement('input'); input.type = 'checkbox'; input.checked = true;
        const swatch = document.createElement('span'); swatch.className = 'peer-swatch'; swatch.style.background = colours[i];
        label.append(input, swatch, document.createTextNode(s.name)); legend.append(label);
        input.addEventListener('change', () => { if (!input.checked && enabled.size === 1) { input.checked = true; return; } input.checked ? enabled.add(s.id) : enabled.delete(s.id); render(); });
      });
      document.querySelector('#peer-through').textContent = `All five portfolios valued through ${dateLabel(peers.dates.at(-1))}.`;
    }
    function inspect(index) {
      selected = Math.max(0, Math.min(data.dates.length-1, index)); range.value = selected;
      range.setAttribute('aria-valuetext', dateLabel(data.dates[selected]));
      document.querySelector('#peer-selected-date').textContent = dateLabel(data.dates[selected]);
      const cx = x(selected);
      chart.querySelector('.peer-cursor').innerHTML = `<path d="M${cx} 25V290" stroke="#657780" stroke-dasharray="3 5"/>` + shown.map(s => `<circle cx="${cx}" cy="${y(s.values[selected])}" r="5" fill="${s.colour}" stroke="#f7f5ef" stroke-width="2"/>`).join('');
      const readout = document.querySelector('#peer-readout'); readout.replaceChildren();
      shown.forEach(s => {
        const item = document.createElement('div'); item.className = 'peer-reading'; item.style.borderTopColor = s.colour;
        const name = document.createElement('span'); name.textContent = s.name;
        const value = document.createElement('strong'); value.textContent = pct(s.values[selected]-100);
        const indexValue = document.createElement('small'); indexValue.textContent = `${s.values[selected].toFixed(2)} indexed value`;
        item.append(name,value,indexValue); readout.append(item);
      });
    }
    function render() {
      data = comparing ? peers : own;
      selected = Math.min(selected, data.dates.length-1);
      shown = data.series.map((s,i) => ({...s,colour:colours[i],pattern:patterns[i]})).filter(s => !comparing || enabled.has(s.id));
      const width = chart.clientWidth < 600 ? Math.max(340, chart.clientWidth) : 1000;
      chart.setAttribute('viewBox', `0 0 ${width} 350`);
      const right = width - 30;
      const values = shown.flatMap(s => s.values), min = Math.min(100,...values), max = Math.max(100,...values), pad = Math.max((max-min)*.15,.15);
      const low = min-pad, high = max+pad;
      x = i => data.dates.length === 1 ? 70 : 70+(Date.parse(data.dates[i])-Date.parse(data.dates[0]))/(Date.parse(data.dates.at(-1))-Date.parse(data.dates[0]))*(right-70);
      y = value => 290-(value-low)/(high-low)*260;
      chart.innerHTML = [low,(low+high)/2,high].map(v => `<path d="M70 ${y(v)}H${right}" stroke="#d7d9d1"/><text x="55" y="${y(v)+5}" text-anchor="end">${v.toFixed(2)}</text>`).join('') + `<path d="M70 ${y(100)}H${right}" stroke="#9ca7a5" stroke-dasharray="3 5"/>` + shown.map(s => `<path d="${s.values.map((v,i) => `${i?'L':'M'}${x(i)},${y(v)}`).join(' ')}" stroke="${s.colour}" stroke-width="${s.id==='meridian'?3.5:2.5}" stroke-dasharray="${s.pattern}" fill="none"/>`).join('') + `<g class="peer-cursor"></g><text x="70" y="330">${dateLabel(data.dates[0])}</text><text x="${right}" y="330" text-anchor="end">${dateLabel(data.dates.at(-1))}</text>`;
      chart.setAttribute('aria-label', `${comparing?'Five-team portfolio comparison':'Meridian portfolio performance'}, indexed to 100. Use the date slider below for values.`);
      range.max = data.dates.length-1; inspect(selected);
    }
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
      comparing = button.dataset.view === 'peers';
      document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      legend.hidden = !comparing; document.querySelector('#peer-method').hidden = !comparing;
      selected = (comparing ? peers : own).dates.length-1; render();
    }));
    const pointAt = event => {
      const point = chart.createSVGPoint(); point.x=event.clientX; point.y=event.clientY;
      const local = point.matrixTransform(chart.getScreenCTM().inverse());
      let closest=0; data.dates.forEach((_,i) => {if(Math.abs(x(i)-local.x)<Math.abs(x(closest)-local.x))closest=i;}); inspect(closest);
    };
    chart.addEventListener('pointermove', pointAt);
    chart.addEventListener('pointerdown', pointAt);
    range.addEventListener('input', () => inspect(Number(range.value)));
    document.querySelector('#tracking-empty').hidden = true; panel.hidden = false; render();
    let previousWidth = chart.clientWidth;
    new ResizeObserver(() => { if (chart.clientWidth !== previousWidth) { previousWidth = chart.clientWidth; render(); } }).observe(chart);
  } catch {
    document.querySelector('#tracking-status').textContent = 'Valuations unavailable';
  }
})();
