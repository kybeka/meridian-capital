const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#navigation');
menuButton.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(open));
  navigation.classList.toggle('open', open);
});
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  menuButton.setAttribute('aria-expanded', 'false');
  navigation.classList.remove('open');
}));
document.querySelectorAll('[role="tablist"]').forEach(list => {
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  function activate(tab) {
    tabs.forEach(item => {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
    });
  }
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', event => {
      let target;
      if (event.key === 'ArrowRight') target = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') target = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') target = 0;
      if (event.key === 'End') target = tabs.length - 1;
      if (target !== undefined) {
        event.preventDefault();
        activate(tabs[target]);
        tabs[target].focus();
      }
    });
  });
});

const sectionLinks = [...navigation.querySelectorAll('a')];
const sectionObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    sectionLinks.forEach(link => {
      if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  });
}, { rootMargin: '-15% 0px -60% 0px' });
sectionLinks.forEach(link => {
  const section = link.pathname === location.pathname && link.hash ? document.querySelector(link.hash) : null;
  if (section) sectionObserver.observe(section);
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
    menuButton.setAttribute('aria-expanded', 'false');
    navigation.classList.remove('open');
    menuButton.focus();
  }
});

const measureButtons = [...document.querySelectorAll('[data-measure]')];
measureButtons.forEach(button => button.addEventListener('click', () => {
  const measure = button.dataset.measure;
  measureButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  document.querySelectorAll('.allocation-row').forEach(row => {
    const value = row.dataset[measure];
    row.querySelector('.allocation-track span').style.width = value + '%';
    row.querySelector('strong').textContent = value + '%';
  });
  document.querySelector('#allocation-description').textContent = measure === 'capital'
    ? 'Share of total capital allocated to each ETF.'
    : 'Share of estimated portfolio variance contributed by each ETF.';
}));

const globe = document.querySelector('.hero-map');
if (globe) {
  const markers = [...globe.querySelectorAll('.orbit-traveller')];
  const pauseButton = document.querySelector('.globe-pause');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const land = globe.querySelector('.globe-land');
  const limb = globe.querySelector('.globe-land-limb');
  const grid = globe.querySelector('.globe-grid');
  const radians = Math.PI / 180;
  const geography = globeLandPoints.map(([longitude, latitude]) => ({
    longitude: longitude * radians,
    sine: Math.sin(latitude * radians),
    cosine: Math.cos(latitude * radians)
  }));
  let lastSurfaceTime = -Infinity;
  function drawSurface(time) {
    if (time - lastSurfaceTime < 40 && time >= lastSurfaceTime) return;
    lastSurfaceTime = time;
    const rotation = 15 * radians + time / 240000 * Math.PI * 2;
    const project = (longitude, sine, cosine) => {
      const relative = longitude - rotation;
      return {x: 270 + 167 * cosine * Math.sin(relative), y: 220 - 167 * sine, z: cosine * Math.cos(relative)};
    };
    let near = '', edge = '';
    geography.forEach(point => {
      const p = project(point.longitude, point.sine, point.cosine);
      if (p.z <= 0) return;
      const radius = (1.1 * Math.sqrt(p.z)).toFixed(2);
      const dot = 'M' + (p.x - Number(radius)).toFixed(2) + ' ' + p.y.toFixed(2) + 'a' + radius + ' ' + radius + ' 0 1 0 ' + (2 * Number(radius)).toFixed(2) + ' 0a' + radius + ' ' + radius + ' 0 1 0 -' + (2 * Number(radius)).toFixed(2) + ' 0';
      if (p.z > .3) near += dot;
      else edge += dot;
    });
    land.setAttribute('d', near);
    limb.setAttribute('d', edge);
    let lines = '';
    function line(coordinates) {
      let drawing = false;
      coordinates.forEach(([lon, lat]) => {
        const p = project(lon * radians, Math.sin(lat * radians), Math.cos(lat * radians));
        if (p.z < 0) { drawing = false; return; }
        lines += (drawing ? 'L' : 'M') + p.x.toFixed(2) + ' ' + p.y.toFixed(2);
        drawing = true;
      });
    }
    for (let lon = -180; lon < 180; lon += 30) line(Array.from({length: 91}, (_, i) => [lon, -90 + 2 * i]));
    for (let lat = -60; lat <= 60; lat += 30) line(Array.from({length: 181}, (_, i) => [-180 + 2 * i, lat]));
    grid.setAttribute('d', lines);
  }
  let elapsed = 0;
  let lastTime = null;
  let frame = null;
  let visible = false;
  let paused = false;
  function draw() {
    drawSurface(elapsed);
    const angle = Math.PI / 6 + elapsed / 120000 * Math.PI * 2;
    const depth = Math.sin(angle);
    const x = 270 + 224 * Math.cos(angle);
    const y = 220 + 83 * depth;
    markers.forEach(marker => {
      marker.setAttribute('transform', 'translate(' + x + ' ' + y + ') scale(' + (.9 + .15 * depth) + ')');
      marker.style.opacity = String(.8 + .2 * depth);
    });
  }
  function tick(time) {
    if (lastTime !== null) elapsed = (elapsed + time - lastTime) % 240000;
    lastTime = time;
    draw();
    frame = requestAnimationFrame(tick);
  }
  function sync() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    lastTime = null;
    if (visible && !document.hidden && !paused && !reducedMotion.matches) frame = requestAnimationFrame(tick);
  }
  new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting;
    sync();
  }).observe(globe);
  pauseButton.addEventListener('click', () => {
    paused = !paused;
    pauseButton.setAttribute('aria-pressed', String(paused));
    pauseButton.textContent = paused ? 'Resume globe animation' : 'Pause globe animation';
    sync();
  });
  reducedMotion.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  draw();
}
