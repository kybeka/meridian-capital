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
    const [ownResult, peerResult, contributionResult] = await Promise.allSettled([get('data/challenge-valuations.csv'), get('data/peer-valuations.json', true), get('data/portfolio-contributions.json', true)]);
    if (ownResult.status !== 'fulfilled') throw Error('Valuations unavailable');
    const rows = ownResult.value.trim().split(/\r?\n/).slice(1).filter(Boolean).map(line => {
      const [date, nav, source] = line.split(',');
      return {date, nav: Number(nav), source};
    });
    rows.forEach((row, i) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(row.date) || !Number.isFinite(row.nav) || row.nav <= 0 || !row.source || (i && row.date <= rows[i-1].date)) throw Error('Invalid valuation record');
    });
    if (!rows.length) throw Error('Empty valuations');
    const contributionData = contributionResult.status === 'fulfilled' ? contributionResult.value : null;
    const contributionRows = new Map();
    const holdingTickers = Object.freeze(['SPY','EEMV','DBC','VGSH','SCHD','STIP','ADBE','KR','HRL','BMY','XOM','HPQ']);
    if (contributionData?.reference_date === rows[0].date && Array.isArray(contributionData.rows)) {
      for (const entry of contributionData.rows) {
        const matching = rows.find(r => r.date === entry.date);
        if (!matching || Math.abs(matching.nav-entry.nav_usd) > .01) continue;
        if (!['since','daily'].every(mode => entry[mode] && Object.keys(entry[mode]).length === holdingTickers.length && holdingTickers.every(t => Number.isFinite(entry[mode][t])))) continue;
        const i = rows.indexOf(matching), previousNav = rows[Math.max(0,i-1)].nav;
        const sum = mode => holdingTickers.reduce((total,t) => total+entry[mode][t],0);
        if (Math.abs(sum('since')-(matching.nav/rows[0].nav-1)*100) > .000001 || Math.abs(sum('daily')-(matching.nav/previousNav-1)*100) > .000001) continue;
        contributionRows.set(entry.date,entry);
      }
    }
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
    chart.insertAdjacentHTML('afterend', `<p class="source-note peer-hint">Hover or tap for values. Use the arrow keys when the chart is focused.</p><div id="peer-method" class="peer-method" hidden><p>We follow each team’s published holdings through both rounds, including the rebalance at the 6 November close. Each portfolio starts at 100 on 16 October.</p><details><summary>Comparison method</summary><p>We value the shares held in each round at daily USD closing prices, including dividends from the ex-date. At the rebalance, the new shares and cash take over. Cash earns no interest; estimates use zero trading fees and taxes. Peer round returns are linked at the 6 November close, so differences between published starting NAVs and our reconstruction do not create a gain or loss on the chart.</p><p>Round 2 holdings checked on 11 November 2026. Prices update each trading day. We use vendor dividend events supplemented by documented distributions; source differences can still affect the estimates. The code records each rebalance reconciliation. Official results come from Bloomberg and the course team.</p><p>The other teams are labelled A–D throughout this chart.</p></details><p id="peer-through" class="source-note"></p></div>`);
    const legend = document.querySelector('#peer-legend');
    let contributionMode = 'since';
    const contributionControls = document.createElement('div'); contributionControls.className = 'contribution-controls';
    contributionControls.innerHTML = '<span>Holding contributions</span><div role="group" aria-label="Contribution period"><button type="button" data-period="since" aria-pressed="true">Since inception</button><button type="button" data-period="daily" aria-pressed="false">That day</button></div>';
    legend.after(contributionControls);
    const plot = document.createElement('div'); plot.className = 'peer-plot with-contributions';
    chart.before(plot); plot.append(chart);
    const tooltip = document.createElement('div'); tooltip.className = 'peer-tooltip'; tooltip.id = 'peer-tooltip'; tooltip.hidden = true; tooltip.setAttribute('role', 'tooltip');
    tooltip.innerHTML = '<strong id="peer-selected-date"></strong><div id="peer-readout"></div>';
    plot.append(tooltip);
    chart.setAttribute('tabindex', '0'); chart.setAttribute('role', 'group'); chart.setAttribute('aria-describedby', 'peer-tooltip');
    let transition;
    const hideTooltip = () => { tooltip.hidden = true; chart.querySelector('.peer-cursor')?.replaceChildren(); };
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
      selected = Math.max(0, Math.min(data.dates.length-1, index));
      document.querySelector('#peer-selected-date').textContent = dateLabel(data.dates[selected]);
      const cx = x(selected);
      chart.querySelector('.peer-cursor').innerHTML = `<path d="M${cx} 25V290" stroke="#657780" stroke-dasharray="3 5"/>` + shown.map(s => `<circle cx="${cx}" cy="${y(s.values[selected])}" r="5" fill="${s.colour}" stroke="#f7f5ef" stroke-width="2"/>`).join('');
      const readout = document.querySelector('#peer-readout'); readout.replaceChildren();
      shown.forEach(s => {
        const item = document.createElement('div'); item.className = 'peer-reading'; item.style.setProperty('--series-colour', s.colour);
        const name = document.createElement('span'); name.textContent = s.name;
        const value = document.createElement('strong'); value.textContent = pct(s.values[selected]-100);
        const indexValue = document.createElement('small'); indexValue.textContent = `${s.values[selected].toFixed(2)} indexed value`;
        item.append(name,value,indexValue); readout.append(item);
      });
      tooltip.classList.toggle('has-contributions', !comparing);
      tooltip.classList.remove('expanded-holdings');
      if (!comparing) {
        const entry = contributionRows.get(data.dates[selected]);
        const section = document.createElement('div'); section.className = 'contribution-detail';
        if (entry) {
          const values = entry[contributionMode];
          const magnitude = Math.max(...Object.values(values).map(Math.abs), .000001);
          const title = document.createElement('p'); title.textContent = contributionMode === 'since' ? 'Return drivers since inception' : 'Return drivers for this close'; section.append(title);
          const list = document.createElement('div'); list.className = 'contribution-list';
          const visibleTickers = data.dates[selected] <= '2026-11-06' ? holdingTickers.slice(0,6) : [...holdingTickers];
          tooltip.classList.toggle('expanded-holdings', visibleTickers.length > 6);
          visibleTickers.sort((a,b) => values[b]-values[a]).forEach(t => {
            const row = document.createElement('div'); row.className = 'contribution-row';
            const label = document.createElement('span'); label.textContent = t;
            const track = document.createElement('span'); track.className = 'contribution-track';
            const bar = document.createElement('span'); bar.className = values[t] < 0 ? 'negative' : 'positive';
            bar.style.width = Math.abs(values[t])/magnitude*50+'%'; bar.style.left = (values[t]<0 ? 50-Math.abs(values[t])/magnitude*50 : 50)+'%'; track.append(bar);
            const value = document.createElement('span'); value.textContent = pct(values[t]).replace('%',' pp');
            row.append(label,track,value); list.append(row);
          });
          const total = document.createElement('p'); total.className = 'contribution-total'; total.textContent = (contributionMode === 'since' ? 'Return since inception: ' : 'Return for this close: ')+pct(Object.values(values).reduce((a,b)=>a+b,0));
          const note = document.createElement('small'); note.textContent = 'Percentage points · Includes dividends receivable. Cash contributes 0; displayed values are rounded.';
          section.append(list,total,note);
        } else { section.textContent = 'Holding breakdown unavailable for this close.'; }
        readout.append(section);
      }
      tooltip.hidden = false;
      const px = cx / chart.viewBox.baseVal.width * plot.clientWidth;
      const left = px + tooltip.offsetWidth + 24 > plot.clientWidth ? px - tooltip.offsetWidth - 16 : px + 16;
      tooltip.style.left = Math.max(4, Math.min(left, plot.clientWidth-tooltip.offsetWidth-4)) + 'px';
      tooltip.style.top = '12px';
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
      const rebalanceIndex = data.dates.indexOf('2026-11-06');
      if (rebalanceIndex >= 0 && rebalanceIndex < data.dates.length-1) chart.insertAdjacentHTML('beforeend', `<path d="M${x(rebalanceIndex)} 30V290" stroke="#a59577" stroke-dasharray="3 5"/><text x="${x(rebalanceIndex)-6}" y="22" text-anchor="end">Round 2</text>`);
      chart.setAttribute('aria-label', `${comparing?'Five-team portfolio comparison':'Meridian portfolio performance'}, indexed to 100. Use left and right arrow keys to explore dates.`);
      hideTooltip();
    }
    document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
      if (comparing === (button.dataset.view === 'peers')) return;
      comparing = button.dataset.view === 'peers';
      document.querySelectorAll('[data-view]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      contributionControls.hidden = comparing;
      plot.classList.toggle('with-contributions', !comparing);
      legend.hidden = !comparing; document.querySelector('#peer-method').hidden = !comparing;
      selected = (comparing ? peers : own).dates.length-1; render();
      transition?.cancel();
      if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
        transition = plot.animate([{opacity: .2, transform: 'translateY(5px)'}, {opacity: 1, transform: 'translateY(0)'}], {duration: 240, easing: 'cubic-bezier(.22,1,.36,1)'});
      }
    }));
    contributionControls.querySelectorAll('button').forEach(button => button.addEventListener('click', () => {
      contributionMode = button.dataset.period;
      contributionControls.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      inspect(selected);
    }));
    const pointAt = event => {
      const point = chart.createSVGPoint(); point.x=event.clientX; point.y=event.clientY;
      const local = point.matrixTransform(chart.getScreenCTM().inverse());
      let closest=0; data.dates.forEach((_,i) => {if(Math.abs(x(i)-local.x)<Math.abs(x(closest)-local.x))closest=i;}); inspect(closest);
    };
    chart.addEventListener('pointermove', pointAt);
    chart.addEventListener('pointerdown', pointAt);
    chart.addEventListener('pointerleave', event => { if (event.pointerType !== 'touch') hideTooltip(); });
    chart.addEventListener('blur', hideTooltip);
    chart.addEventListener('keydown', event => {
      const targets = {ArrowLeft: selected-1, ArrowRight: selected+1, Home: 0, End: data.dates.length-1};
      if (event.key === 'Escape') { hideTooltip(); return; }
      if (event.key in targets) { event.preventDefault(); inspect(targets[event.key]); }
    });
    document.addEventListener('pointerdown', event => { if (!plot.contains(event.target)) hideTooltip(); });
    document.querySelector('#tracking-empty').hidden = true; panel.hidden = false; render();
    let previousWidth = chart.clientWidth;
    new ResizeObserver(() => { if (chart.clientWidth !== previousWidth) { previousWidth = chart.clientWidth; render(); } }).observe(chart);
  } catch {
    document.querySelector('#tracking-status').textContent = 'Valuations unavailable';
  }
})();
