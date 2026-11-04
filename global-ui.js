(() => {
  if (window.__papelesBebeGlobalUiInitialized) return;
  window.__papelesBebeGlobalUiInitialized = true;
  const MASTER_KEY = 'papelesbebe_que_me_falta_v1';
  const APP_COMPLETED_KEY = 'tramitesFacilesCompletados';
  const HEADER_VERSION = '20261104-preparativos-marketing';
  const FOOTER_VERSION = '20261022-share5';
  const MASTER_KEYS = ['registro','seguridad-social','tarjeta-sanitaria','padron','prestacion','deduccion','ayudas'];
  const NAV_ITEMS = [
    ['/mi-panel/', 'Mis trámites'],
    ['/ayudas-nacimiento/', 'Ayudas'],
    ['/herramientas/', 'Herramientas'],
    ['/guias-familias/', 'Guías'],
    ['/preparativos-bebe/', '🧸 Preparativos']
  ];

  function readLocal(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return value == null ? fallback : value;
    } catch (_) { return fallback; }
  }
  function writeLocal(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) {}
  }
  function readMaster() {
    const state = readLocal(MASTER_KEY, {});
    return state && typeof state === 'object' ? state : {};
  }
  function writeMaster(state) {
    writeLocal(MASTER_KEY, state);
    window.dispatchEvent(new CustomEvent('papelesbebe:progress', { detail: state }));
  }
  function progressCount() {
    const master = readMaster();
    return MASTER_KEYS.filter((key) => master[key] === true).length;
  }

  function masterKeyForAppId(id) {
    if (id === 'registro-civil') return 'registro';
    if (id === 'seguridad-social-bebe') return 'seguridad-social';
    if (id === 'tsi-cataluna' || id === 'tarjeta-sanitaria-autonomica') return 'tarjeta-sanitaria';
    if (id === 'empadronamiento') return 'padron';
    if (id === 'prestacion-nacimiento' || id === 'situacion-desempleo') return 'prestacion';
    if (id === 'deduccion-maternidad') return 'deduccion';
    if (/^(ayuda|ayudas|pago-unico)/.test(id || '')) return 'ayudas';
    return '';
  }

  function migrateLegacyProgress() {
    let master = readMaster();
    const completed = readLocal(APP_COMPLETED_KEY, []);
    if (!Object.keys(master).length && Array.isArray(completed) && completed.length) {
      master = {};
      completed.forEach((id) => {
        const key = masterKeyForAppId(id);
        if (key) master[key] = true;
      });
      if (Object.keys(master).length) writeMaster(master);
    }
  }

  function activeSection(href) {
    const p = location.pathname;
    if (href === '/mi-panel/') return p.startsWith('/mi-panel/');
    if (href === '/herramientas/') return p.startsWith('/herramientas/');
    if (href === '/observatorio/') return p.startsWith('/observatorio/');
    if (href === '/preparativos-bebe/') return p.startsWith('/preparativos-bebe/');
    if (href === '/ayudas-nacimiento/') return p.startsWith('/ayuda') || p.startsWith('/familias-') || p.startsWith('/bono-') || p.startsWith('/tarxeta-') || p.startsWith('/deduccion-nacimiento-');
    if (href === '/tramites-bebe/') return /(registro|seguridad-social|tarjeta-sanitaria|empadron|certificado|dni-bebe|pasaporte-bebe)/.test(p);
    if (href === '/guias-familias/') return p.startsWith('/guias-') || p.startsWith('/permiso-') || p.startsWith('/deduccion-maternidad');
    return p.startsWith(href);
  }

  function asegurarEstilosGlobales() {
    if (document.getElementById('pb-global-ui-style')) return;
    const style = document.createElement('style');
    style.id = 'pb-global-ui-style';
    style.textContent = `

      /* Una única tarjeta visual para ruta, progreso y acciones de revisión. */
      html.pb-journey #pb-journey-chrome #pb-route-context{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:start!important;column-gap:18px!important;row-gap:12px!important;}
      html.pb-journey #pb-route-context > #pb-article-progress,
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{grid-column:1/-1!important;width:100%!important;max-width:none!important;margin:0!important;padding:15px 0 0!important;border:0!important;border-top:1px solid #dce3f2!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;box-sizing:border-box!important}
      html.pb-journey #pb-route-context > #pb-article-progress{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:14px!important}
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:14px!important}
      html.pb-journey #pb-route-context .pb-route-progress{grid-column:2!important;grid-row:1!important}
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome #pb-route-context{grid-template-columns:1fr!important}
        html.pb-journey #pb-route-context .pb-route-progress{grid-column:1!important;grid-row:2!important}
        html.pb-journey #pb-route-context > #pb-article-progress,
        html.pb-journey #pb-route-context > #pb-ayudas-final-control{grid-column:1!important;flex-direction:column!important;align-items:stretch!important;padding-top:12px!important}
      }

      html.pb-journey .pb-route-step-nav{display:flex;gap:14px;flex-wrap:wrap;margin-top:9px}
      html.pb-journey .pb-route-step-nav a{font-size:.84rem;line-height:1.35;font-weight:750;color:#5058c9;text-decoration:none}
      html.pb-journey .pb-route-step-nav a:hover{text-decoration:underline}
      html.pb-journey .pb-route-step-nav a:focus-visible{outline:2px solid #5058c9;outline-offset:3px;border-radius:3px}
      @media(max-width:700px){html.pb-journey .pb-route-step-nav{gap:12px;margin-top:8px}html.pb-journey .pb-route-step-nav a{min-height:35px;display:inline-flex;align-items:center}}

      /* Mantener las dos tarjetas en un flujo estable al cambiar de estado. */
      html.pb-journey #pb-journey-chrome{display:flex!important;flex-direction:column!important;gap:14px!important}
      html.pb-journey #pb-journey-chrome #pb-route-context,
      html.pb-journey #pb-journey-chrome #pb-article-progress{margin:0!important;flex-shrink:0}
      html.pb-journey main > .badge,html.pb-journey main > .hero + .badge{display:none!important}

      /* Shell único por encima de la guía: nunca dentro del recuadro del artículo. */
      html.pb-journey #pb-journey-chrome{width:min(100% - 40px,1100px);max-width:1100px;margin:26px auto 0;padding:0;box-sizing:border-box}
      html.pb-journey #pb-journey-chrome #pb-route-context,
      html.pb-journey #pb-journey-chrome #pb-article-progress{display:flex!important;align-items:center;justify-content:space-between;gap:18px;box-sizing:border-box;width:100%!important;max-width:none!important;margin:0 0 18px!important;padding:18px 22px!important;background:#f8f9ff!important;border:1px solid #dce3f2!important;border-radius:17px!important;box-shadow:none!important}
      html.pb-journey #pb-journey-chrome .pb-article-progress-actions{display:flex;flex-wrap:wrap;align-items:center;gap:9px}
      html.pb-journey #pb-journey-chrome .pb-article-progress-actions button,
      html.pb-journey #pb-journey-chrome .pb-article-progress-actions a{min-height:43px;box-sizing:border-box}
      html.pb-journey main{padding-top:0!important}
      html.pb-journey main>.badge{display:none!important}
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome{width:calc(100% - 24px);margin-top:14px}
        html.pb-journey #pb-journey-chrome #pb-route-context,
        html.pb-journey #pb-journey-chrome #pb-article-progress{padding:14px!important;margin-bottom:12px!important}
        html.pb-journey #pb-journey-chrome #pb-article-progress{flex-direction:column;align-items:stretch}
        html.pb-journey #pb-journey-chrome .pb-article-progress-actions{display:grid;grid-template-columns:1fr}
        html.pb-journey #pb-journey-chrome .pb-article-progress-actions>*{width:100%;text-align:center}
      }

      /* Consistent warm backdrop and white cards across all seven route templates. */
      html.pb-journey, html.pb-journey body { background:linear-gradient(115deg,#fff4f0 0%,#fcfafb 48%,#f4f2ff 100%) fixed!important; }
      html.pb-journey main { background:transparent!important; }
      html.pb-journey main > .hero,html.pb-journey main > .hero-guide,html.pb-journey main > .tools-hero { background:#fff!important;border:1px solid #dfe4f0!important; }
      html.pb-journey main > #pb-route-context,html.pb-journey main > #pb-article-progress { background:#f8f9ff!important;border:1px solid #dce3f2!important; }
      @media(max-width:700px){html.pb-journey,html.pb-journey body{background:#faf9fd!important}}

      .pb-journey main > .badge{display:none!important}
      .pb-journey main > .breadcrumbs-visibles,.pb-journey main > .crumbs,.pb-journey main > .tool-breadcrumb{order:3!important}
      .pb-journey main > #pb-article-progress{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:16px!important}
      .pb-journey main > #pb-article-progress .pb-article-progress-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
      .pb-journey main > #pb-article-progress button,.pb-journey main > #pb-article-progress a{min-height:42px;box-sizing:border-box}
      .pb-journey main > .hero,.pb-journey main > .hero-guide,.pb-journey main > .tools-hero{padding:30px!important;margin-top:0!important}
      @media(max-width:700px){.pb-journey main > #pb-article-progress{flex-direction:column!important;align-items:stretch!important}.pb-journey main > #pb-article-progress .pb-article-progress-actions{display:grid!important;grid-template-columns:1fr!important}.pb-journey main > #pb-article-progress .pb-article-progress-actions>*{width:100%;text-align:center}.pb-journey main > .hero,.pb-journey main > .hero-guide,.pb-journey main > .tools-hero{padding:20px!important}}

      header.pb-global-header{background:#fff!important;border-bottom:1px solid #e7e8ef!important;box-shadow:0 1px 0 rgba(24,31,54,.02)!important;position:relative!important;z-index:1000!important}
      header.pb-global-header .header-contenido{max-width:1280px!important;margin:0 auto!important;min-height:74px!important;padding:10px 24px!important;display:flex!important;align-items:center!important;justify-content:space-between!important;gap:24px!important;box-sizing:border-box!important}
      header.pb-global-header .logo-enlace{flex:0 0 auto!important;text-decoration:none!important}
      header.pb-global-header .nav-principal{display:flex!important;align-items:center!important;justify-content:flex-end!important;gap:6px!important;flex-wrap:wrap!important;margin:0!important;padding:0!important}
      header.pb-global-header .nav-principal a{display:inline-flex!important;align-items:center!important;gap:6px!important;min-height:42px!important;padding:9px 11px!important;border-radius:12px!important;border:1px solid transparent!important;background:transparent!important;color:#586176!important;text-decoration:none!important;font-weight:750!important;font-size:.94rem!important;line-height:1.2!important;white-space:nowrap!important;box-shadow:none!important}
      header.pb-global-header .nav-principal a:hover{background:#f6f7ff!important;color:#454bc0!important}
      header.pb-global-header .nav-principal a[aria-current="page"]{background:#f0efff!important;color:#555bd1!important;border-color:#dcddff!important}
      header.pb-global-header .nav-principal a.pb-nav-shop,header.pb-global-header .nav-principal a.pb-nav-shop[aria-current="page"]{background:linear-gradient(110deg,#fff0d5,#ffdb9e)!important;border:1px solid #e7b46a!important;color:#76410d!important;font-weight:900!important;box-shadow:0 3px 12px rgba(165,99,20,.17)!important;padding:9px 12px!important;gap:7px!important}
      header.pb-global-header .nav-principal a.pb-nav-shop:hover{background:#ffd38b!important;color:#653605!important;box-shadow:0 5px 15px rgba(165,99,20,.23)!important}
      header.pb-global-header .nav-principal a.pb-nav-shop:focus-visible{outline:3px solid #9d641f!important;outline-offset:3px!important}
      header.pb-global-header .nav-principal .pb-nav-shop-badge{display:inline-flex;align-items:center;border-radius:5px;background:#9d5218;color:#fff;font-size:.6rem;letter-spacing:.04em;font-weight:900;padding:3px 5px;line-height:1}
      .pb-progress-badge{display:inline-flex;align-items:center;justify-content:center;min-width:34px;padding:2px 7px;border-radius:999px;background:#eef9f2;color:#23724c;font-size:.75rem;font-weight:800;border:1px solid #d5ecdf}
      .pb-article-progress{max-width:1120px;margin:14px auto 20px;padding:14px 16px;border:1px solid #e4e6f2;border-radius:16px;background:#fbfbff;display:flex;align-items:center;justify-content:space-between;gap:14px;box-sizing:border-box}
      .pb-article-progress strong{display:block;color:#27334d;margin-bottom:3px}.pb-article-progress p{margin:0;color:#687087;font-size:.92rem}.pb-article-progress-actions{display:flex;gap:8px;flex-wrap:wrap}.pb-article-progress button,.pb-article-progress a{border:1px solid #d9dcf5;border-radius:10px;padding:8px 11px;background:#fff;color:#5057c8;font:inherit;font-weight:750;text-decoration:none;cursor:pointer;white-space:nowrap}.pb-article-progress.is-done{background:#f4fbf7;border-color:#d6ecdf}.pb-article-progress.is-done strong{color:#23724c}
      @media(min-width:701px){#pb-article-progress{max-width:940px!important;padding:12px 16px!important;gap:10px!important;box-shadow:none!important}#pb-article-progress p{font-size:.79rem!important;margin:3px 0 0!important}#pb-article-progress .pb-article-progress-actions{gap:7px!important}#pb-article-progress .pb-article-progress-actions a,#pb-article-progress .pb-article-progress-actions button{font-size:.82rem!important;padding:8px 10px!important;min-height:38px!important}#pb-article-progress .pb-next-step-link{background:#6067e8!important;color:#fff!important;-webkit-text-fill-color:#fff!important}}
      footer.pb-global-footer{margin-top:48px!important;background:#182035!important;color:#dfe4f0!important;border-top:0!important;padding:0!important}.pb-footer-inner{max-width:1180px;margin:0 auto;padding:34px 24px;display:grid;grid-template-columns:1.1fr 2fr auto;gap:28px;align-items:start;box-sizing:border-box}.pb-footer-brand{font-weight:850;font-size:1.15rem;color:#fff!important;text-decoration:none}.pb-footer-brand span{color:#8f94ff}.pb-global-footer p{color:#b8c0d2!important;margin:8px 0 0!important}.pb-global-footer nav{display:flex;gap:10px 18px;flex-wrap:wrap}.pb-global-footer nav a{color:#eef1f8!important;text-decoration:none;font-weight:650}.pb-global-footer nav a:hover{text-decoration:underline}.pb-footer-copy{white-space:nowrap;font-size:.88rem!important}
      .pb-global-footer .pb-share{max-width:1180px;margin:0 auto;padding:15px 24px 26px;border-top:1px solid rgba(255,255,255,.14);display:flex;gap:10px 16px;align-items:center;flex-wrap:wrap;box-sizing:border-box}
      .pb-global-footer .pb-share-label{font-weight:750;color:#f5f6fc;font-size:.91rem}
      .pb-global-footer .pb-share-links{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
      .pb-global-footer .pb-share-links a,.pb-global-footer .pb-share-links button{display:inline-flex;align-items:center;justify-content:center;min-height:40px;padding:8px 12px;border:1px solid rgba(229,233,248,.23);background:rgba(255,255,255,.06);color:#f3f5fc!important;-webkit-text-fill-color:#f3f5fc!important;border-radius:11px;text-decoration:none;font:inherit;font-weight:750;font-size:.83rem;cursor:pointer}
      .pb-global-footer .pb-share-links svg{display:block;width:19px;height:19px;flex:none}
      .pb-global-footer .pb-share-links a,.pb-global-footer .pb-share-links button{gap:8px}
      .pb-global-footer .pb-share-links [data-pb-share="whatsapp"] svg{color:#35d17d}
      .pb-global-footer .pb-share-links [data-pb-share="facebook"] svg{color:#8eb8ff}
      .pb-global-footer .pb-share-links a:hover,.pb-global-footer .pb-share-links button:hover{background:rgba(255,255,255,.15);text-decoration:none}
      .pb-global-footer .pb-share-links a:focus-visible,.pb-global-footer .pb-share-links button:focus-visible{outline:3px solid #a5a9ff;outline-offset:2px}
      .pb-global-footer .pb-share-status{font-size:.77rem;color:#cdd4e4;min-height:1em}
      @media(max-width:700px){.pb-global-footer .pb-share{padding:16px 16px 26px;gap:9px}.pb-global-footer .pb-share-label{flex-basis:100%}}
      @media print{.pb-global-footer .pb-share{display:none!important}}
      #pb-mobile-nav{display:none}
      @media(max-width:900px){header.pb-global-header .header-contenido{align-items:flex-start!important;flex-direction:column!important;gap:8px!important;padding:10px 16px!important}header.pb-global-header .nav-principal{width:100%!important;justify-content:flex-start!important;overflow-x:auto!important;flex-wrap:nowrap!important;padding-bottom:2px!important}header.pb-global-header .nav-principal a{font-size:.88rem!important;padding:8px 10px!important}.pb-footer-inner{grid-template-columns:1fr;gap:18px}}
      /* Mobile: one navigation at the bottom; top header is branding only. */
      @media(max-width:700px){
        header.pb-global-header .header-contenido{min-height:56px!important;height:auto!important;display:flex!important;flex-direction:row!important;align-items:center!important;justify-content:flex-start!important;gap:0!important;padding:8px 16px!important}
        header.pb-global-header .nav-principal,header.pb-global-header .header-acciones{display:none!important}
        header.pb-global-header .logo-enlace{margin:0!important}
        body{padding-bottom:calc(72px + env(safe-area-inset-bottom,0px))!important}
        #pb-mobile-nav{grid-template-columns:repeat(5,minmax(0,1fr))!important;padding-bottom:env(safe-area-inset-bottom,0px)!important}
        #pb-mobile-nav a{display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important;min-width:0!important;min-height:62px!important;padding:7px 1px 5px!important;font-size:clamp(.59rem,2.35vw,.73rem)!important;line-height:1.12!important;white-space:normal!important}
        #pb-mobile-nav a span{font-size:1.18rem!important;margin-bottom:5px!important}
      }
      @media(max-width:700px){#pb-article-progress{margin:8px 12px 12px!important;padding:10px 12px!important;gap:7px!important;border-radius:12px!important;box-shadow:none!important}#pb-article-progress strong{font-size:14px!important}#pb-article-progress p{display:none!important}#pb-article-progress .pb-article-progress-actions{width:100%;gap:7px!important}#pb-article-progress .pb-article-progress-actions button,#pb-article-progress .pb-article-progress-actions a{font-size:12px!important;min-height:38px!important;padding:8px 10px!important}#pb-article-progress .pb-article-progress-actions a[data-pb-open-panel]{display:none!important}#pb-article-progress .pb-next-step-link{background:#6067e8!important;color:#fff!important;-webkit-text-fill-color:#fff!important;border-color:#6067e8!important}body{padding-bottom:calc(72px + env(safe-area-inset-bottom,0px))!important}#pb-mobile-nav{display:grid;grid-template-columns:repeat(4,1fr);position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#fff;border-top:1px solid #e1e4ee;box-shadow:0 -5px 20px rgba(29,35,58,.08)}#pb-mobile-nav a{padding:10px 4px 9px;text-align:center;text-decoration:none;color:#687087;font-size:.73rem;font-weight:750}#pb-mobile-nav a span{display:block;font-size:1.05rem;margin-bottom:2px}#pb-mobile-nav a[aria-current="page"]{color:#565bd6;background:#f6f5ff}.pb-article-progress{margin:12px 14px 18px;align-items:flex-start;flex-direction:column}.pb-footer-copy{white-space:normal}}
    `;
    // Orden uniforme: ruta > estado > migas > guía; eliminar el badge decorativo heredado.
    const normalizeJourney = () => {
      const main = document.querySelector('main');
      if (!main) return;
      const route = main.querySelector('#pb-route-context');
      const status = main.querySelector('#pb-article-progress');
      if (route && main.firstElementChild !== route) main.prepend(route);
      if (route && status && route.nextElementSibling !== status) route.insertAdjacentElement('afterend',status);
    };
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded',normalizeJourney,{once:true});
    else normalizeJourney();
    // Ayudas: el padding heredado de tools-main estrechaba estado y guía 40 px por lado.
    style.textContent += `
      html.pb-journey body main.tools-main {width:min(calc(100% - 40px),1100px)!important;max-width:1100px!important;padding-left:0!important;padding-right:0!important;box-sizing:border-box!important;}
      html.pb-journey main.tools-main #pb-ayudas-final-control,
      html.pb-journey main.tools-main > .tools-hero {width:100%!important;max-width:none!important;box-sizing:border-box!important;}
      @media(max-width:700px){
        html.pb-journey body main.tools-main {width:calc(100% - 24px)!important;padding-left:0!important;padding-right:0!important;}
      }
    `;
    // Layout estable: una columna real, sin grid heredado ni desbordamientos.
    style.textContent += `
      html.pb-journey #pb-journey-chrome > #pb-route-context{
        display:flex!important;flex-direction:column!important;align-items:stretch!important;
        justify-content:flex-start!important;gap:12px!important;min-width:0!important;
        height:auto!important;overflow:visible!important;padding:20px 24px!important;
      }
      html.pb-journey #pb-route-context > .pb-route-copy{
        display:block!important;flex:none!important;width:100%!important;min-width:0!important;
        max-width:100%!important;white-space:normal!important;
      }
      html.pb-journey #pb-route-context > .pb-route-progress{
        display:flex!important;align-items:center!important;gap:10px!important;
        width:100%!important;min-width:0!important;max-width:100%!important;
        grid-row:auto!important;grid-column:auto!important;flex:none!important;
      }
      html.pb-journey #pb-route-context > .pb-route-progress .pb-route-track{flex:1!important;max-width:none!important}
      html.pb-journey #pb-route-context > #pb-article-progress,
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{
        display:flex!important;position:static!important;flex-direction:row!important;
        align-items:center!important;justify-content:space-between!important;flex-wrap:wrap!important;
        width:100%!important;min-width:0!important;max-width:100%!important;
        margin:0!important;padding:15px 0 0!important;border:0!important;
        border-top:1px solid #dce3f2!important;border-radius:0!important;
        box-shadow:none!important;background:transparent!important;gap:12px!important;
        grid-row:auto!important;grid-column:auto!important;
      }
      html.pb-journey #pb-route-context .pb-article-progress-actions,
      html.pb-journey #pb-route-context .pb-ayudas-final-actions{
        display:flex!important;flex-wrap:wrap!important;gap:8px!important;max-width:100%!important;min-width:0!important;
      }
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome > #pb-route-context{padding:16px!important;gap:10px!important}
        html.pb-journey #pb-route-context > #pb-article-progress,
        html.pb-journey #pb-route-context > #pb-ayudas-final-control{
          flex-direction:column!important;align-items:stretch!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          display:flex!important;flex-direction:column!important;align-items:stretch!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions > *,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions > *{width:100%!important;box-sizing:border-box!important}
      }
    `;
    // Disposición definitiva: título a la izquierda; estado y acciones alineados a la derecha.
    style.textContent += `
      html.pb-journey #pb-journey-chrome > #pb-route-context{
        display:grid!important;grid-template-columns:minmax(0,1fr) auto auto!important;
        align-items:center!important;gap:12px 18px!important;
      }
      html.pb-journey #pb-route-context > .pb-route-copy{
        grid-column:1!important;grid-row:1!important;width:auto!important;
      }
      html.pb-journey #pb-route-context > .pb-route-progress{
        grid-column:1/-1!important;grid-row:2!important;
      }
      html.pb-journey #pb-route-context > #pb-article-progress,
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{
        display:contents!important;
      }
      html.pb-journey #pb-route-context .pb-progress-status-label,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy{
        grid-column:2!important;grid-row:1!important;
        min-width:0!important;text-align:right!important;
      }
      html.pb-journey #pb-route-context .pb-progress-status-label strong,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy strong{
        white-space:nowrap!important;color:#27724a!important;font-size:.94rem!important;
      }
      html.pb-journey #pb-route-context #pb-article-progress:not(.is-done) .pb-progress-status-label strong{
        color:#6f7891!important;
      }
      html.pb-journey #pb-route-context .pb-progress-status-label p,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy p{display:none!important}
      html.pb-journey #pb-route-context .pb-article-progress-actions,
      html.pb-journey #pb-route-context .pb-ayudas-final-actions{
        grid-column:3!important;grid-row:1!important;
        display:flex!important;flex-direction:row!important;align-items:center!important;
        flex-wrap:wrap!important;justify-content:flex-end!important;gap:8px!important;
      }
      @media(max-width:1050px){
        html.pb-journey #pb-journey-chrome > #pb-route-context{
          grid-template-columns:minmax(0,1fr) auto!important;
        }
        html.pb-journey #pb-route-context .pb-progress-status-label,
        html.pb-journey #pb-route-context .pb-ayudas-final-copy{grid-column:2!important;grid-row:1!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          grid-column:1/-1!important;grid-row:3!important;justify-content:flex-start!important;
        }
      }
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome > #pb-route-context{
          grid-template-columns:minmax(0,1fr) auto!important;gap:12px!important;
        }
        html.pb-journey #pb-route-context .pb-route-progress{grid-column:1/-1!important;grid-row:2!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          grid-column:1/-1!important;grid-row:3!important;
          flex-direction:column!important;align-items:stretch!important;
        }
      }
    `;
    style.textContent += `
      html.pb-journey.pb-guide-only #pb-journey-chrome,
      html.pb-journey.pb-guide-only #pb-article-progress,
      html.pb-journey.pb-guide-only #pb-ayudas-final-control{display:none!important}
      html.pb-journey #pb-guide-start{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;padding:13px 18px;margin:0 0 20px;background:#f7f8ff;border:1px solid #e0e4f7;border-radius:13px;font-size:.9rem;color:#485573}
      html.pb-journey #pb-guide-start a{font-weight:750;color:#5058cc;text-decoration:none}
      html.pb-journey #pb-guide-start a:hover{text-decoration:underline}
      @media(max-width:700px){html.pb-journey #pb-guide-start{padding:12px 14px;align-items:flex-start}}
    `;
    /* UX recorrido: enlaces compactos y control de estado siempre visible. */
    style.textContent += `
      html.pb-journey #pb-journey-chrome > #pb-route-context{
        display:flex!important;flex-direction:column!important;align-items:stretch!important;
        justify-content:flex-start!important;gap:10px!important;height:auto!important;
      }
      html.pb-journey #pb-route-context > .pb-route-copy,
      html.pb-journey #pb-route-context > .pb-route-progress{width:100%!important;flex:none!important}
      html.pb-journey #pb-route-context .pb-route-step-nav{
        display:flex!important;flex-flow:row wrap!important;justify-content:flex-start!important;
        align-items:center!important;column-gap:18px!important;row-gap:4px!important;
        margin:8px 0 0!important;padding:0!important;min-height:0!important;
      }
      html.pb-journey #pb-route-context .pb-route-step-nav a{
        display:inline-flex!important;align-items:center!important;width:auto!important;
        min-height:32px!important;margin:0!important;padding:2px 0!important;
        font-size:.86rem!important;line-height:1.35!important;
      }
      html.pb-journey #pb-route-context > #pb-article-progress,
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{
        display:flex!important;flex-direction:row!important;align-items:center!important;
        justify-content:space-between!important;flex-wrap:wrap!important;
        position:static!important;visibility:visible!important;opacity:1!important;
        padding:13px 0 0!important;margin:0!important;width:100%!important;
        border:0!important;border-top:1px solid #dce3f2!important;
        background:transparent!important;gap:10px!important;
      }
      html.pb-journey #pb-route-context .pb-progress-status-label,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy{
        display:block!important;text-align:left!important;flex:0 0 auto!important;
      }
      html.pb-journey #pb-route-context .pb-article-progress-actions,
      html.pb-journey #pb-route-context .pb-ayudas-final-actions{
        display:flex!important;flex-flow:row wrap!important;justify-content:flex-start!important;
        align-items:center!important;gap:8px!important;
      }
      html.pb-journey #pb-route-context #pb-ayudas-final-done:not([hidden]){
        display:inline-flex!important;visibility:visible!important;
      }
      @media(max-width:700px){
        html.pb-journey #pb-route-context .pb-route-step-nav{column-gap:14px!important;row-gap:2px!important}
        html.pb-journey #pb-route-context > #pb-article-progress,
        html.pb-journey #pb-route-context > #pb-ayudas-final-control{
          flex-direction:column!important;align-items:stretch!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          display:flex!important;flex-direction:column!important;align-items:stretch!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions > *,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions > *{width:100%!important;box-sizing:border-box!important}
      }
    `;
    // Corregir navegación y controles del recorrido en móvil y escritorio.
    style.textContent += `
      html.pb-journey #pb-journey-chrome #pb-route-context{
        display:flex!important;flex-direction:column!important;align-items:stretch!important;
        gap:10px!important;padding:16px 20px!important;height:auto!important}
      html.pb-journey #pb-route-context > .pb-route-copy{display:block!important;width:100%!important;flex:none!important;text-align:left!important}
      html.pb-journey #pb-route-context .pb-route-step-nav{
        display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
        justify-content:flex-start!important;align-items:center!important;
        column-gap:16px!important;row-gap:2px!important;margin:6px 0 0!important}
      html.pb-journey #pb-route-context .pb-route-step-nav a{
        display:inline-flex!important;width:auto!important;min-height:0!important;
        padding:2px 0!important;margin:0!important;line-height:1.35!important}
      html.pb-journey #pb-route-context > .pb-route-progress{
        display:flex!important;width:100%!important;max-width:none!important;grid-column:auto!important;grid-row:auto!important}
      html.pb-journey #pb-route-context > #pb-article-progress,
      html.pb-journey #pb-route-context > #pb-ayudas-final-control{
        display:flex!important;position:static!important;visibility:visible!important;opacity:1!important;
        flex-direction:row!important;align-items:center!important;justify-content:space-between!important;
        gap:12px!important;flex-wrap:wrap!important;width:100%!important;max-width:none!important;
        margin:0!important;padding:12px 0 0!important;border:0!important;
        border-top:1px solid #dce3f2!important;border-radius:0!important;background:transparent!important;box-shadow:none!important}
      html.pb-journey #pb-route-context .pb-progress-status-label,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy{
        display:block!important;visibility:visible!important;text-align:left!important;min-width:0!important;
        grid-column:auto!important;grid-row:auto!important}
      html.pb-journey #pb-route-context .pb-article-progress-actions,
      html.pb-journey #pb-route-context .pb-ayudas-final-actions{
        display:flex!important;visibility:visible!important;flex-wrap:wrap!important;
        flex-direction:row!important;align-items:center!important;justify-content:flex-start!important;
        gap:8px!important;grid-column:auto!important;grid-row:auto!important}
      html.pb-journey #pb-route-context #pb-ayudas-final-done:not([hidden]){display:inline-flex!important;visibility:visible!important}
      html.pb-journey #pb-route-context #pb-ayudas-final-done[hidden]{display:none!important}
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome #pb-route-context{padding:14px 16px!important;gap:10px!important}
        html.pb-journey #pb-route-context .pb-route-step-nav{column-gap:13px!important;row-gap:2px!important}
        html.pb-journey #pb-route-context > #pb-article-progress,
        html.pb-journey #pb-route-context > #pb-ayudas-final-control{flex-direction:column!important;align-items:stretch!important;gap:8px!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          flex-direction:column!important;align-items:stretch!important;width:100%!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions > *,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions > *{width:100%!important;box-sizing:border-box!important;text-align:center!important}
      }

      /* Compact, consistent mobile navigation. Desktop unchanged. */
      @media (max-width:767px) {
        html.pb-journey #pb-route-context .pb-route-step-nav {
          display:grid!important;
          grid-template-columns:repeat(2,minmax(0,1fr))!important;
          gap:10px!important;
          width:100%!important;
          margin:10px 0 0!important;
          align-items:stretch!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a {
          display:flex!important;
          flex-direction:column!important;
          justify-content:center!important;
          align-items:flex-start!important;
          box-sizing:border-box!important;
          width:100%!important;
          min-width:0!important;
          min-height:56px!important;
          padding:9px 11px!important;
          margin:0!important;
          border:1px solid #dce0ee!important;
          border-radius:12px!important;
          background:#f2f3fa!important;
          color:#343c60!important;
          font-size:clamp(.76rem,3.15vw,.86rem)!important;
          font-weight:700!important;
          line-height:1.3!important;
          text-decoration:none!important;
          white-space:normal!important;
          overflow-wrap:anywhere!important;
          box-shadow:none!important;
          -webkit-tap-highlight-color:transparent;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a.pb-route-next {
          background:#555bb6!important;
          border-color:#555bb6!important;
          color:#fff!important;
          align-items:flex-end!important;
          text-align:right!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a:only-child {
          grid-column:1/-1!important;
          width:100%!important;
          min-height:52px!important;
          align-items:center!important;
          text-align:center!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a:focus-visible {
          outline:3px solid #818cf8!important;
          outline-offset:3px!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a:active {transform:scale(.98)}
      }
    `;
    document.head.appendChild(style);
  }

  function navHtml() {
    return NAV_ITEMS.map(([href,text]) => {
      const current = activeSection(href) ? ' aria-current="page"' : '';
      const classes = href === '/preparativos-bebe/' ? ' class="pb-nav-shop"' : '';
      const panelAttr = href === '/mi-panel/' ? ' data-pb-nav="panel"' : '';
      return `<a href="${href}"${classes}${current}${panelAttr}>${text}${href === '/preparativos-bebe/' ? '<span class="pb-nav-shop-badge" aria-hidden="true">TOP</span>' : ''}</a>`;
    }).join('');
  }

  function normalizarCabecera() {
    asegurarEstilosGlobales();
    let header = document.querySelector('body > header, header');
    if (!header) {
      header = document.createElement('header');
      document.body.insertBefore(header, document.body.firstChild);
    }
    const expectedPath = location.pathname;
    const alreadyCurrent = header.dataset.pbHeaderVersion === HEADER_VERSION && header.dataset.pbHeaderPath === expectedPath;
    if (!alreadyCurrent) {
      header.className = 'pb-global-header';
      header.dataset.pbHeaderVersion = HEADER_VERSION;
      header.dataset.pbHeaderPath = expectedPath;
      header.innerHTML = `<div class="header-contenido"><a href="/" class="logo logo-enlace" aria-label="Ir al inicio">Papeles del <span>Bebé</span></a><nav class="nav-principal" aria-label="Navegación principal">${navHtml()}</nav></div>`;
    }
    actualizarBadgePanel();
  }

  function actualizarBadgePanel() {
    const link = document.querySelector('[data-pb-nav="panel"]');
    if (!link) return;
    const count = progressCount();
    let badge = link.querySelector('.pb-progress-badge');
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'pb-progress-badge';
      link.appendChild(badge);
    }
    const text = count === MASTER_KEYS.length ? `${count}/7 ✓` : `${count}/7`;
    const aria = `${count} de 7 bloques completados`;
    if (badge.textContent !== text) badge.textContent = text;
    if (badge.getAttribute('aria-label') !== aria) badge.setAttribute('aria-label', aria);
  }

  function setupFooterSharing(footer) {
    const canonical = document.querySelector('link[rel="canonical"]');
    let url = location.origin + location.pathname;
    if (canonical?.href) {
      try {
        const candidate = new URL(canonical.href, location.origin);
        if (candidate.origin === location.origin) url = candidate.href;
      } catch (_) {}
    }
    const title = (document.title || 'Papeles del Bebé').trim();
    const message = 'Te comparto esta página de Papeles del Bebé: ' + title;
    // Textos editables antes de publicar en X, según la sección visitada.
    function shareMessageForX(path) {
      if (path === '/') return '👶 ¿Vas a tener un bebé? Entre el Registro Civil, la Seguridad Social y las ayudas es fácil perderse 😅 Aquí puedes organizar los trámites gratis, paso a paso.';
      if (path.startsWith('/herramientas/calculadora-permiso-nacimiento/')) return '📅 ¿Cuándo terminará tu permiso por nacimiento? Calcula las fechas y revisa cómo organizarlo. Una herramienta gratuita para futuras familias 👶';
      if (path.startsWith('/herramientas/buscador-ayudas/')) return '💶 ¿Has comprobado qué ayudas por nacimiento podrías solicitar? Este buscador gratuito te orienta según tu comunidad y situación familiar 👶';
      if (path.startsWith('/checklist-imprimible/')) return '✅ Registro Civil, Seguridad Social, tarjeta sanitaria… ¡cuántos papeles cuando nace un bebé! Esta checklist gratuita e imprimible ayuda a organizarse 👶';
      if (path.startsWith('/mi-panel/')) return '👶 ¿Qué trámite toca después de tener un bebé? Organiza los pendientes y marca lo que ya has revisado, gratis y sin registrarte ✅';
      if (path.startsWith('/herramientas/')) return '👶 ¿Preparando el nacimiento? Estas herramientas gratuitas te ayudan con los permisos, las ayudas y los primeros trámites.';
      if (path.startsWith('/ayudas-nacimiento/') || path.startsWith('/comunidades/')) return '💶 ¿Qué ayudas existen cuando nace un bebé? Aquí tienes información por comunidad y enlaces para revisar los requisitos 👶';
      if (path.startsWith('/preparativos-bebe/')) return '🧸 ¿Preparando la llegada de un bebé? Esta lista te ayuda a distinguir lo esencial de lo que puede esperar, sin complicarte.';
      if (/permiso|prestacion-nacimiento|solicitar-permiso/.test(path)) return '📅 ¿Dudas con el permiso por nacimiento? Esta guía gratuita explica los pasos y enlaza con los trámites oficiales 👶';
      if (/registro-civil|empadron|tarjeta-sanitaria|seguridad-social/.test(path)) return '✅ Uno de los trámites después del nacimiento que conviene tener claro. Aquí tienes una guía sencilla con los pasos que debes revisar 👶';
      return '👶 Entre trámites, ayudas y fechas importantes, tener un bebé trae mucho papeleo. Esta guía gratuita puede ponértelo más fácil: ' + title.replace(/\s*\|\s*Papeles del Bebé.*$/i,'').slice(0,75);
    }
    const messageX = shareMessageForX(location.pathname);
    const destinations = {
      whatsapp:'https://api.whatsapp.com/send?text='+encodeURIComponent(message+' '+url),
      facebook:'https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(url),
      x:'https://twitter.com/intent/tweet?text='+encodeURIComponent(messageX)+'&url='+encodeURIComponent(url)
    };
    footer.querySelectorAll('[data-pb-share]').forEach(control => {
      const platform=control.dataset.pbShare;
      if(platform!=='copy') { control.href=destinations[platform];return; }
      control.addEventListener('click',async()=>{
        const status=footer.querySelector('.pb-share-status');
        try { await navigator.clipboard.writeText(url);if(status)status.textContent='Enlace copiado'; }
        catch (_) { if(status)status.textContent='No se pudo copiar. Utiliza la dirección del navegador.'; }
      });
    });
  }

  function normalizarFooter() {
    let footer = document.querySelector('footer');
    if (!footer) { footer = document.createElement('footer'); document.body.appendChild(footer); }
    if (footer.dataset.pbFooterVersion === FOOTER_VERSION) return;
    footer.className = 'pb-global-footer';
    footer.dataset.pbFooterVersion = FOOTER_VERSION;
    footer.innerHTML = `<div class="pb-footer-inner"><div><a class="pb-footer-brand" href="/">Papeles del <span>Bebé</span></a><p>Menos papeleo. Más tiempo para tu bebé.</p></div><nav aria-label="Navegación del pie"><a href="/mi-panel/">Mis trámites</a><a href="/ayudas-nacimiento/">Ayudas</a><a href="/herramientas/">Herramientas</a><a href="/guias-familias/">Guías</a><a href="/preparativos-bebe/">🧸 Preparativos</a><a href="/observatorio/">📊 Observatorio de ayudas</a><a href="/metodologia/">Cómo revisamos</a><a href="/quienes-somos/">Quiénes somos</a><a href="/aviso-legal/">Aviso legal</a><a href="/cookies/">Cookies</a><a href="/contacto/">Contacto</a><a href="/privacidad/">Privacidad</a></nav><p class="pb-footer-copy">© 2026 Papeles del Bebé</p></div><div class="pb-share" aria-label="Compartir esta página"><span class="pb-share-label">¿Te ha sido útil? Compártela</span><div class="pb-share-links"><a data-pb-share="whatsapp" href="#" target="_blank" rel="noopener noreferrer" aria-label="Compartir esta página por WhatsApp"><svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M20.5 3.5A11.8 11.8 0 0 0 12.1 0C5.55 0 .25 5.3.25 11.85c0 2.1.55 4.1 1.6 5.95L.15 24l6.35-1.66c1.7.93 3.62 1.42 5.58 1.42 6.53 0 11.85-5.3 11.85-11.84 0-3.15-1.22-6.13-3.43-8.42ZM12.08 21.75a9.9 9.9 0 0 1-5.05-1.38l-.36-.22-3.77.99 1-3.67-.25-.38a9.73 9.73 0 0 1-1.49-5.25c0-5.48 4.46-9.94 9.94-9.94s9.94 4.46 9.94 9.94-4.46 9.91-9.96 9.91Zm5.46-7.45c-.3-.15-1.77-.87-2.04-.97-.27-.1-.47-.15-.67.15-.2.3-.77.97-.94 1.17-.17.2-.35.22-.65.07-.3-.15-1.26-.47-2.4-1.48-.89-.79-1.49-1.77-1.67-2.07-.17-.3-.02-.46.13-.61.14-.13.3-.35.45-.52.15-.18.2-.3.3-.5.1-.2.05-.37-.03-.52-.07-.15-.67-1.62-.91-2.22-.24-.58-.48-.5-.67-.51h-.57c-.2 0-.52.08-.79.37s-1.04 1.02-1.04 2.49c0 1.47 1.07 2.89 1.22 3.09.15.2 2.1 3.21 5.08 4.5.71.31 1.26.49 1.69.63.71.23 1.36.2 1.87.12.57-.08 1.77-.72 2.02-1.42.25-.7.25-1.3.17-1.42-.07-.12-.27-.2-.57-.35Z"/></svg><span>WhatsApp</span></a><a data-pb-share="facebook" href="#" target="_blank" rel="noopener noreferrer" aria-label="Compartir esta página en Facebook"><svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M22 12.06C22 6.5 17.52 2 12 2S2 6.5 2 12.06c0 5.02 3.66 9.18 8.44 9.94v-7.04H7.9v-2.9h2.54V9.84c0-2.52 1.5-3.91 3.79-3.91 1.1 0 2.26.2 2.26.2v2.5h-1.27c-1.25 0-1.64.78-1.64 1.58v1.85h2.8l-.45 2.9h-2.35V22c4.78-.76 8.42-4.92 8.42-9.94Z"/></svg><span>Facebook</span></a><a data-pb-share="x" href="#" target="_blank" rel="noopener noreferrer" aria-label="Compartir esta página en X"><svg aria-hidden="true" viewBox="0 0 24 24" fill="currentColor"><path d="M18.9 2H22l-6.78 7.75L23.2 22h-6.25l-4.9-7.41L5.56 22H2.43l7.25-8.29L1.8 2h6.41l4.43 6.76L18.9 2Zm-1.1 18h1.73L7.27 3.89H5.41L17.8 20Z"/></svg><span>X</span></a><button type="button" data-pb-share="copy" aria-label="Copiar enlace de esta página"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg><span>Copiar enlace</span></button></div><span class="pb-share-status" role="status" aria-live="polite"></span></div>`;
    setupFooterSharing(footer);
  }

  function renderMobileNav() {
    if (document.getElementById('pb-mobile-nav')) return;
    const nav = document.createElement('nav');
    nav.id = 'pb-mobile-nav';
    nav.setAttribute('aria-label','Navegación móvil');
    const items = [['/mi-panel/','✓','Trámites'],['/ayudas-nacimiento/','€','Ayudas'],['/herramientas/','◈','Herramientas'],['/guias-familias/','▤','Guías'],['/preparativos-bebe/','🧸','Preparativos']];
    nav.innerHTML = items.map(([href,icon,label]) => `<a href="${href}"${activeSection(href) ? ' aria-current="page"' : ''}><span aria-hidden="true">${icon}</span>${label}</a>`).join('');
    document.body.appendChild(nav);
  }

  function keyForPath(pathname) {
    if (/registro-civil|comprobar-nacimiento-inscrito/.test(pathname)) return 'registro';
    if (/alta-bebe-seguridad-social|incluir-bebe-beneficiario-seguridad-social/.test(pathname)) return 'seguridad-social';
    if (/tarjeta-sanitaria-bebe/.test(pathname)) return 'tarjeta-sanitaria';
    if (/empadron/.test(pathname)) return 'padron';
    if (/prestacion-nacimiento|permiso-nacimiento-cuidado-menor|solicitar-permiso-nacimiento-online|como-saber-prestacion|cuando-paga-seguridad-social/.test(pathname)) return 'prestacion';
    if (/deduccion-maternidad/.test(pathname)) return 'deduccion';
    if (/^\/(ayuda|ayudas|bono-|tarxeta-|familias-|deduccion-nacimiento-)/.test(pathname)) return 'ayudas';
    return '';
  }

  function etiquetaKey(key) {
    return { registro:'Registro Civil', 'seguridad-social':'Seguridad Social', 'tarjeta-sanitaria':'Tarjeta sanitaria', padron:'Empadronamiento', prestacion:'Prestación por nacimiento', deduccion:'Deducción por maternidad', ayudas:'Ayudas' }[key] || 'Este paso';
  }

  function renderArticleProgress() {
    const key = keyForPath(location.pathname);
    const main = document.querySelector('main');
    if (!key || !main || !new URLSearchParams(location.search).has('ruta') || location.pathname.startsWith('/herramientas/') || location.pathname.startsWith('/mi-panel/') || location.pathname === '/ayudas-nacimiento/') return;
    let box = document.getElementById('pb-article-progress');
    if (!box) {
      box = document.createElement('section');
      box.id = 'pb-article-progress';
      const breadcrumbs = main.querySelector('.breadcrumbs-visibles, .breadcrumbs');
      const route = main.querySelector('#pb-route-context');
      if (route) route.insertAdjacentElement('afterend', box);
      else if (breadcrumbs) breadcrumbs.insertAdjacentElement('afterend', box);
      else main.insertBefore(box, main.firstChild);
    }
    const route = document.getElementById('pb-route-context');
    const shell = document.getElementById('pb-journey-chrome');
    if (shell && box.parentNode !== route && box.parentNode !== shell) shell.appendChild(box);
    else if (!shell && route && box.previousElementSibling !== route) route.insertAdjacentElement('afterend', box);
    const done = readMaster()[key] === true;
    const reviewOnly = key === 'ayudas' || key === 'deduccion';
    const steps = [
      ['registro','Registro Civil','/registro-civil-bebe/'],
      ['seguridad-social','Seguridad Social','/incluir-bebe-beneficiario-seguridad-social/'],
      ['tarjeta-sanitaria','Tarjeta sanitaria','/tarjeta-sanitaria-bebe/'],
      ['padron','Empadronamiento','/empadronar-bebe/'],
      ['prestacion','Permiso y prestación','/permiso-nacimiento-cuidado-menor-2026/'],
      ['deduccion','Deducciones','/deduccion-maternidad/?ruta=1'],
      ['ayudas','Ayudas','/ayudas-nacimiento/?ruta=1']
    ];
    const nextStep = steps.find(([stepKey]) => readMaster()[stepKey] !== true);
    const mobile = window.matchMedia('(max-width:700px)').matches;
    const signature = `${key}:${done ? '1' : '0'}:${reviewOnly ? '1' : '0'}:${nextStep ? nextStep[0] : 'all'}`;
    if (box.dataset.pbRenderSignature === signature) return;
    box.dataset.pbRenderSignature = signature;
    box.className = `pb-article-progress${done ? ' is-done' : ''}`;
    const forward = nextStep && (nextStep[0] !== key || done)
      ? `<a class="pb-next-step-link" href="${nextStep[2]}">Paso siguiente: ${nextStep[1]} →</a>`
      : (!nextStep ? '<a class="pb-next-step-link" href="/mi-panel/">Finalizado ✓ Ver mi resumen</a>' : '');
    box.innerHTML = `<div class="pb-article-progress-actions"><button type="button" data-pb-toggle-progress="${key}">${done ? 'Marcar como pendiente' : 'Marcar como hecho'}</button>${!nextStep ? '<a class="pb-next-step-link" href="/mi-panel/">Ver resumen final →</a>' : ''}<a href="/mi-panel/" data-pb-open-panel>Abrir Mi panel →</a></div>`;
    box.querySelector('button').addEventListener('click', () => {
      const next = readMaster();
      next[key] = !done;
      writeMaster(next);
      // Mantener a la vista la acción siguiente tras marcar el trámite.
      requestAnimationFrame(() => {
        const updated = document.getElementById('pb-article-progress');
        const follow = updated && updated.querySelector('.pb-next-step-link');
        if (follow && next[key]) {
          updated.scrollIntoView({block:'start',behavior:'smooth'});
          follow.focus({preventScroll:true});
        }
      });
    });
  }

  function syncAppChecklist() {
    const boxes = Array.from(document.querySelectorAll('.checkTramite[data-id]'));
    if (!boxes.length) return;
    const master = readMaster();
    let completed = readLocal(APP_COMPLETED_KEY, []);
    if (!Array.isArray(completed)) completed = [];
    const completedSet = new Set(completed);
    boxes.forEach((box) => {
      const id = box.dataset.id;
      const key = masterKeyForAppId(id);
      if (!key) return;
      if (typeof master[key] === 'boolean') {
        box.checked = master[key];
        if (master[key]) completedSet.add(id); else completedSet.delete(id);
      }
      if (!box.dataset.pbMasterBound) {
        box.dataset.pbMasterBound = '1';
        box.addEventListener('change', () => { const next = readMaster(); next[key] = box.checked; writeMaster(next); });
      }
      if (typeof window.actualizarAspectoTramite === 'function') { try { window.actualizarAspectoTramite(box); } catch (_) {} }
    });
    writeLocal(APP_COMPLETED_KEY, Array.from(completedSet));
    if (typeof window.actualizarContador === 'function') { try { window.actualizarContador(); } catch (_) {} }
  }

  function syncPrintableChecklist() {
    if (!location.pathname.startsWith('/checklist-imprimible/')) return;
    const boxes = Array.from(document.querySelectorAll('section[aria-label="Lista de trámites"] input[type="checkbox"]'));
    const keys = ['registro','registro','seguridad-social','tarjeta-sanitaria','padron','prestacion','ayudas','deduccion'];
    const master = readMaster();
    boxes.forEach((box,index) => {
      const key = keys[index]; if (!key) return;
      if (typeof master[key] === 'boolean') box.checked = master[key];
      if (!box.dataset.pbMasterBound) { box.dataset.pbMasterBound='1'; box.addEventListener('change',()=>{ const next=readMaster(); next[key]=box.checked; writeMaster(next); }); }
    });
  }

  function syncSimpleProgress() {
    document.querySelectorAll('input[type="checkbox"][data-key]').forEach((box) => {
      const key = box.dataset.key; if (!MASTER_KEYS.includes(key)) return;
      const master = readMaster();
      if (typeof master[key] === 'boolean' && box.checked !== master[key]) box.checked = master[key];
      if (!box.dataset.pbMasterBound) { box.dataset.pbMasterBound='1'; box.addEventListener('change',()=>{ const next=readMaster(); next[key]=box.checked; writeMaster(next); }); }
    });
  }


  function ensureJourneyShell() {
    const steps = [
      ['/registro-civil-bebe/?ruta=1','Registro Civil','🧾'],
      ['/incluir-bebe-beneficiario-seguridad-social/?ruta=1','Seguridad Social','👶'],
      ['/tarjeta-sanitaria-bebe/?ruta=1','Tarjeta sanitaria','🏥'],
      ['/empadronar-bebe/?ruta=1','Empadronamiento','🏠'],
      ['/permiso-nacimiento-cuidado-menor-2026/?ruta=1','Prestación y permiso','🗓️'],
      ['/deduccion-maternidad/?ruta=1','Deducciones','💳'],
      ['/ayudas-nacimiento/?ruta=1','Ayudas','💶']
    ];
    const active = location.pathname === '/permiso-nacimiento-cuidado-menor/' ? '/permiso-nacimiento-cuidado-menor-2026/' : location.pathname;
    const i = steps.findIndex(step => step[0].split('?')[0] === active);
    if (i === -1 || !new URLSearchParams(location.search).has('ruta')) return;
    const main = document.querySelector('main');
    if (!main || !main.parentNode) return;
    let shell = document.getElementById('pb-journey-chrome');
    if (!shell) { shell = document.createElement('div'); shell.id = 'pb-journey-chrome'; main.parentNode.insertBefore(shell, main); }
    let route = document.getElementById('pb-route-context');
    if (!route) { route = document.createElement('div'); route.id = 'pb-route-context'; route.className = 'pb-route-context'; }
    const number = i + 1;
    const completed = progressCount();
    const percent = Math.round(completed * 100 / 7);
    const current = steps[i];
    const done = readMaster()[MASTER_KEYS[i]] === true;
    const signature = `${number}:${completed}:${done ? 'hecho' : 'pendiente'}`;
    if (route.dataset.step !== signature) {
      route.dataset.step = signature;
      const prev = i > 0 ? `<a class="pb-route-prev" href="${steps[i-1][0]}">← Anterior: ${steps[i-1][1]}</a>` : '';
      const next = i < 6 ? `<a class="pb-route-next" href="${steps[i+1][0]}">Siguiente: ${steps[i+1][1]} →</a>` : '';
      // Conservar los controles interactivos antes de reconstruir la ruta.
      // Si no, innerHTML los destruye al cambiar de pendiente a hecho.
      const existingControl = route.querySelector(':scope > #pb-ayudas-final-control, :scope > #pb-article-progress');
      if (existingControl) existingControl.remove();
      route.innerHTML = `<div class="pb-route-copy"><span>TU RUTA · ${number}/7</span><strong>${current[2]} ${current[1]}</strong><nav class="pb-route-step-nav" aria-label="Navegar entre los siete pasos">${prev}${next}</nav></div><span class="pb-route-state ${done ? 'is-done' : ''}" role="status">${done ? '✓ Hecho' : 'Pendiente'}</span><div class="pb-route-progress" aria-label="${completed} de 7 trámites revisados"><b>${percent}%</b><span class="pb-route-track"><i style="width:${percent}%"></i></span></div>`;
      if (existingControl) route.appendChild(existingControl);
    }
    if (route.parentNode !== shell || shell.firstElementChild !== route) shell.prepend(route);
    const status = document.getElementById('pb-article-progress') || document.getElementById('pb-ayudas-final-control');
    if (status && status.parentNode !== route) route.appendChild(status);
    // Estado único en la banda superior; botón final únicamente en los controles inferiores.
    const duplicatedLabel = route.querySelector('.pb-progress-status-label, .pb-ayudas-final-copy');
    if (duplicatedLabel) duplicatedLabel.style.setProperty('display','none','important');
    const finalAction = route.querySelector('#pb-ayudas-final-done');
    if (finalAction) finalAction.style.removeProperty('display');
    // La navegación y el estado forman una sola tarjeta, también en Ayudas.
  }

  // La visita al panel no implica que se haya revisado ningún trámite.
  // El estado del recorrido procede exclusivamente de las siete marcas reales.
  function hasStartedJourney(){
    return progressCount()>0;
  }
  function showGuideEntry(){
    if(!document.documentElement.classList.contains('pb-journey'))return;
    const active=hasStartedJourney();
    document.documentElement.classList.toggle('pb-guide-only',!active);
    if(active || document.getElementById('pb-journey-chrome')){document.documentElement.classList.remove('pb-guide-only');document.getElementById('pb-guide-start')?.remove();return;}
    const main=document.querySelector('main');
    if(!main || document.getElementById('pb-guide-start'))return;
    const box=document.createElement('div');
    box.id='pb-guide-start';
    box.innerHTML='<span>¿Quieres organizar todos los trámites?</span><a href="/mi-panel/">Organizar mis 7 trámites →</a>';
    main.prepend(box);
  }
  function aplicar() {
    normalizarCabecera();
    normalizarFooter();
    renderMobileNav();
    syncAppChecklist();
    syncPrintableChecklist();
    syncSimpleProgress();
    if(new URLSearchParams(location.search).has('ruta')){renderArticleProgress();ensureJourneyShell();}
    showGuideEntry();
    actualizarBadgePanel();
  }

  // Plantilla visual única para el recorrido principal, independiente del tipo de página.
  const journeyPaths = new Set([
    '/registro-civil-bebe/',
    '/incluir-bebe-beneficiario-seguridad-social/',
    '/tarjeta-sanitaria-bebe/',
    '/empadronar-bebe/',
    '/permiso-nacimiento-cuidado-menor-2026/',
    '/permiso-nacimiento-cuidado-menor/',
    '/deduccion-maternidad/',
    '/ayudas-nacimiento/'
  ]);
  if (journeyPaths.has(location.pathname) && new URLSearchParams(location.search).has('ruta')) {
    document.documentElement.classList.add('pb-journey');
    const style = document.createElement('style');
    style.id = 'pb-journey-design';
    style.textContent = `
      .pb-journey body { background:#fafbff; }
      .pb-journey main { width:min(100% - 40px,1100px)!important; max-width:1100px!important; margin:0 auto!important; padding:26px 0 70px!important; box-sizing:border-box; }
      /* Evitar que las secciones queden pegadas al borde del main. */
      .pb-journey main { padding-left:clamp(16px,3vw,32px)!important;padding-right:clamp(16px,3vw,32px)!important; }
      .pb-journey main > .badge, .pb-journey main > .breadcrumbs-visibles, .pb-journey main > .crumbs,
      .pb-journey main > .tool-breadcrumb { position:relative; }
      .pb-journey main > #pb-route-context, .pb-journey main > #pb-article-progress,
      .pb-journey main > #pb-aid-step-final { border:1px solid #dbe2f1!important;background:#f8faff!important; }
      .pb-journey main > .hero, .pb-journey main > .hero-guide,
      .pb-journey main > .tools-hero { border:1px solid #dce3f2!important;box-shadow:0 8px 28px rgba(32,46,90,.035)!important; }
      .pb-journey main > .badge { margin-bottom:20px!important; }
      .pb-journey main > .hero, .pb-journey main > .hero-guide, .pb-journey main > .tools-hero { margin-top:12px!important; }
      .pb-journey main > #pb-route-context, .pb-journey main > #pb-article-progress,
      .pb-journey main > #pb-aid-step-final { width:100%!important;max-width:none!important;box-sizing:border-box!important;border-radius:16px!important;box-shadow:none!important; }
      .pb-journey main > #pb-route-context { margin:0 0 14px!important;padding:17px 20px!important; }
      .pb-journey main > #pb-article-progress, .pb-journey main > #pb-aid-step-final { margin:0 0 24px!important;padding:16px 20px!important; }
      .pb-journey main > .breadcrumbs-visibles, .pb-journey main > .crumbs,
      .pb-journey main > .tool-breadcrumb { margin:0 0 19px!important;padding:0!important;font-size:.86rem!important; }
      .pb-journey main > .hero, .pb-journey main > .hero-guide,
      .pb-journey main > .tools-hero { width:100%!important;max-width:none!important;box-sizing:border-box!important;margin:0 0 26px!important;padding:34px clamp(20px,4vw,42px)!important;border-radius:22px!important;background:#fff!important;border:1px solid #e5e9f4!important;text-align:left!important;box-shadow:none!important; }
      .pb-journey main > .hero h1, .pb-journey main > .hero-guide h1,
      .pb-journey main > .tools-hero h1 { font-size:clamp(2rem,4.2vw,3.2rem)!important;line-height:1.12!important;letter-spacing:-.035em!important;max-width:900px!important;margin:18px 0 18px!important;text-align:left!important; }
      .pb-journey main > .hero .subtitle, .pb-journey main > .hero-guide .lead,
      .pb-journey main > .tools-hero > p { font-size:clamp(1rem,1.7vw,1.12rem)!important;line-height:1.65!important;max-width:850px!important;margin:0 0 20px!important;text-align:left!important; }
      .pb-journey main > .hero .badge,.pb-journey main > .hero-guide .eyebrow,
      .pb-journey main > .tools-hero .tool-kicker { margin:0!important;display:inline-flex!important;font-size:.79rem!important; }
      .pb-journey main .contenido-informativo { text-align:left!important; }
      .pb-journey main .pb-hub-panel { margin:24px 0!important; }
      .pb-journey main .pb-observatorio-feature { margin:24px 0!important; }
      .pb-journey main #pb-aid-step-final button {min-height:44px!important}
      @media(max-width:700px){
        .pb-journey main {width:calc(100% - 16px)!important;padding:14px 12px 86px!important}
        .pb-journey main > #pb-route-context {margin-bottom:10px!important;padding:13px 14px!important}
        .pb-journey main > #pb-article-progress,.pb-journey main > #pb-aid-step-final {margin-bottom:17px!important;padding:14px!important}
        .pb-journey main > .hero,.pb-journey main > .hero-guide,.pb-journey main > .tools-hero {padding:22px 17px!important;border-radius:16px!important;margin-bottom:18px!important}
        .pb-journey main > .hero h1,.pb-journey main > .hero-guide h1,.pb-journey main > .tools-hero h1 {font-size:clamp(1.75rem,7vw,2.25rem)!important;margin:14px 0!important}
        .pb-journey main > .hero .subtitle,.pb-journey main > .hero-guide .lead,.pb-journey main > .tools-hero > p {font-size:.96rem!important;line-height:1.55!important}
      }
    `;
    style.textContent += `
      html.pb-journey #pb-journey-chrome > #pb-route-context{display:grid!important;grid-template-columns:minmax(0,1fr) auto auto!important;gap:12px!important;align-items:center!important;padding:16px 20px!important}
      html.pb-journey #pb-route-context > .pb-route-copy{grid-column:1!important;grid-row:1!important;min-width:0!important;width:auto!important}
      html.pb-journey #pb-route-context > .pb-route-state{grid-column:2!important;grid-row:1!important;display:inline-flex!important;align-items:center!important;white-space:nowrap!important;padding:6px 11px!important;border-radius:99px!important;background:#eef0f7!important;color:#5c667b!important;font-weight:800!important;font-size:.82rem!important}
      html.pb-journey #pb-route-context > .pb-route-state.is-done{background:#e8f7ee!important;color:#23734b!important}
      html.pb-journey #pb-route-context > .pb-route-progress{grid-column:1/-1!important;grid-row:2!important;width:100%!important;display:flex!important}
      html.pb-journey #pb-route-context > #pb-article-progress,html.pb-journey #pb-route-context > #pb-ayudas-final-control{display:contents!important}
      html.pb-journey #pb-route-context .pb-progress-status-label,html.pb-journey #pb-route-context .pb-ayudas-final-copy{display:none!important}
      html.pb-journey #pb-route-context .pb-article-progress-actions,html.pb-journey #pb-route-context .pb-ayudas-final-actions{grid-column:3!important;grid-row:1!important;display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;gap:8px!important;justify-content:flex-end!important;align-items:center!important;width:auto!important}
      html.pb-journey #pb-route-context .pb-route-step-nav{display:flex!important;flex-flow:row wrap!important;gap:4px 14px!important;justify-content:flex-start!important;margin:5px 0 0!important}
      html.pb-journey #pb-route-context .pb-route-step-nav a{display:inline-flex!important;width:auto!important;min-height:32px!important;padding:3px 0!important;margin:0!important}
      html.pb-journey #pb-route-context .pb-route-next{margin-left:auto!important}
      html.pb-journey #pb-route-context #pb-ayudas-final-done[hidden]{display:none!important}
      @media(max-width:1100px){html.pb-journey #pb-journey-chrome > #pb-route-context{grid-template-columns:minmax(0,1fr) auto!important}html.pb-journey #pb-route-context .pb-article-progress-actions,html.pb-journey #pb-route-context .pb-ayudas-final-actions{grid-column:1/-1!important;grid-row:3!important;justify-content:flex-start!important}}
      @media(max-width:700px){
        html.pb-journey #pb-journey-chrome > #pb-route-context{padding:14px 16px!important;gap:10px!important}
        html.pb-journey #pb-route-context .pb-route-step-nav{display:flex!important;flex-flow:row nowrap!important;justify-content:space-between!important;gap:12px!important}
        html.pb-journey #pb-route-context .pb-route-step-nav a{width:auto!important;max-width:50%!important;min-width:0!important;white-space:normal!important;overflow-wrap:break-word!important;font-size:.8rem!important;line-height:1.3!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions,html.pb-journey #pb-route-context .pb-ayudas-final-actions{grid-column:1/-1!important;grid-row:3!important;display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;width:100%!important;gap:8px!important}
        html.pb-journey #pb-route-context .pb-article-progress-actions > *,html.pb-journey #pb-route-context .pb-ayudas-final-actions > *{width:auto!important;flex:1 1 140px!important;min-height:44px!important;white-space:normal!important}
      }
    `;

    /* v1.1.0: navegación móvil compacta y controles de finalización. */
    style.textContent += `
      @media(max-width:700px){
        html.pb-journey #pb-route-context .pb-route-step-nav{
          display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;
          gap:8px!important;width:100%!important;margin-top:10px!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a{
          display:flex!important;flex-direction:column!important;justify-content:center!important;
          width:100%!important;max-width:none!important;min-width:0!important;
          box-sizing:border-box!important;padding:9px 7px!important;
          min-height:54px!important;border:1px solid #dce3f2!important;
          border-radius:10px!important;background:#f7f8ff!important;
          font-size:.78rem!important;line-height:1.25!important;text-align:center!important;
          overflow-wrap:anywhere!important;white-space:normal!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a:only-child{
          grid-column:1/-1!important;
          width:100%!important;
          max-width:none!important;
          min-height:48px!important;
          padding:9px 12px!important;
          text-align:center!important;
          align-items:center!important;
        }
        html.pb-journey #pb-route-context .pb-route-step-nav a.pb-route-next{
          background:#555bb6!important;
          border-color:#555bb6!important;
          color:#fff!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions{
          flex-direction:row!important;align-items:center!important;justify-content:flex-start!important;
          gap:8px!important;width:100%!important;
        }
        html.pb-journey #pb-route-context .pb-article-progress-actions > *,
        html.pb-journey #pb-route-context .pb-ayudas-final-actions > *{
          width:auto!important;flex:0 1 auto!important;min-height:40px!important;
          padding:9px 12px!important;font-size:.82rem!important;line-height:1.25!important;
          border-radius:9px!important;white-space:normal!important;
        }
        html.pb-journey #pb-route-context button[data-pb-toggle-progress]{
          flex:1 1 100%!important;width:100%!important;
        }
        html.pb-journey #pb-route-context #pb-ayudas-final-done:not([hidden]){
          display:inline-flex!important;max-width:100%!important;
        }
      }
    `;
    /* Una única etiqueta de estado; el resumen se muestra desde la ruta sin F5. */
    style.textContent += `
      html.pb-journey #pb-route-context .pb-progress-status-label,
      html.pb-journey #pb-route-context .pb-ayudas-final-copy{display:none!important}
      html.pb-journey #pb-route-context .pb-route-summary{display:inline-flex!important;align-items:center!important;justify-content:center!important;background:#5863df!important;color:#fff!important;padding:9px 14px!important;border-radius:10px!important;text-decoration:none!important;font-weight:800!important;min-height:40px!important}
      html.pb-journey #pb-route-context #pb-ayudas-final-done[hidden]{display:none!important}
      html.pb-journey #pb-route-context #pb-ayudas-final-done:not([hidden]){display:inline-flex!important}
      @media(max-width:700px){html.pb-journey #pb-route-context .pb-route-summary{grid-column:1/-1!important;width:100%!important;box-sizing:border-box!important}}
    `;
    document.head.appendChild(style);
  }

  migrateLegacyProgress();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', aplicar, { once:true }); else aplicar();
  window.addEventListener('storage', aplicar);
  window.addEventListener('papelesbebe:progress', aplicar);

  document.addEventListener('click', (event) => {
    const panelLink = event.target.closest('a[data-pb-open-panel]');
    if (!panelLink) return;
    event.preventDefault();
    window.location.assign('/mi-panel/');
  });

  // Páginas estáticas: aplicar al cargar y cuando cambie el progreso.
  // Evitar reescaneos y mutaciones en cascada del DOM en dispositivos móviles.
})();