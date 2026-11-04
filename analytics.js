(() => {
  // Vercel Web Analytics para esta web HTML estática (sin Next.js ni npm).
  // Se carga una sola vez en todas las páginas que incluyen /analytics.js.
  if (!window.__pbVercelAnalyticsLoaded) {
    window.__pbVercelAnalyticsLoaded = true;
    window.va = window.va || function () {
      (window.vaq = window.vaq || []).push(arguments);
    };
    if (!document.querySelector('script[src="/_vercel/insights/script.js"]')) {
      const insights = document.createElement('script');
      insights.defer = true;
      insights.src = '/_vercel/insights/script.js';
      document.head.appendChild(insights);
    }
  }
  if (!window.__pbPanelBridgeScriptRequested) {
    window.__pbPanelBridgeScriptRequested = true;
    const bridge = document.createElement('script');
    bridge.src = '/herramientas/panel-bridge.js?v=20261020-1';
    bridge.defer = true;
    document.head.appendChild(bridge);
  }

  if (!window.__papelesBebeGlobalUiLoaded && !document.querySelector('script[src^="/global-ui.js"]')) {
    window.__papelesBebeGlobalUiLoaded = true;
    const ui = document.createElement('script');
    ui.src = '/global-ui.js?v=20261104-preparativos-marketing';
    ui.defer = true;
    document.head.appendChild(ui);
  }

  if (!window.__papelesBebeSharedContextLoaded) {
    window.__papelesBebeSharedContextLoaded = true;
    const sharedContext = document.createElement('script');
    sharedContext.src = '/herramientas/shared-context.js?v=20261015-1';
    sharedContext.defer = true;
    document.head.appendChild(sharedContext);
  }

  if (!window.__papelesBebeToolEnhancementsLoaded) {
    window.__papelesBebeToolEnhancementsLoaded = true;
    const toolEnhancements = document.createElement('script');
    toolEnhancements.src = '/herramientas/tool-enhancements.js?v=20261020-2';
    toolEnhancements.defer = true;
    document.head.appendChild(toolEnhancements);
  }

  if (!window.__papelesBebePersistentStateLoaded) {
    window.__papelesBebePersistentStateLoaded = true;
    const persistentState = document.createElement('script');
    persistentState.src = '/herramientas/persistent-state.js?v=20261019-1';
    persistentState.defer = true;
    document.head.appendChild(persistentState);
  }

  if (!window.__papelesBebeUxFocusLoaded) {
    window.__papelesBebeUxFocusLoaded = true;
    const uxFocus = document.createElement('script');
    uxFocus.src = '/ux-focus.js?v=20261022-contextual1';
    uxFocus.defer = true;
    document.head.appendChild(uxFocus);
  }

  if (!window.__papelesBebeUxHotfixLoaded) {
    window.__papelesBebeUxHotfixLoaded = true;
    const uxHotfix = document.createElement('script');
    uxHotfix.src = '/ux-hotfix.js?v=20261016-1';
    uxHotfix.defer = true;
    document.head.appendChild(uxHotfix);
  }

  if (!window.__papelesBebeQaHotfixLoaded) {
    window.__papelesBebeQaHotfixLoaded = true;
    const qaHotfix = document.createElement('script');
    qaHotfix.src = '/qa-hotfix.js?v=20261016-3';
    qaHotfix.defer = true;
    document.head.appendChild(qaHotfix);
  }

  if (window.location.pathname.startsWith('/api/preparar-tarjeta-sanitaria')) {
    const resultActions = document.createElement('script');
    resultActions.src = '/preparador-tarjeta-sanitaria/resultado-actions.js?v=20261016-1';
    resultActions.defer = true;
    document.head.appendChild(resultActions);
  }

  if (window.location.pathname === '/herramientas/que-me-falta/' || window.location.pathname === '/herramientas/que-me-falta') {
    const valueV2 = document.createElement('script');
    valueV2.src = '/herramientas/que-me-falta/value-v2.js?v=20261016-4';
    valueV2.defer = true;
    document.head.appendChild(valueV2);
  }


  // El simulador UX 3.1 ya presenta los resultados; no inyectar el panel antiguo value-v2.

  if (window.location.pathname.startsWith('/herramientas/')) {
    const p0ux = document.createElement('script');
    p0ux.src = '/herramientas/p0-ux.js?v=20261019-1';
    p0ux.defer = true;
    p0ux.addEventListener('load', () => {
      const simple = document.createElement('script');
      simple.src = '/herramientas/ux-simple.js?v=20261019-1';
      simple.addEventListener('load', () => {
        const progressive=document.createElement('script');
        progressive.src='/herramientas/ux-progresivo.js?v=20261019-1';
        document.head.appendChild(progressive);
      });
      document.head.appendChild(simple);
    });
    document.head.appendChild(p0ux);
  }

  const GA_ID = 'G-YQ7QHVVWZV';
  const STORAGE_KEY = 'papelesbebe_analytics_consent';

  function loadGa4() {
    if (window.__papelesBebeGaLoaded) return;
    window.__papelesBebeGaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function(){ dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { send_page_view: true, allow_google_signals: false, allow_ad_personalization_signals: false });
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
    document.head.appendChild(script);
    const path = window.location.pathname;
    if (path === '/checklist/' || path.startsWith('/checklist/?')) window.gtag('event', 'checklist_start');
    if (path.startsWith('/checklist/completada')) window.gtag('event', 'checklist_completed');
  }

  function removeBanner() { document.getElementById('pb-consent-banner')?.remove(); }
  function saveChoice(value) { try { localStorage.setItem(STORAGE_KEY, value); } catch (_) {} }
  function showBanner() {
    if (document.getElementById('pb-consent-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'pb-consent-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Preferencias de analítica');
    banner.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;z-index:99999;max-width:720px;margin:auto;background:#fff;border:1px solid #ddd;border-radius:16px;box-shadow:0 12px 40px rgba(0,0,0,.18);padding:18px;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:#1f2937';
    banner.innerHTML = `<div style="font-weight:700;font-size:16px;margin-bottom:6px">¿Nos permites medir visitas?</div><div style="font-size:14px;line-height:1.5;margin-bottom:14px">Usamos Google Analytics 4 solo para saber cuántas personas visitan Papeles del Bebé y qué páginas resultan útiles. No cargamos Analytics hasta que aceptes. <a href="/cookies/" style="color:#4f46e5">Información sobre cookies</a>.</div><div style="display:flex;gap:10px;flex-wrap:wrap;justify-content:flex-end"><button id="pb-reject-analytics" type="button" style="border:1px solid #cbd5e1;background:#fff;color:#334155;border-radius:10px;padding:10px 14px;cursor:pointer;font-weight:600">Rechazar</button><button id="pb-accept-analytics" type="button" style="border:0;background:#4f46e5;color:#fff;border-radius:10px;padding:10px 14px;cursor:pointer;font-weight:700">Aceptar analítica</button></div>`;
    document.body.appendChild(banner);
    document.getElementById('pb-accept-analytics').addEventListener('click', () => { saveChoice('accepted'); removeBanner(); loadGa4(); });
    document.getElementById('pb-reject-analytics').addEventListener('click', () => { saveChoice('rejected'); removeBanner(); });
  }

  // Medición anónima por categoría: solo después de aceptar analítica.
  // Nunca enviamos URL de Amazon, identificadores personales ni datos familiares.
  document.addEventListener('click', function (event) {
    const link = event.target.closest('a[data-affiliate-category]');
    if (!link) return;
    let choice = null;
    try { choice = localStorage.getItem(STORAGE_KEY); } catch (_) {}
    if (choice !== 'accepted' || typeof window.gtag !== 'function') return;
    const category = String(link.dataset.affiliateCategory || '').slice(0, 70);
    if (!/^[a-z0-9-]{1,70}$/.test(category)) return;
    window.gtag('event', 'affiliate_click', {
      affiliate_network: 'amazon',
      affiliate_category: category,
      page_location: window.location.origin + window.location.pathname
    });
  });

  let consent = null;
  try { consent = localStorage.getItem(STORAGE_KEY); } catch (_) {}
  if (consent === 'accepted') loadGa4();
  else if (consent !== 'rejected') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showBanner, { once: true });
    else showBanner();
  }
})();