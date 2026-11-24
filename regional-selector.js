// Selector compacto de comunidad en Trámites. Sin seguimiento ni dependencias.
(() => {
  const select = document.getElementById('pb-territory-select');
  const button = document.getElementById('pb-territory-go');
  if (!select || !button) return;
  const go = () => {
    const url = select.value;
    if (!url || !/^\/comunidades\/[a-z0-9-]+\/$/.test(url)) {
      select.focus();
      return;
    }
    window.location.assign(url);
  };
  button.addEventListener('click', go);
  select.addEventListener('change', () => {
    button.disabled = !select.value;
  });
  button.disabled = true;
})();
