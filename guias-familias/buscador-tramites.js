(() => {
  'use strict';
  const field = document.getElementById('pbFindInput');
  const results = document.getElementById('pbFindResults');
  if (!field || !results) return;

  // El mismo índice que utiliza el buscador de ayudas: todas las URLs canónicas
  // publicadas en el sitemap, regeneradas en cada despliegue.
  const normalize = value => (value || '').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim();
  let pages = [];
  let loading = true;
  let unavailable = false;

  const showMessage = message => {
    const p = document.createElement('p');
    p.textContent = message;
    results.append(p);
  };

  function render() {
    const q = normalize(field.value);
    results.replaceChildren();
    if (!q) {
      results.hidden = true;
      return;
    }
    results.hidden = false;
    if (loading) {
      showMessage('Buscando entre las guías publicadas…');
      return;
    }
    if (unavailable) {
      showMessage('No se pudo cargar el buscador. Prueba a recargar la página o utiliza las categorías de abajo.');
      return;
    }
    const words = q.split(' ').filter(Boolean);
    const matches = pages.map(page => {
      const title = normalize(page.title);
      const region = normalize(page.region);
      const slug = normalize(page.url);
      const searchable = normalize([page.title, page.description, page.keywords, page.region, page.url].join(' '));
      if (!words.every(word => searchable.includes(word))) return null;
      const score = words.reduce((total, word) =>
        total + (title.includes(word) ? 6 : 0)
              + (region.includes(word) ? 4 : 0)
              + (slug.includes(word) ? 3 : 0), 0);
      return { page, score };
    }).filter(Boolean).sort((a, b) => b.score - a.score ||
      a.page.title.localeCompare(b.page.title, 'es')).slice(0, 12);

    if (!matches.length) {
      showMessage('No encontramos esa búsqueda. Prueba con menos palabras o consulta las categorías de abajo.');
      return;
    }
    for (const { page } of matches) {
      const a = document.createElement('a');
      a.href = page.url;
      const strong = document.createElement('strong');
      strong.textContent = page.title;
      const small = document.createElement('small');
      small.textContent = page.description || (page.region ? 'Guía de ' + page.region : 'Guía práctica');
      a.append(strong, small);
      results.append(a);
    }
  }

  field.addEventListener('input', render);
  fetch('/site-search-index.json', { cache: 'no-cache' })
    .then(response => {
      if (!response.ok) throw new Error('Índice HTTP ' + response.status);
      return response.json();
    })
    .then(data => {
      if (!Array.isArray(data)) throw new Error('Índice inválido');
      pages = data;
    })
    .catch(() => { unavailable = true; })
    .finally(() => { loading = false; render(); });
})();
