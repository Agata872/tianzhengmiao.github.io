(() => {
  try {
    const saved = localStorage.getItem('tm-theme');
    if (saved === 'light' || saved === 'dark') document.documentElement.dataset.theme = saved;
  } catch (_) { /* Storage is optional, including on file:// previews. */ }
})();
