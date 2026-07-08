/* ════════════════════════════════════════════════════════════════════
   VOGX — Service / Package Detail Modal  (service-detail-modal.js)
   ------------------------------------------------------------------
   A single, self-contained, reusable popup for viewing the full
   details of a SERVICE or a PACKAGE — image, price, duration,
   description, "How it works" steps (services) / "What's included"
   (packages) — with an Add-to-cart button, styled like the
   Urban Company detail popup, using the same VOGX theme tokens as
   services_listing.html.

   HOW TO USE ON ANY PAGE (services listing, cart, my-bookings, etc.):

     1. Add this ONE line before </body>, after your page's own
        <script> block (order doesn't matter, but after is safest):

          <script src="service-detail-modal.js"></script>

     2. Open it from anywhere with:

          openServiceDetail(serviceId);      // e.g. from a "View details" link
          openPackageDetail(packageId);       // e.g. from a "View Package" link

        Example (replace an <a href="service-detail.html?id=..."> link):

          <a href="javascript:void(0)" onclick="openServiceDetail(42)">View details</a>

     That's it — no other HTML/CSS needs to exist on the page. The
     modal injects its own markup + styles once, on first use, and
     removes itself cleanly if called twice.

   INTEGRATION WITH YOUR EXISTING CART:
     If the host page already defines `updateCartBadge()` (all VOGX
     pages do), this modal calls it after every Add/±, so the navbar
     badge stays in sync automatically. Cart data is read/written to
     the same `vogx_cart` localStorage key & item shape your other
     pages already use: { id, type: 'service'|'package', name, price,
     image, qty }.

     If the host page defines `openLogin()`, it's used to prompt login
     when an anonymous user hits "Add". Otherwise a toast is shown.

   ════════════════════════════════════════════════════════════════════ */

