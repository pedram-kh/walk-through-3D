// Stop loading: each stop is its own download (stops/<id>/stop.js and its files).
// While the visitor views stop N, stops N+1 and N+2 load in the background, one at a time,
// nearest first, so each stop is ready before its section scrolls into view (and N-1, for
// a visitor who lands further down the page). Nothing is unloaded once loaded. A stop that
// is not ready, or failed, shows its poster: the section's background image, which the
// canvas covers once the stop is ready.
const LOAD_AHEAD = 2;

export class StopLoader {
  constructor({ views, makeContext, makeRenderer, onLoaded, onError }) {
    Object.assign(this, { views, makeContext, makeRenderer, onLoaded, onError });
    for (const view of views) view.status = 'idle';
    this.loading = null;
  }

  // Load what the visitor needs around stop `index`; each finished load starts the next one.
  // Returns the load in progress, if any.
  focus(index) {
    this.index = index;
    if (this.loading) return this.loading;
    const wanted = [index, ...Array.from({ length: LOAD_AHEAD }, (_, k) => index + 1 + k), index - 1]
      .filter(i => i >= 0 && i < this.views.length);
    const next = wanted.map(i => this.views[i]).find(view => view.status === 'idle');
    if (!next) return null;
    const loading = this.load(next).finally(() => {
      this.loading = null;
      if (!this.disposed) this.focus(this.index);
    });
    this.loading = loading;
    return loading;
  }

  async load(view) {
    view.status = 'loading';
    try {
      const module = await import(`../${view.stop.dir}stop.js`);
      const stop = await module.load(this.makeContext(view));
      if (view.status !== 'loading') { stop.dispose(); return; }   // disposed while loading
      view.renderer = this.makeRenderer(view);
      view.module = stop;
      view.holder.add(stop.group);
      view.status = 'ready';
      this.onLoaded(view);
    } catch (error) {
      view.status = 'failed';
      view.error = error;
      this.onError(view, error);
    }
  }

  // Give up on a stop (its graphics context was lost): the poster stays.
  fail(view) {
    this.unload(view);
    view.status = 'failed';
  }

  unload(view) {
    if (view.module) { view.holder.remove(view.module.group); view.module.dispose(); }
    view.module = null;
    if (view.renderer) { view.renderer.dispose(); view.renderer.domElement.remove(); }
    view.renderer = null;
    view.status = 'idle';
  }

  dispose() {
    this.disposed = true;
    for (const view of this.views) this.unload(view);
  }
}
