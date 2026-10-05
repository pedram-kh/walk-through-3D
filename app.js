// Chooses between the live 3D sections and the plain page with posters.
// Touch devices, reduced motion, data saver and any graphics failure get the posters.
const html = document.documentElement;
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const finePointer = matchMedia('(pointer: fine)');

let page = null, loading = false, failed = false;

const eligible = () => finePointer.matches && !reduced.matches && !navigator.connection?.saveData;

function showPosters(error) {
  page?.dispose();
  page = null;
  html.classList.remove('live');
  if (error) { failed = true; console.warn('Poster fallback:', error.message); }
}

function sync() {
  if (!eligible()) { showPosters(); return; }
  if (page || loading || failed) return;
  loading = true;
  html.classList.add('live');
  import('./runtime/runtime.js')
    .then(m => m.startPage())
    .then(started => {
      if (!eligible()) { started.dispose(); showPosters(); return; }
      page = started;
    })
    .catch(showPosters)
    .finally(() => { loading = false; });
}

reduced.addEventListener('change', sync);
finePointer.addEventListener('change', sync);
sync();
