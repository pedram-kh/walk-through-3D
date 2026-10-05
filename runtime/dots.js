// Progress dots: one per section, vertical, on the left. Each is a jump link: clicking it
// scrolls smoothly to that section. The dot of the section on screen is filled.
export function mountDots(sections) {
  const nav = document.createElement('nav');
  nav.className = 'page-dots';
  nav.setAttribute('aria-label', 'Sections');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const links = sections.map((section, index) => {
    const link = document.createElement('a');
    link.href = '#' + section.id;
    link.setAttribute('aria-label', `${index + 1}: ${section.dataset.title ?? section.id}`);
    link.addEventListener('click', e => {
      e.preventDefault();
      section.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth' });
      history.replaceState(null, '', '#' + section.id);
    });
    nav.append(link);
    return link;
  });
  document.body.append(nav);

  let current = -1;
  return {
    setCurrent(index) {
      if (index === current) return;
      current = index;
      links.forEach((link, i) => i === index ? link.setAttribute('aria-current', 'location') : link.removeAttribute('aria-current'));
    },
    dispose() { nav.remove(); },
  };
}