(function () {
  if (window.__vogxDetailModalLoaded) return; // avoid double-injection
  window.__vogxDetailModalLoaded = true;

  /* ── CONFIG ──────────────────────────────────────────────────── */
  const API = window.API || 'http://127.0.0.1:8000/api';

  /* ── STYLES ──────────────────────────────────────────────────── */
  const css = `
  .sdm-overlay {
    position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 3000;
    display: none; align-items: flex-start; justify-content: center;
    padding: 40px 20px; overflow-y: auto;
  }
  .sdm-overlay.open { display: flex; }
  .sdm-popup {
    background: var(--white, #fff); border-radius: var(--radius, 12px);
    width: 100%; max-width: 560px; overflow: hidden;
    box-shadow: var(--shadow-md, 0 4px 24px rgba(0,0,0,.12));
    position: relative; margin: auto 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--black, #111);
  }
  .sdm-close {
    position: absolute; top: 14px; right: 14px; z-index: 2;
    width: 34px; height: 34px; border-radius: 50%;
    background: rgba(255,255,255,.92); border: none; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; line-height: 1; color: var(--gray-1, #333);
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
    transition: background .2s ease;
  }
  .sdm-close:hover { background: #fff; }

  .sdm-hero {
    width: 100%; height: 240px; overflow: hidden;
    background: linear-gradient(135deg, var(--brand-tint, #fce4ec), var(--brand-light, #f8bbd0));
    display: flex; align-items: center; justify-content: center;
  }
  .sdm-hero img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .sdm-hero svg { width: 56px; height: 56px; stroke: var(--brand, #c2185b); fill: none; stroke-width: 1.4; opacity: .6; }

  .sdm-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
    color: var(--brand, #c2185b); margin-bottom: 8px;
  }
  .sdm-badge svg { width: 13px; height: 13px; stroke: var(--brand, #c2185b); fill: none; stroke-width: 2; }

  .sdm-content { padding: 22px 26px 28px; max-height: calc(90vh - 240px); overflow-y: auto; }

  .sdm-top-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 14px; }
  .sdm-titleblock { min-width: 0; }
  .sdm-name { font-size: 20px; font-weight: 800; line-height: 1.3; margin-bottom: 8px; }
  .sdm-price-line { font-size: 14.5px; color: var(--gray-2, #666); }
  .sdm-price-line b { color: var(--black, #111); font-size: 16px; font-weight: 700; }
  .sdm-price-line .sdm-dot { margin: 0 6px; color: var(--gray-4, #ccc); }
  .sdm-orig-price { font-size: 13px; color: var(--gray-3, #999); text-decoration: line-through; margin-right: 6px; }
  .sdm-save { font-size: 12px; font-weight: 700; color: #2e7d32; margin-top: 4px; }
  .sdm-action { flex-shrink: 0; }

  .sdm-add-btn {
    padding: 10px 26px; border-radius: 22px; border: 1.5px solid var(--brand, #c2185b);
    background: var(--white, #fff); color: var(--brand, #c2185b);
    font-size: 14px; font-weight: 700; cursor: pointer; white-space: nowrap;
    transition: background .2s ease; font-family: inherit;
  }
  .sdm-add-btn:hover { background: var(--brand-tint, #fce4ec); }
  .sdm-added-btn {
    padding: 10px 26px; border-radius: 22px; border: 1.5px solid var(--brand, #c2185b);
    background: var(--brand, #c2185b); color: var(--white, #fff);
    font-size: 14px; font-weight: 700; cursor: pointer; white-space: nowrap;
    transition: background .2s ease, color .2s ease; font-family: inherit;
  }
  .sdm-added-btn:hover { background: var(--white, #fff); color: var(--brand, #c2185b); }

  .sdm-desc { font-size: 14px; color: var(--gray-2, #666); line-height: 1.65; margin-bottom: 24px; }

  .sdm-section-title { font-size: 16px; font-weight: 800; margin-bottom: 16px; }

  /* "How it works" numbered timeline (services) */
  .sdm-steps-list { position: relative; padding-left: 36px; margin-bottom: 8px; }
  .sdm-step { position: relative; padding-bottom: 22px; }
  .sdm-step:last-child { padding-bottom: 0; }
  .sdm-step::before {
    content: ''; position: absolute; left: -24px; top: 26px; bottom: -4px; width: 2px;
    background: var(--gray-4, #ccc);
  }
  .sdm-step:last-child::before { display: none; }
  .sdm-step-num {
    position: absolute; left: -36px; top: 0; width: 26px; height: 26px; border-radius: 50%;
    background: var(--brand-tint, #fce4ec); color: var(--brand-dark, #880e4f);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 12.5px; flex-shrink: 0;
  }
  .sdm-step-title { font-size: 14.5px; font-weight: 700; margin-bottom: 4px; }
  .sdm-step-desc { font-size: 13.5px; color: var(--gray-2, #666); line-height: 1.55; }

  /* "What's included" (packages) */
  .sdm-included-list { border-top: 1px solid var(--gray-5, #f5f5f5); margin-bottom: 6px; }
  .sdm-included-row {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 12px 0; border-bottom: 1px solid var(--gray-5, #f5f5f5);
  }
  .sdm-included-name { font-size: 13.5px; font-weight: 600; }
  .sdm-included-dur { font-size: 12px; color: var(--gray-3, #999); margin-top: 2px; }
  .sdm-included-price { font-size: 13px; color: var(--gray-3, #999); flex-shrink: 0; }

  .sdm-loading, .sdm-error { padding: 40px 20px; text-align: center; color: var(--gray-3, #999); font-size: 14px; }

  .sdm-toast-rack {
    position: fixed; top: 76px; right: 20px; z-index: 3500;
    display: flex; flex-direction: column; gap: 8px;
  }
  .sdm-toast {
    min-width: 220px; padding: 12px 16px; border-radius: 8px;
    background: #222; color: #fff; font-size: 13px; font-weight: 500;
    box-shadow: 0 4px 24px rgba(0,0,0,.12);
  }
  .sdm-toast.success { border-left: 3px solid #4caf50; }
  .sdm-toast.error { border-left: 3px solid #f44336; }

  @media (max-width: 600px) {
    .sdm-overlay { padding: 0; align-items: flex-end; }
    .sdm-popup { max-width: 100%; border-radius: var(--radius, 12px) var(--radius, 12px) 0 0; max-height: 92vh; overflow-y: auto; }
    .sdm-hero { height: 190px; }
    .sdm-content { max-height: none; }
  }
  `;
  const styleTag = document.createElement('style');
  styleTag.textContent = css;
  document.head.appendChild(styleTag);

  /* ── MARKUP ──────────────────────────────────────────────────── */
  const wrap = document.createElement('div');
  wrap.innerHTML = `
    <div class="sdm-overlay" id="sdmOverlay" role="dialog" aria-modal="true" aria-label="Details">
      <div class="sdm-popup">
        <button class="sdm-close" id="sdmClose" aria-label="Close">&times;</button>
        <div id="sdmBody"></div>
      </div>
    </div>
    <div class="sdm-toast-rack" id="sdmToastRack" aria-live="polite"></div>
  `;
  document.body.appendChild(wrap);

  const overlayEl = document.getElementById('sdmOverlay');
  const bodyEl = document.getElementById('sdmBody');

  /* ── UTILS ───────────────────────────────────────────────────── */
  function esc(s) {
    if (typeof window.esc === 'function') return window.esc(s);
    return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  }
  function money(n) { return `₹${Number(n || 0).toLocaleString('en-IN')}`; }

  function sdmToast(msg, type) {
    if (typeof window.toast === 'function') { window.toast(msg, type); return; }
    const rack = document.getElementById('sdmToastRack');
    const t = document.createElement('div');
    t.className = `sdm-toast ${type || 'success'}`;
    t.textContent = msg;
    rack.appendChild(t);
    setTimeout(() => t.remove(), 3200);
  }

  function sdmIsLoggedIn() {
    if (typeof window.isLoggedIn === 'function') return window.isLoggedIn();
    return !!localStorage.getItem('auth_token');
  }
  function sdmOpenLogin() {
    if (typeof window.openLogin === 'function') { window.openLogin(); return; }
    sdmToast('Please log in to add items to your cart.', 'error');
  }
  function sdmUpdateBadge() {
    if (typeof window.updateCartBadge === 'function') { window.updateCartBadge(); return; }
    const badge = document.getElementById('cartBadge');
    if (!badge) return;
    const count = sdmGetCart().reduce((sum, i) => sum + (i.qty || 1), 0);
    badge.textContent = count;
    badge.classList.toggle('visible', count > 0);
  }

  /* cart — same schema/localStorage key as the rest of the VOGX site */
  function sdmGetCart() { try { return JSON.parse(localStorage.getItem('vogx_cart') || '[]'); } catch { return []; } }
  function sdmSaveCart(items) { localStorage.setItem('vogx_cart', JSON.stringify(items)); sdmUpdateBadge(); }
  function sdmCartHas(id, type) {
    return sdmGetCart().some(c => String(c.id) === String(id) && c.type === type);
  }
  function sdmCartAdd(item) {
    const cart = sdmGetCart();
    const existing = cart.find(c => String(c.id) === String(item.id) && c.type === item.type);
    if (existing) return; // already in cart, one-per-service only
    cart.push({ ...item, qty: 1 });
    sdmSaveCart(cart);
    sdmToast(`${item.name} added to cart`, 'success');
    if (typeof window.refreshAllSteppers === 'function') window.refreshAllSteppers();
    renderActionArea();
  }
  function sdmCartRemove(id, type) {
    const cart = sdmGetCart();
    const idx = cart.findIndex(c => String(c.id) === String(id) && c.type === type);
    if (idx === -1) return;
    cart.splice(idx, 1);
    sdmSaveCart(cart);
    if (typeof window.refreshAllSteppers === 'function') window.refreshAllSteppers();
    renderActionArea();
  }

  /* ── API FETCH ───────────────────────────────────────────────── */
  async function sdmApiFetch(path) {
    if (typeof window.apiFetch === 'function') return window.apiFetch(path);
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('auth_token');
    if (token) headers['Authorization'] = `Token ${token}`;
    const res = await fetch(`${API}${path}`, { headers });
    const data = await res.json();
    if (!res.ok) throw { status: res.status, data };
    return data;
  }

  /* ── STATE for currently-open item (used by action area re-renders) ── */
  let _current = null; // { id, type, name, price, image }

  function actionAreaHTML() {
    if (!_current) return '';
    if (sdmCartHas(_current.id, _current.type)) {
      return `<button class="sdm-added-btn" id="sdmRemoveBtn">Added ✓</button>`;
    }
    return `<button class="sdm-add-btn" id="sdmAddBtn">Add</button>`;
  }

  function renderActionArea() {
    const el = document.getElementById('sdmAction');
    if (!el) return;
    el.innerHTML = actionAreaHTML();
    wireActionArea();
  }

  function wireActionArea() {
    const addBtn = document.getElementById('sdmAddBtn');
    if (addBtn) addBtn.addEventListener('click', () => sdmCartAdd(_current));
    const removeBtn = document.getElementById('sdmRemoveBtn');
    if (removeBtn) removeBtn.addEventListener('click', () => sdmCartRemove(_current.id, _current.type));
  }

  /* ── OPEN / CLOSE ────────────────────────────────────────────── */
  function openOverlay() {
    overlayEl.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeDetailModal() {
    overlayEl.classList.remove('open');
    document.body.style.overflow = '';
    _current = null;
  }
  window.closeDetailModal = closeDetailModal;

  document.getElementById('sdmClose').addEventListener('click', closeDetailModal);
  overlayEl.addEventListener('click', e => { if (e.target === overlayEl) closeDetailModal(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && overlayEl.classList.contains('open')) closeDetailModal(); });

  const ICON_SERVICE = `<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>`;
  const ICON_PACKAGE = `<svg viewBox="0 0 24 24"><path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/></svg>`;

  /* ── RENDER: SERVICE ─────────────────────────────────────────── */
  function renderService(svc) {
    const heroImg = svc.detail_image || svc.preview_image || '';
    const cartImg = svc.preview_image || '';
    _current = { id: svc.id, type: 'service', name: svc.name, price: Number(svc.price), image: cartImg };

    const steps = svc.steps || [];

    bodyEl.innerHTML = `
      <div class="sdm-hero">
        ${heroImg ? `<img src="${heroImg}" alt="${esc(svc.name)}">` : ICON_SERVICE}
      </div>
      <div class="sdm-content">
        <div class="sdm-badge">${ICON_SERVICE} ${esc(svc.category_name || 'Service')}</div>
        <div class="sdm-top-row">
          <div class="sdm-titleblock">
            <h3 class="sdm-name">${esc(svc.name)}</h3>
            <div class="sdm-price-line"><b>${money(svc.price)}</b><span class="sdm-dot">•</span>${svc.duration_minutes} mins</div>
          </div>
          <div class="sdm-action" id="sdmAction">${actionAreaHTML()}</div>
        </div>
        <p class="sdm-desc">${esc(svc.description || '')}</p>
        ${steps.length ? `
          <div class="sdm-section-title">How it works</div>
          <div class="sdm-steps-list">
            ${steps
              .slice()
              .sort((a, b) => a.step_number - b.step_number)
              .map(s => `
                <div class="sdm-step">
                  <div class="sdm-step-num">${s.step_number}</div>
                  <div class="sdm-step-title">${esc(s.title)}</div>
                  ${s.description ? `<div class="sdm-step-desc">${esc(s.description)}</div>` : ''}
                </div>
              `).join('')}
          </div>
        ` : ''}
      </div>
    `;
    wireActionArea();
  }

  /* ── RENDER: PACKAGE ─────────────────────────────────────────── */
  function renderPackage(pkg) {
    const img = pkg.image || '';
    _current = { id: pkg.id, type: 'package', name: pkg.name, price: Number(pkg.package_price), image: img };

    const services = pkg.services || [];
    const original = services.reduce((sum, s) => sum + Number(s.price), 0);
    const price = Number(pkg.package_price);
    const totalMinutes = services.reduce((sum, s) => sum + Number(s.duration_minutes || 0), 0);

    bodyEl.innerHTML = `
      <div class="sdm-hero">
        ${img ? `<img src="${img}" alt="${esc(pkg.name)}">` : ICON_PACKAGE}
      </div>
      <div class="sdm-content">
        <div class="sdm-badge">${ICON_PACKAGE} Package</div>
        <div class="sdm-top-row">
          <div class="sdm-titleblock">
            <h3 class="sdm-name">${esc(pkg.name)}</h3>
            <div class="sdm-price-line">
              ${original > price ? `<span class="sdm-orig-price">${money(original)}</span>` : ''}
              <b>${money(price)}</b><span class="sdm-dot">•</span>${totalMinutes} mins
            </div>
            ${original > price ? `<div class="sdm-save">You save ${money(original - price)}</div>` : ''}
          </div>
          <div class="sdm-action" id="sdmAction">${actionAreaHTML()}</div>
        </div>
        <p class="sdm-desc">${esc(pkg.description || '')}</p>
        <div class="sdm-section-title">What's included</div>
        <div class="sdm-included-list">
          ${services.map(s => `
            <div class="sdm-included-row">
              <div>
                <div class="sdm-included-name">${esc(s.name)}</div>
                <div class="sdm-included-dur">${s.duration_minutes} mins</div>
              </div>
              <div class="sdm-included-price">${money(s.price)}</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    wireActionArea();
  }

  function renderLoading() {
    bodyEl.innerHTML = `<div class="sdm-loading">Loading…</div>`;
  }
  function renderError(msg) {
    bodyEl.innerHTML = `<div class="sdm-error">${esc(msg || 'Could not load details')}</div>`;
  }

  /* ── PUBLIC API ──────────────────────────────────────────────── */
  window.openServiceDetail = async function (id, preloaded) {
    openOverlay();
    if (preloaded) { renderService(preloaded); return; }
    renderLoading();
    try {
      const svc = await sdmApiFetch(`/services/services/${id}/`);
      renderService(svc);
    } catch {
      renderError('Could not load service details.');
    }
  };

  window.openPackageDetail = async function (id, preloaded) {
    openOverlay();
    if (preloaded) { renderPackage(preloaded); return; }
    renderLoading();
    try {
      const pkg = await sdmApiFetch(`/services/packages/${id}/`);
      renderPackage(pkg);
    } catch {
      renderError('Could not load package details.');
    }
  };
})();