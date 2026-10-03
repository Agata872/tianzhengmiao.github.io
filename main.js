/* Progressive enhancement: every page remains readable without JavaScript. */
(() => {
  'use strict';
  const root = document.documentElement;
  root.classList.add('has-js');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const toast = document.querySelector('.toast');
  let toastTimer;
  function announce(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('is-visible'), 3200);
  }

  const themeToggle = document.querySelector('.theme-toggle');
  function syncTheme() {
    const dark = root.dataset.theme !== 'light';
    if (themeToggle) {
      themeToggle.setAttribute('aria-pressed', String(dark));
      themeToggle.setAttribute('aria-label', 'Switch to ' + (dark ? 'light' : 'dark') + ' theme');
    }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = dark ? '#0c1014' : '#f5f6f2';
  }
  syncTheme();
  themeToggle?.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    try { localStorage.setItem('tm-theme', root.dataset.theme); } catch (_) { /* Optional persistence. */ }
    syncTheme();
  });

  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.nav-links');
  function setMenu(open, returnFocus = false) {
    if (!menuToggle || !nav) return;
    menuToggle.setAttribute('aria-expanded', String(open));
    menuToggle.setAttribute('aria-label', (open ? 'Close' : 'Open') + ' navigation');
    nav.classList.toggle('is-open', open);
    if (returnFocus) menuToggle.focus();
  }
  menuToggle?.addEventListener('click', () => setMenu(menuToggle.getAttribute('aria-expanded') !== 'true'));
  nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menuToggle?.getAttribute('aria-expanded') === 'true') setMenu(false, true);
  });
  document.addEventListener('click', event => {
    if (menuToggle?.getAttribute('aria-expanded') === 'true' && !event.target.closest('.site-nav')) setMenu(false);
  });
  window.matchMedia('(min-width: 801px)').addEventListener('change', event => {
    if (event.matches) setMenu(false);
  });

  // Collection state is independent. Search includes full authors, notes, and titles.
  document.querySelectorAll('[data-filter-scope]').forEach(scope => {
    const items = [...scope.querySelectorAll('[data-filter-item]')];
    const buttons = [...scope.querySelectorAll('[data-filter]')];
    const search = scope.querySelector('[data-search]');
    const year = scope.querySelector('[data-year-filter]');
    const empty = scope.querySelector('.empty-state');
    const status = scope.querySelector('.filter-status');
    const count = scope.querySelector('[data-result-count]');
    let category = 'all';
    const searchText = new Map(items.map(item => [item, item.textContent.toLocaleLowerCase()]));
    function apply() {
      const query = (search?.value || '').trim().toLocaleLowerCase();
      let visible = 0;
      items.forEach(item => {
        const categoryMatch = category === 'all' || (item.dataset.categories || '').split(' ').includes(category);
        const yearMatch = !year || year.value === 'all' || item.dataset.year === year.value;
        const searchMatch = query.split(/\s+/).every(term => searchText.get(item).includes(term));
        item.hidden = !(categoryMatch && yearMatch && searchMatch);
        if (!item.hidden) visible++;
      });
      buttons.forEach(button => {
        const selected = button.dataset.filter === category;
        button.classList.toggle('is-selected', selected);
        button.setAttribute('aria-pressed', String(selected));
      });
      const noun = scope.dataset.filterScope === 'publications' ? 'paper' : scope.dataset.filterScope === 'notes' ? 'note' : 'project';
      const message = visible + ' ' + noun + (visible === 1 ? '' : 's');
      if (count) count.textContent = message;
      if (status) status.textContent = message + ' shown';
      if (empty) empty.hidden = visible > 0;
    }
    buttons.forEach(button => button.addEventListener('click', () => { category = button.dataset.filter; apply(); }));
    search?.addEventListener('input', apply);
    year?.addEventListener('change', apply);
    function reset() {
      category = 'all';
      if (search) search.value = '';
      if (year) year.value = 'all';
      apply();
    }
    scope.querySelector('[data-reset-filters]')?.addEventListener('click', () => { reset(); (search || buttons[0])?.focus(); });
    scope.addEventListener('reveal-item', reset);
    apply();
  });

  function revealNote() {
    if (!location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target?.classList.contains('post')) return;
    target.closest('[data-filter-scope]')?.dispatchEvent(new Event('reveal-item'));
    const details = target.querySelector('details');
    if (details) details.open = true;
    requestAnimationFrame(() => target.scrollIntoView({ behavior: reducedMotion.matches ? 'instant' : 'smooth', block: 'start' }));
  }
  revealNote();
  window.addEventListener('hashchange', revealNote);

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(text); return true; } catch (_) { /* Local preview fallback. */ }
    }
    const previousFocus = document.activeElement;
    const field = document.createElement('textarea');
    field.value = text;
    field.setAttribute('aria-label', 'Copy text');
    Object.assign(field.style, { position: 'fixed', left: '0', top: '0', opacity: '0', pointerEvents: 'none' });
    (document.querySelector('dialog[open]') || document.body).append(field);
    field.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch (_) { /* Provide manual selection. */ }
    field.remove();
    previousFocus?.focus({ preventScroll: true });
    return copied;
  }
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const copied = await copyText(button.dataset.copy);
      announce(copied ? 'Email address copied.' : 'Email: ' + button.dataset.copy);
    });
  });

  const citationDialog = document.querySelector('.citation-dialog');
  const citationCode = document.querySelector('#citation-code');
  const citationFeedback = document.querySelector('.citation-feedback');
  document.querySelectorAll('[data-citation]').forEach(button => {
    button.addEventListener('click', () => {
      citationCode.textContent = button.dataset.citation;
      citationFeedback.textContent = '';
      citationDialog.showModal();
    });
  });
  citationDialog?.querySelector('[data-close-dialog]')?.addEventListener('click', () => citationDialog.close());
  citationDialog?.querySelector('[data-copy-citation]')?.addEventListener('click', async () => {
    const copied = await copyText(citationCode.textContent);
    citationFeedback.textContent = copied ? 'BibTeX copied.' : 'Select the citation above and copy it manually.';
    if (!copied) {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(citationCode);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  });
  const imageDialog = document.querySelector('.image-dialog');
  document.querySelectorAll('[data-enlarge]').forEach(link => {
    link.addEventListener('click', event => {
      if (!imageDialog?.showModal) return;
      event.preventDefault();
      const original = link.querySelector('img');
      const expanded = imageDialog.querySelector('img');
      expanded.src = link.href;
      expanded.alt = original.alt;
      imageDialog.querySelector('p').textContent = link.parentElement.querySelector('figcaption')?.textContent || original.alt;
      imageDialog.showModal();
    });
  });
  imageDialog?.querySelector('[data-close-image]')?.addEventListener('click', () => imageDialog.close());
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.addEventListener('click', event => {
      const box = dialog.getBoundingClientRect();
      if (event.target === dialog && (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom)) dialog.close();
    });
  });

  // A conceptual topology: distance changes line emphasis, never claimed throughput.
  const network = document.querySelector('[data-network]');
  if (network) {
    const svg = network.querySelector('svg');
    const user = network.querySelector('.mobile-user');
    const nodes = [...network.querySelectorAll('[data-node]')];
    const lines = [...network.querySelectorAll('[data-link]')];
    const slider = network.querySelector('input[type="range"]');
    const readout = network.querySelector('.network-readout');
    const pause = network.querySelector('[data-network-pause]');
    let selected = null;
    let userPosition = { x: 250, y: 210 };
    let manualPause = false;
    let visible = true;
    let pointerFrame = 0;
    function draw(x, y) {
      userPosition = { x: Math.max(50, Math.min(450, x)), y: Math.max(40, Math.min(300, y)) };
      user.setAttribute('transform', 'translate(' + userPosition.x + ' ' + userPosition.y + ')');
      lines.forEach((line, i) => {
        line.setAttribute('x2', String(userPosition.x));
        line.setAttribute('y2', String(userPosition.y));
        const distance = Math.hypot(userPosition.x - Number(nodes[i].dataset.x), userPosition.y - Number(nodes[i].dataset.y));
        line.style.opacity = String(Math.max(.12, .65 - distance / 600));
        line.classList.toggle('is-highlighted', selected === i);
        line.classList.toggle('is-dimmed', selected !== null && selected !== i);
      });
    }
    function inspect(index) {
      selected = selected === index ? null : index;
      nodes.forEach((node, i) => node.setAttribute('aria-pressed', String(i === selected)));
      readout.textContent = selected === null ? 'Shared coverage. Distributed intelligence.' : 'AP.' + String(selected + 1).padStart(2, '0') + ' ↔ USER.01 / Select again to see all links.';
      draw(userPosition.x, userPosition.y);
    }
    nodes.forEach((node, i) => {
      node.addEventListener('click', () => inspect(i));
      node.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(i); }
      });
    });
    slider.addEventListener('input', () => {
      const value = Number(slider.value) / 100;
      draw(60 + value * 380, 210 - Math.sin(value * Math.PI * 2) * 65);
    });
    svg.addEventListener('pointermove', event => {
      if (event.pointerType !== 'mouse' || event.target.closest('[data-node]')) return;
      if (pointerFrame) cancelAnimationFrame(pointerFrame);
      pointerFrame = requestAnimationFrame(() => {
        const point = svg.createSVGPoint();
        point.x = event.clientX;
        point.y = event.clientY;
        const local = point.matrixTransform(svg.getScreenCTM().inverse());
        draw(local.x, local.y);
        slider.value = String(Math.round((userPosition.x - 50) / 400 * 100));
        pointerFrame = 0;
      });
    });
    function syncAnimation() {
      const paused = manualPause || reducedMotion.matches || !visible || document.hidden;
      network.classList.toggle('is-paused', paused);
      pause.setAttribute('aria-pressed', String(manualPause || reducedMotion.matches));
      pause.setAttribute('aria-label', reducedMotion.matches ? 'Signal animation paused by reduced motion preference' : manualPause ? 'Resume signal animation' : 'Pause signal animation');
      pause.textContent = manualPause || reducedMotion.matches ? '▷' : 'Ⅱ';
      pause.disabled = reducedMotion.matches;
    }
    pause.addEventListener('click', () => { manualPause = !manualPause; syncAnimation(); });
    reducedMotion.addEventListener('change', syncAnimation);
    document.addEventListener('visibilitychange', syncAnimation);
    if ('IntersectionObserver' in window) new IntersectionObserver(entries => { visible = entries[0].isIntersecting; syncAnimation(); }).observe(network);
    draw(250, 210);
    syncAnimation();
  }

  const progress = document.querySelector('.reading-progress');
  const sectionLinks = [...document.querySelectorAll('.home-page .nav-link[href^="#"]')];
  const sections = sectionLinks.map(link => document.getElementById(link.hash.slice(1))).filter(Boolean);
  let scrollPending = false;
  function updateScroll() {
    const range = root.scrollHeight - window.innerHeight;
    if (progress) progress.style.transform = 'scaleX(' + (range > 0 ? Math.min(1, window.scrollY / range) : 0) + ')';
    if (sections.length) {
      let current = sections[0].id;
      sections.forEach(section => { if (section.getBoundingClientRect().top <= 150) current = section.id; });
      sectionLinks.forEach(link => {
        const active = link.hash === '#' + current;
        link.classList.toggle('is-active', active);
        if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      });
    }
    scrollPending = false;
  }
  window.addEventListener('scroll', () => {
    if (!scrollPending) { scrollPending = true; requestAnimationFrame(updateScroll); }
  }, { passive: true });
  window.addEventListener('resize', updateScroll);
  updateScroll();
  document.querySelectorAll('[data-current-year]').forEach(item => { item.textContent = String(new Date().getFullYear()); });
})();
