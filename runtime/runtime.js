// Page runtime for the flat version: every stop is a normal full-screen section, one below
// the other, with its own 3D scene drawn on a canvas inside the section, so the scene
// scrolls exactly with its HTML. No camera journeys, no freeze, no black and white, no
// particles. A stop animates (and plays its videos) only while its section is on screen.
// Stops load in order: stop 01 first, then always the two after the one being viewed, so
// each stop is ready before the visitor reaches it (see loader.js).
import * as THREE from 'three';
import { StopLoader } from './loader.js';
import { mountDots } from './dots.js';

const MAX_PIXEL_RATIO = 1.5;
const BACKGROUND = new THREE.Color().setRGB(0.00061, 0.00061, 0.00121);   // the page's black, linear

export async function startPage() {
  const data = await fetch('stops.json').then(r => { if (!r.ok) throw Error('Missing stops.json'); return r.json(); });
  const halfH = Math.tan(THREE.MathUtils.degToRad(data.camera.horizontal_fov_deg) / 2);
  const design = data.camera.design_aspect;
  const cleanup = [];
  const listen = (target, type, fn, options) => {
    target.addEventListener(type, fn, options);
    cleanup.push(() => target.removeEventListener(type, fn, options));
  };
  const mouse = { x: 0, y: 0, inside: false };          // CSS px in the window
  let disposed = false, raf = 0, quality = MAX_PIXEL_RATIO;

  // One view per stop: its section, a layer inside it (canvas and HTML captions), a camera
  // at the stop's rest view, and its own scene and renderer once loaded.
  const views = data.stops.map(stop => {
    const section = document.getElementById(stop.section);
    if (!section) throw Error('Section missing from the page: #' + stop.section);
    const layer = Object.assign(document.createElement('div'), { className: 'scene' });
    layer.setAttribute('aria-hidden', 'true');
    const overlay = Object.assign(document.createElement('div'), { className: 'tags' });
    layer.append(overlay);
    section.prepend(layer);
    const camera = new THREE.PerspectiveCamera(30, 2, 0.1, 200);
    camera.position.fromArray(stop.rest.position);
    camera.quaternion.fromArray(stop.rest.quaternion);
    camera.updateMatrixWorld();
    const holder = new THREE.Group();                    // places the stop as it was built
    holder.position.fromArray(stop.origin);
    holder.quaternion.fromArray(stop.quaternion);
    const scene = new THREE.Scene();
    scene.background = BACKGROUND;
    scene.add(holder);
    return { stop, section, layer, overlay, camera, scene, holder, renderer: null, module: null,
             pointer: { x: 0, y: 0, inside: false }, onScreen: false, frozen: true, dirty: true,
             size: { width: 1, height: 1, pixelScale: 1 } };
  });

  // ---- Sizing: keep the designed frame on any screen (as the hero always did) ----
  function fit(view) {
    const width = view.section.clientWidth || innerWidth, height = view.section.clientHeight || innerHeight;
    const aspect = width / height;
    const tanV = Math.max(halfH / aspect, halfH / design);
    const pixelRatio = Math.min(devicePixelRatio, quality);
    view.camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(tanV));
    view.camera.aspect = aspect;
    view.camera.updateProjectionMatrix();
    view.size = { width, height, pixelScale: height * pixelRatio / (2 * tanV) };
    if (view.renderer) {
      view.renderer.setPixelRatio(pixelRatio);
      view.renderer.setSize(width, height, false);
    }
    view.module?.resize(view.size);
    view.dirty = true;
  }
  function resize() {
    // How the 3D view scales around the screen centre compared with the design frame, so HTML
    // that lines up with 3D objects can follow: left: calc(50% + (X - 50%) * var(--fit-x)).
    const aspect = innerWidth / innerHeight;
    document.documentElement.style.setProperty('--fit-x', String(Math.min(1, design / aspect)));
    document.documentElement.style.setProperty('--fit-y', String(Math.min(1, aspect / design)));
    views.forEach(fit);
  }
  const observer = new ResizeObserver(resize);
  observer.observe(document.body);
  cleanup.push(() => observer.disconnect());
  resize();

  // ---- Which sections are on screen ----
  const visibility = new IntersectionObserver(entries => {
    for (const entry of entries) {
      const view = views.find(v => v.section === entry.target);
      view.onScreen = entry.isIntersecting;
      view.dirty = true;
    }
  });
  views.forEach(view => visibility.observe(view.section));
  cleanup.push(() => visibility.disconnect());

  listen(window, 'pointermove', e => { mouse.x = e.clientX; mouse.y = e.clientY; mouse.inside = true; }, { passive: true });
  listen(document.documentElement, 'pointerleave', () => { mouse.inside = false; });

  // ---- Loading ----
  const loader = new StopLoader({
    views,
    makeContext: view => ({
      dir: view.stop.dir, section: view.section, camera: view.camera, overlay: view.overlay, pointer: view.pointer,
      invalidate: () => { view.dirty = true; },
    }),
    makeRenderer: view => {
      const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
      renderer.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); lose(view); });
      view.layer.prepend(renderer.domElement);
      return renderer;
    },
    onLoaded: view => {
      fit(view);
      view.module.setFrozen(true);
      view.frozen = true;
      view.module.update(0);
      view.renderer.render(view.scene, view.camera);   // first frame drawn before the canvas fades in
      view.section.classList.add('scene-ready');
    },
    onError: (view, error) => console.warn(`Stop ${view.stop.id} failed to load; showing its poster:`, error),
  });
  function lose(view) {
    console.warn(`Stop ${view.stop.id} lost its graphics context; showing its poster.`);
    view.section.classList.remove('scene-ready');
    loader.fail(view);
  }
  const dots = mountDots(views.map(v => v.section));

  // The section the visitor is looking at: the one under the middle of the screen.
  function current() {
    const middle = innerHeight / 2;
    const index = views.findIndex(v => { const r = v.section.getBoundingClientRect(); return r.top <= middle && r.bottom > middle; });
    return index >= 0 ? index : views.findLastIndex(v => v.section.getBoundingClientRect().top <= middle);
  }

  // Stop 01 first: nothing else loads until it is ready.
  await loader.focus(0);
  if (views[0].status !== 'ready') { dispose(); throw views[0].error ?? Error('Stop 01 did not load'); }

  // ---- Frame loop ----
  const diagnostics = { fps: 0, current: 0, live: [], loaded: [], drawCalls: 0, pixelRatio: 0 };
  let last = performance.now(), streak = 0, streakTime = 0, slowFor = 0;
  function frame(now) {
    raf = requestAnimationFrame(frame);
    const wall = (now - last) / 1000, dt = Math.min(wall, 0.05);
    last = now;
    const index = Math.max(0, current());
    dots.setCurrent(index);
    loader.focus(index);
    let drawn = false, drawCalls = 0;
    for (const view of views) {
      if (view.status !== 'ready') continue;
      const live = view.onScreen && !document.hidden;
      if (view.frozen === live) { view.frozen = !live; view.module.setFrozen(!live); view.dirty = true; }
      if (!view.onScreen) continue;
      // The cursor in this section's own view (-1..1), and whether it is over the section.
      const r = view.section.getBoundingClientRect();
      view.pointer.x = (mouse.x - r.left) / r.width * 2 - 1;
      view.pointer.y = 1 - (mouse.y - r.top) / r.height * 2;
      view.pointer.inside = mouse.inside && mouse.y >= r.top && mouse.y < r.bottom;
      const animating = view.module.update(dt);
      if (!animating && !view.dirty) continue;
      view.dirty = false;
      view.renderer.render(view.scene, view.camera);
      drawCalls += view.renderer.info.render.calls;
      drawn = true;
    }
    if (!drawn) { streak = 0; streakTime = 0; return; }

    // Quality guard over continuous rendering: lower the pixel ratio if it stays slow.
    streak++; streakTime += wall;
    if (streak >= 90) {
      diagnostics.fps = streak / streakTime;
      slowFor = diagnostics.fps < 24 ? slowFor + streakTime : 0;
      if (slowFor > 5 && quality > 1) { quality = 1; resize(); slowFor = 0; }
      streak = 0; streakTime = 0;
    }
    Object.assign(diagnostics, {
      current: index, drawCalls, pixelRatio: Math.min(devicePixelRatio, quality),
      live: views.filter(v => v.status === 'ready' && !v.frozen).map(v => v.stop.id),
      loaded: views.filter(v => v.status === 'ready').map(v => v.stop.id),
    });
  }
  // document.documentElement.pageDiagnostics in the console.
  Object.defineProperty(document.documentElement, 'pageDiagnostics', { configurable: true, get: () => ({ ...diagnostics }) });
  raf = requestAnimationFrame(frame);

  function dispose() {
    if (disposed) return;
    disposed = true;
    cancelAnimationFrame(raf);
    cleanup.forEach(fn => fn());
    dots.dispose();
    loader.dispose();
    for (const view of views) { view.layer.remove(); view.section.classList.remove('scene-ready'); }
  }
  return { dispose };
}
