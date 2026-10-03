/* Interactive schematic of a cell-free network and its bipartite graph.
   The figure is complete static SVG without this script; the script adds dragging, selection and view switching. */
(() => {
  'use strict';
  document.documentElement.classList.add('has-js');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
  const copy = list => list.map(point => point.slice());
  const ease = t => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

  const STEPS = [
    'Step 1 of 3 · Input: the channel state information H, one entry per AP–user link, enters the graph.',
    'Step 2 of 3 · Layer l → l+1: the feature of every edge (AP m, user k) is updated.',
    'Step 3 of 3 · Output: the precoder W, computed at the CPU.'
  ];
  const DEFAULT = {
    system: 'Drag a user, or focus it and use the arrow keys: the channels H change, shown here as line weight. Select a node to highlight its links.',
    graph: 'Every AP–user wireless link is an edge of the bipartite graph. Select a node to see its edges, or step through the layers.'
  };

  document.querySelectorAll('[data-network]').forEach(init);

  function init(figure) {
    const svg = figure.querySelector('svg');
    const layout = JSON.parse(figure.dataset.layout);
    const aps = [...figure.querySelectorAll('.ap')];
    const users = [...figure.querySelectorAll('.user')];
    const links = [...figure.querySelectorAll('.link')];
    const readout = figure.querySelector('[data-readout]');
    const stepButton = figure.querySelector('[data-advance]');
    const viewButtons = [...figure.querySelectorAll('[data-view-btn]')];

    let view = figure.dataset.view;
    let step = 0;
    let selected = null;
    let frame = 0;
    let drag = null;
    let justDragged = false;
    const position = { aps: copy(layout[view].aps), users: copy(layout[view].users) };
    let savedUsers = copy(layout.system.users);
    let blend = view === 'system' ? 1 : 0; // 1: links attach to the icons, 0: to the node centres

    const weight = (a, u) => 1 / (1 + Math.pow(Math.hypot(a[0] - u[0], a[1] - u[1]) / layout.scale, 2));
    const related = (m, k) => selected && (selected.kind === 'ap' ? selected.index === m : selected.index === k);

    function draw() {
      aps.forEach((node, i) => node.setAttribute('transform', 'translate(' + position.aps[i] + ')'));
      users.forEach((node, i) => node.setAttribute('transform', 'translate(' + position.users[i] + ')'));
      links.forEach(line => {
        const m = Number(line.dataset.m);
        const k = Number(line.dataset.k);
        const a = position.aps[m];
        const u = position.users[k];
        const w = weight(a, u);
        line.setAttribute('x1', a[0]);
        line.setAttribute('y1', a[1] + layout.anchor[0] * blend);
        line.setAttribute('x2', u[0]);
        line.setAttribute('y2', u[1] + layout.anchor[1] * blend);
        const base = step >= 2 ? .4 + .55 * w : .1 + .8 * w;
        line.style.strokeWidth = (.5 + 2 * w).toFixed(2);
        line.style.opacity = (related(m, k) ? Math.max(.6, base) : base).toFixed(2);
        line.classList.toggle('is-related', Boolean(related(m, k)));
      });
    }

    function message() {
      if (selected) {
        const n = selected.index + 1;
        return selected.kind === 'ap'
          ? 'AP ' + n + ' has a wireless link to each of the ' + users.length + ' users: ' + users.length + ' edges in the graph.'
          : 'User ' + n + ' has a wireless link to each of the ' + aps.length + ' access points: ' + aps.length + ' edges in the graph.';
      }
      return view === 'graph' && step ? STEPS[step - 1] : DEFAULT[view];
    }

    function refresh() {
      figure.dataset.view = view;
      figure.dataset.step = String(step);
      figure.classList.toggle('has-selection', Boolean(selected));
      aps.forEach((node, i) => {
        const on = selected && selected.kind === 'ap' && selected.index === i;
        node.classList.toggle('is-selected', Boolean(on));
        node.setAttribute('aria-pressed', String(Boolean(on)));
      });
      users.forEach((node, i) => {
        const on = selected && selected.kind === 'user' && selected.index === i;
        node.classList.toggle('is-selected', Boolean(on));
        node.setAttribute('aria-pressed', String(Boolean(on)));
      });
      viewButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.viewBtn === view)));
      stepButton.disabled = view !== 'graph';
      stepButton.textContent = step === 0 ? 'Step through the layers ▸' : step < 3 ? 'Next step ▸' : 'Restart ↺';
      readout.textContent = message();
      draw();
    }

    function animateTo(target, blendTo) {
      cancelAnimationFrame(frame);
      const from = { aps: copy(position.aps), users: copy(position.users) };
      const blendFrom = blend;
      const start = performance.now();
      const duration = reduced.matches ? 0 : 600;
      const tick = now => {
        const t = duration ? Math.min(1, (now - start) / duration) : 1;
        const eased = ease(t);
        blend = blendFrom + (blendTo - blendFrom) * eased;
        ['aps', 'users'].forEach(group => position[group].forEach((point, i) => {
          point[0] = from[group][i][0] + (target[group][i][0] - from[group][i][0]) * eased;
          point[1] = from[group][i][1] + (target[group][i][1] - from[group][i][1]) * eased;
        }));
        draw();
        if (t < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    }

    function setView(next) {
      if (next === view) return;
      if (view === 'system') savedUsers = copy(position.users);
      view = next;
      step = 0;
      refresh();
      animateTo(next === 'system' ? { aps: layout.system.aps, users: savedUsers } : layout.graph, next === 'system' ? 1 : 0);
    }

    function toggle(kind, index) {
      selected = selected && selected.kind === kind && selected.index === index ? null : { kind, index };
      refresh();
    }

    function toSvg(event) {
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      return point.matrixTransform(svg.getScreenCTM().inverse());
    }

    function moveUser(k, x, y) {
      position.users[k] = [clamp(x, layout.bounds[0], layout.bounds[2]), clamp(y, layout.bounds[1], layout.bounds[3])];
      draw();
    }

    function makeInteractive(node, kind, index, label) {
      node.setAttribute('role', 'button');
      node.setAttribute('tabindex', '0');
      node.setAttribute('aria-pressed', 'false');
      node.setAttribute('aria-label', label);
      node.addEventListener('click', () => {
        if (justDragged) { justDragged = false; return; }
        toggle(kind, index);
      });
      node.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); toggle(kind, index); return; }
        const delta = { ArrowLeft: [-12, 0], ArrowRight: [12, 0], ArrowUp: [0, -12], ArrowDown: [0, 12] }[event.key];
        if (kind === 'user' && view === 'system' && delta) {
          event.preventDefault();
          moveUser(index, position.users[index][0] + delta[0], position.users[index][1] + delta[1]);
        }
      });
    }

    aps.forEach((node, i) => makeInteractive(node, 'ap', i, 'Access point ' + (i + 1) + ': show its links'));
    users.forEach((node, k) => {
      makeInteractive(node, 'user', k, 'User ' + (k + 1) + ': show its links; in the system view, drag or use the arrow keys to move');
      node.addEventListener('pointerdown', event => {
        if (view !== 'system') return;
        drag = { k, x: event.clientX, y: event.clientY, moved: false };
        node.setPointerCapture(event.pointerId);
      });
      node.addEventListener('pointermove', event => {
        if (!drag || drag.k !== k) return;
        if (!drag.moved && Math.hypot(event.clientX - drag.x, event.clientY - drag.y) < 4) return;
        drag.moved = true;
        const point = toSvg(event);
        moveUser(k, point.x, point.y);
      });
      const end = () => {
        justDragged = Boolean(drag && drag.moved);
        drag = null;
        if (justDragged) setTimeout(() => { justDragged = false; }, 0);
      };
      node.addEventListener('pointerup', end);
      node.addEventListener('pointercancel', end);
    });

    viewButtons.forEach(button => button.addEventListener('click', () => setView(button.dataset.viewBtn)));
    stepButton.addEventListener('click', () => {
      selected = null;
      step = (step + 1) % 4;
      refresh();
    });
    refresh();
  }
})();
