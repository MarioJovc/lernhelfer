/* @ds-bundle: {"format":4,"namespace":"TUDa","components":[{"name":"Button"},{"name":"TextField"},{"name":"Select"},{"name":"Checkbox"},{"name":"Radio"},{"name":"Switch"},{"name":"SegmentedControl"},{"name":"DatePicker"},{"name":"Tabs"},{"name":"TopBar"},{"name":"Sidebar"},{"name":"Breadcrumbs"},{"name":"LogoSlot"},{"name":"Card"},{"name":"Table"},{"name":"List"},{"name":"Modal"},{"name":"Alert"},{"name":"Toast"},{"name":"Tooltip"},{"name":"Badge"},{"name":"Tag"},{"name":"Pagination"},{"name":"Progress"},{"name":"Stepper"},{"name":"Skeleton"},{"name":"EmptyState"},{"name":"Avatar"},{"name":"Menu"},{"name":"Icon"}]} */
/* TU Darmstadt App Design System – bundle.js (Vanilla JS, keine Abhängigkeiten).
   Stellt window.TUDa bereit und verdrahtet alle Komponenten mit data-tuda-* Attributen.
   TUDa.init(root) ist idempotent und läuft automatisch nach DOMContentLoaded. */
(function () {
  'use strict';
  var doc = document;

  /* ------------------------------------------------------------ Icons (24-px-Raster, 1,75 px Strich) */
  var ICONS = {
    'search': '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.35-4.35"/>',
    'x': '<path d="M6 6l12 12M18 6L6 18"/>',
    'check': '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    'chevron-down': '<path d="M6 9l6 6 6-6"/>',
    'chevron-up': '<path d="M6 15l6-6 6 6"/>',
    'chevron-left': '<path d="M15 6l-6 6 6 6"/>',
    'chevron-right': '<path d="M9 6l6 6-6 6"/>',
    'chevrons-up-down': '<path d="M8 9l4-4 4 4M8 15l4 4 4-4"/>',
    'arrow-up': '<path d="M12 19V5M6.5 10.5L12 5l5.5 5.5"/>',
    'arrow-down': '<path d="M12 5v14M6.5 13.5L12 19l5.5-5.5"/>',
    'arrow-right': '<path d="M5 12h14M13.5 6.5L19 12l-5.5 5.5"/>',
    'arrow-left': '<path d="M19 12H5M10.5 6.5L5 12l5.5 5.5"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'minus': '<path d="M5 12h14"/>',
    'calendar': '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    'clock': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    'home': '<path d="M4 10.5L12 4l8 6.5V19a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H5.5A1.5 1.5 0 0 1 4 19z"/>',
    'dashboard': '<rect x="3.5" y="3.5" width="7" height="8" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="5" rx="1.5"/><rect x="13.5" y="11.5" width="7" height="9" rx="1.5"/><rect x="3.5" y="14.5" width="7" height="6" rx="1.5"/>',
    'book': '<path d="M12 6.5C10.5 5 8 4.5 4 4.5v14c4 0 6.5.5 8 2 1.5-1.5 4-2 8-2v-14c-4 0-6.5.5-8 2z"/><path d="M12 6.5v14"/>',
    'graduation': '<path d="M2.5 9.5L12 5l9.5 4.5L12 14z"/><path d="M6.5 11.6v4.4c0 1.5 2.5 3 5.5 3s5.5-1.5 5.5-3v-4.4M21.5 9.5v5"/>',
    'clipboard-check': '<rect x="5" y="4.5" width="14" height="16" rx="2"/><path d="M9 4.5v-1h6v1M9 13l2 2 4-4"/>',
    'user': '<circle cx="12" cy="8.5" r="4"/><path d="M4.5 20c.8-3.6 3.8-6 7.5-6s6.7 2.4 7.5 6"/>',
    'users': '<circle cx="9" cy="8.5" r="3.5"/><path d="M2.5 19.5c.6-3.2 3.2-5.5 6.5-5.5s5.9 2.3 6.5 5.5M15.5 5.2a3.5 3.5 0 0 1 0 6.6M17.5 14.3c2.2.7 3.6 2.6 4 5.2"/>',
    'settings': '<path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
    'bell': '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    'info': '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.6v.15"/>',
    'help': '<circle cx="12" cy="12" r="8.5"/><path d="M9.6 9.4a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.7M12 16.9v.1"/>',
    'alert-triangle': '<path d="M10.3 4.6L3 17.5a2 2 0 0 0 1.7 3h14.6a2 2 0 0 0 1.7-3L13.7 4.6a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4M12 16.9v.1"/>',
    'alert-octagon': '<path d="M8.4 3.5h7.2l5 5v7.2l-5 5H8.4l-5-5V8.5z"/><path d="M12 8v4.5M12 15.9v.1"/>',
    'check-circle': '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.3l2.5 2.5 4.5-5"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'more': '<circle class="is-filled" cx="6" cy="12" r="1.5"/><circle class="is-filled" cx="12" cy="12" r="1.5"/><circle class="is-filled" cx="18" cy="12" r="1.5"/>',
    'filter': '<path d="M4 5.5h16l-6 7.5v5l-4 2v-7z"/>',
    'download': '<path d="M12 4v11M7.5 10.5L12 15l4.5-4.5M5 19.5h14"/>',
    'upload': '<path d="M12 15V4M7.5 8.5L12 4l4.5 4.5M5 19.5h14"/>',
    'external': '<path d="M14 4.5h5.5V10M19.5 4.5L11 13"/><path d="M17 13.5v4a2 2 0 0 1-2 2H6.5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h4"/>',
    'log-out': '<path d="M14 4.5H6.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H14"/><path d="M10 12h10M16.5 8.5L20 12l-3.5 3.5"/>',
    'log-in': '<path d="M10 4.5h7.5a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H10"/><path d="M4 12h10M10.5 8.5L14 12l-3.5 3.5"/>',
    'trash': '<path d="M4.5 7h15M9.5 7V5a1.5 1.5 0 0 1 1.5-1.5h2A1.5 1.5 0 0 1 14.5 5v2M6.5 7l.8 11.6a2 2 0 0 0 2 1.9h5.4a2 2 0 0 0 2-1.9L17.5 7"/>',
    'edit': '<path d="M4.5 19.5l1-4.2L15.8 5a1.9 1.9 0 0 1 2.7 0l.5.5a1.9 1.9 0 0 1 0 2.7L8.7 18.5z"/><path d="M13.5 7.5l3 3"/>',
    'eye': '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6L6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4L6 18M18 6l1.4-1.4"/>',
    'moon': '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    'monitor': '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M8.5 20h7M12 16.5V20"/>',
    'map-pin': '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.5"/>',
    'building': '<path d="M4.5 20.5v-15a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v15M14.5 9.5h4a1 1 0 0 1 1 1v10M3 20.5h18M8 8h3M8 11.5h3M8 15h3"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 7l8.5 6 8.5-6"/>',
    'file': '<path d="M14 3.5H7.5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8z"/><path d="M14 3.5V8h4.5M9 13h6M9 16.5h4"/>',
    'list': '<path d="M9 6.5h11M9 12h11M9 17.5h11M4 6.5h1M4 12h1M4 17.5h1"/>',
    'bookmark': '<path d="M6.5 4.5a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v16L12 16.5l-5.5 4z"/>',
    'star': '<path d="M12 3.8l2.5 5.1 5.6.8-4 3.9.9 5.6-5-2.6-5 2.6.9-5.6-4-3.9 5.6-.8z"/>',
    'lock': '<rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    'globe': '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.3 2.4 3.5 5.2 3.5 8.5s-1.2 6.1-3.5 8.5c-2.3-2.4-3.5-5.2-3.5-8.5s1.2-6.1 3.5-8.5z"/>',
    'sort': '<path d="M8 4.5v15M4.5 8L8 4.5 11.5 8M16 19.5v-15M12.5 16l3.5 3.5 3.5-3.5"/>',
    'panel-left': '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><path d="M9.5 4.5v15"/>',
    'copy': '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5v-2a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>',
    'sparkle': '<path d="M12 3.5l1.5 7 7 1.5-7 1.5-1.5 7-1.5-7-7-1.5 7-1.5z"/>',
    'refresh': '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3M19.5 4.5v4h-4"/>'
  };
  function icon(name, opts) {
    opts = opts || {};
    var body = ICONS[name] || ICONS['help'];
    var cls = 'tuda-icon' + (opts.size ? ' tuda-icon--' + opts.size : '') + (opts.className ? ' ' + opts.className : '');
    var a11y = opts.label ? ' role="img" aria-label="' + esc(opts.label) + '"' : ' aria-hidden="true" focusable="false"';
    return '<svg class="' + cls + '" viewBox="0 0 24 24"' + a11y + '>' + body + '</svg>';
  }
  function hydrateIcons(root) {
    qsa('svg[data-icon]', root).forEach(function (svg) {
      var name = svg.getAttribute('data-icon');
      if (svg.getAttribute('data-icon-ready') === name) return;
      svg.setAttribute('viewBox', '0 0 24 24');
      if (!svg.classList.contains('tuda-icon')) svg.classList.add('tuda-icon');
      if (!svg.hasAttribute('aria-label')) { svg.setAttribute('aria-hidden', 'true'); svg.setAttribute('focusable', 'false'); }
      else svg.setAttribute('role', 'img');
      svg.innerHTML = ICONS[name] || ICONS['help'];
      svg.setAttribute('data-icon-ready', name);
    });
  }

  /* ------------------------------------------------------------ Helpers */
  function qsa(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function once(el, key) { var k = 'tudaInit' + key; if (el.dataset[k]) return false; el.dataset[k] = '1'; return true; }
  function lang(el) { var l = ((el && el.closest('[lang]')) || doc.documentElement).getAttribute('lang') || 'de'; return l.slice(0, 2).toLowerCase() === 'en' ? 'en' : 'de'; }
  var T = {
    de: { prev: 'Vorheriger Monat', next: 'Nächster Monat', today: 'Heute', close: 'Schließen', week: 'KW', weekLong: 'Kalenderwoche', choose: 'Datum wählen', todaySuffix: ', heute',
          days: ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'], daysLong: ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'],
          results: function (n) { return n === 0 ? 'Keine Vorschläge' : n === 1 ? '1 Vorschlag verfügbar' : n + ' Vorschläge verfügbar'; },
          sorted: function (c, d) { return 'Sortiert nach ' + c + ', ' + (d === 'ascending' ? 'aufsteigend' : 'absteigend'); },
          selected: function (n) { return n === 1 ? '1 ausgewählt' : n + ' ausgewählt'; }, dismiss: 'Hinweis schließen', copied: 'In die Zwischenablage kopiert' },
    en: { prev: 'Previous month', next: 'Next month', today: 'Today', close: 'Close', week: 'Wk', weekLong: 'Calendar week', choose: 'Choose date', todaySuffix: ', today',
          days: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'], daysLong: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
          results: function (n) { return n === 0 ? 'No suggestions' : n === 1 ? '1 suggestion available' : n + ' suggestions available'; },
          sorted: function (c, d) { return 'Sorted by ' + c + ', ' + d; },
          selected: function (n) { return n + ' selected'; }, dismiss: 'Dismiss', copied: 'Copied to clipboard' }
  };
  var liveEl;
  function announce(msg) {
    if (!liveEl) {
      liveEl = doc.createElement('div'); liveEl.className = 'tuda-sr-only'; liveEl.setAttribute('aria-live', 'polite'); liveEl.setAttribute('role', 'status');
      doc.body.appendChild(liveEl);
    }
    liveEl.textContent = ''; setTimeout(function () { liveEl.textContent = msg; }, 60);
  }
  function focusables(root) {
    return qsa('a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])', root)
      .filter(function (el) { return el.offsetParent !== null || el === doc.activeElement; });
  }

  /* ------------------------------------------------------------ Theme */
  var THEME_KEY = 'tuda-theme';
  var theme = {
    get: function () { try { return localStorage.getItem(THEME_KEY) || 'system'; } catch (e) { return 'system'; } },
    effective: function () {
      var m = doc.documentElement.getAttribute('data-theme');
      if (m === 'light' || m === 'dark') return m;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },
    set: function (mode) {
      if (mode === 'light' || mode === 'dark') doc.documentElement.setAttribute('data-theme', mode);
      else doc.documentElement.removeAttribute('data-theme');
      try { localStorage.setItem(THEME_KEY, mode); } catch (e) { /* Speicher nicht verfügbar */ }
      qsa('[data-tuda-theme-control] input[type="radio"]').forEach(function (r) { r.checked = r.value === mode; });
      doc.dispatchEvent(new CustomEvent('tuda:themechange', { detail: { mode: mode, effective: theme.effective() } }));
    },
    restore: function () { var m = theme.get(); if (m !== 'system') theme.set(m); }
  };
  function initThemeControls(root) {
    qsa('[data-tuda-theme-control]', root).forEach(function (group) {
      if (!once(group, 'Theme')) return;
      var current = doc.documentElement.getAttribute('data-theme') || theme.get();
      qsa('input[type="radio"]', group).forEach(function (r) {
        r.checked = r.value === current;
        r.addEventListener('change', function () { if (r.checked) theme.set(r.value); });
      });
    });
  }

  /* ------------------------------------------------------------ Tabs */
  function initTabs(root) {
    qsa('[data-tuda-tabs]', root).forEach(function (wrap) {
      if (!once(wrap, 'Tabs')) return;
      var list = wrap.querySelector('[role="tablist"]');
      var tabs = qsa('[role="tab"]', list);
      var ind = list.querySelector('.tuda-tabs__indicator');
      function move(tab) {
        if (!ind || !tab) return;
        ind.style.setProperty('--_x', tab.offsetLeft + 'px');
        ind.style.setProperty('--_w', tab.offsetWidth + 'px');
      }
      function select(tab, focus) {
        tabs.forEach(function (t) {
          var on = t === tab;
          t.setAttribute('aria-selected', on ? 'true' : 'false');
          t.tabIndex = on ? 0 : -1;
          var p = doc.getElementById(t.getAttribute('aria-controls'));
          if (p) p.hidden = !on;
        });
        if (focus) { tab.focus(); tab.scrollIntoView({ block: 'nearest', inline: 'nearest' }); }
        move(tab);
      }
      tabs.forEach(function (t, i) {
        t.addEventListener('click', function () { select(t, false); });
        t.addEventListener('keydown', function (e) {
          var idx = null;
          if (e.key === 'ArrowRight') idx = (i + 1) % tabs.length;
          else if (e.key === 'ArrowLeft') idx = (i - 1 + tabs.length) % tabs.length;
          else if (e.key === 'Home') idx = 0;
          else if (e.key === 'End') idx = tabs.length - 1;
          if (idx !== null) { e.preventDefault(); select(tabs[idx], true); }
        });
      });
      var active = tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0] || tabs[0];
      select(active, false);
      wrap.classList.add('is-ready');
      if (window.ResizeObserver) new ResizeObserver(function () { move(tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0]); }).observe(list);
      if (doc.fonts && doc.fonts.ready) doc.fonts.ready.then(function () { move(tabs.filter(function (t) { return t.getAttribute('aria-selected') === 'true'; })[0]); });
    });
  }

  /* ------------------------------------------------------------ Modal (native <dialog>) */
  var modal = {
    open: function (id, opener) {
      var dlg = typeof id === 'string' ? doc.getElementById(id) : id;
      if (!dlg || dlg.open) return;
      dlg._opener = opener || doc.activeElement;
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
      var auto = dlg.querySelector('[autofocus]');
      if (auto) auto.focus();
    },
    close: function (id, value) {
      var dlg = typeof id === 'string' ? doc.getElementById(id) : id;
      if (!dlg) return;
      if (dlg.close) dlg.close(value); else dlg.removeAttribute('open');
    }
  };
  function initModals(root) {
    qsa('[data-tuda-open]', root).forEach(function (btn) {
      if (!once(btn, 'Open')) return;
      btn.setAttribute('aria-haspopup', 'dialog');
      btn.addEventListener('click', function () { modal.open(btn.getAttribute('data-tuda-open'), btn); });
    });
    qsa('dialog.tuda-modal', root).forEach(function (dlg) {
      if (!once(dlg, 'Dialog')) return;
      dlg.addEventListener('click', function (e) {
        if (e.target.closest('[data-tuda-close]')) { modal.close(dlg, e.target.closest('[data-tuda-close]').value || ''); return; }
        if (e.target === dlg && !dlg.hasAttribute('data-static')) {
          var r = dlg.getBoundingClientRect();
          if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) modal.close(dlg);
        }
      });
      dlg.addEventListener('close', function () {
        if (dlg._opener && doc.contains(dlg._opener)) dlg._opener.focus();
        dlg.dispatchEvent(new CustomEvent('tuda:modalclose', { detail: { value: dlg.returnValue } }));
      });
    });
  }

  /* ------------------------------------------------------------ Toast */
  var STATUS_ICON = { success: 'check-circle', warning: 'alert-triangle', error: 'alert-octagon', info: 'info' };
  function toast(o) {
    o = o || {};
    var tone = o.tone || 'info';
    var region = o.region || doc.querySelector('.tuda-toast-region:not(.tuda-toast-region--inline)');
    if (!region) {
      region = doc.createElement('div'); region.className = 'tuda-toast-region';
      region.setAttribute('aria-live', 'polite'); region.setAttribute('aria-label', lang() === 'en' ? 'Notifications' : 'Benachrichtigungen');
      doc.body.appendChild(region);
    }
    var t = doc.createElement('div');
    t.className = 'tuda-toast tuda-toast--' + tone;
    if (tone === 'error') t.setAttribute('role', 'alert');
    t.innerHTML = icon(STATUS_ICON[tone]) +
      '<div class="tuda-toast__content"><p class="tuda-toast__title">' + esc(o.title || '') + '</p>' + (o.text ? '<p class="tuda-toast__text">' + esc(o.text) + '</p>' : '') + '</div>' +
      '<div class="tuda-toast__actions">' + (o.action ? '<button type="button" class="tuda-btn tuda-btn--ghost tuda-btn--sm" data-act>' + esc(o.action.label) + '</button>' : '') +
      '<button type="button" class="tuda-btn tuda-btn--ghost tuda-btn--neutral tuda-btn--icon tuda-btn--sm" data-close aria-label="' + (lang() === 'en' ? 'Close notification' : 'Benachrichtigung schließen') + '">' + icon('x') + '</button></div>';
    region.appendChild(t);
    var timer, remaining = o.timeout || 6000, started;
    function leave() {
      clearTimeout(timer);
      t.classList.add('is-leaving');
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 220);
    }
    function start() { if (tone === 'error' || o.timeout === 0) return; started = Date.now(); timer = setTimeout(leave, remaining); }
    function pause() { if (!started) return; clearTimeout(timer); remaining -= Date.now() - started; started = null; }
    t.addEventListener('mouseenter', pause); t.addEventListener('mouseleave', start);
    t.addEventListener('focusin', pause); t.addEventListener('focusout', start);
    t.querySelector('[data-close]').addEventListener('click', leave);
    var act = t.querySelector('[data-act]');
    if (act) act.addEventListener('click', function () { if (o.action.onClick) o.action.onClick(); leave(); });
    start();
    return { close: leave, el: t };
  }
  function initToastTriggers(root) {
    qsa('[data-tuda-toast]', root).forEach(function (btn) {
      if (!once(btn, 'Toast')) return;
      btn.addEventListener('click', function () {
        var o = {}; try { o = JSON.parse(btn.getAttribute('data-tuda-toast')); } catch (e) { o = { title: btn.getAttribute('data-tuda-toast') }; }
        if (o.undo) o.action = { label: o.undo };
        toast(o);
      });
    });
  }

  /* ------------------------------------------------------------ Tooltip (WCAG 1.4.13: dismissible, hoverable, persistent) */
  function initTooltips(root) {
    qsa('[data-tuda-tooltip]', root).forEach(function (trg, i) {
      if (!once(trg, 'Tip')) return;
      var tip = doc.createElement('div');
      tip.className = 'tuda-tooltip'; tip.setAttribute('role', 'tooltip'); tip.hidden = true;
      tip.id = 'tuda-tip-' + Math.random().toString(36).slice(2, 8);
      tip.textContent = trg.getAttribute('data-tuda-tooltip');
      doc.body.appendChild(tip);
      var prev = trg.getAttribute('aria-describedby');
      /* Tooltip = aria-label? Dann nicht doppelt vorlesen. */
      if (trg.getAttribute('aria-label') !== tip.textContent) trg.setAttribute('aria-describedby', (prev ? prev + ' ' : '') + tip.id);
      var showT, hideT;
      function place() {
        var r = trg.getBoundingClientRect();
        tip.style.position = 'fixed';
        tip.style.left = '0px'; tip.style.top = '0px';
        var tw = tip.offsetWidth, th = tip.offsetHeight;
        var left = Math.max(8, Math.min(window.innerWidth - tw - 8, r.left + r.width / 2 - tw / 2));
        var top = r.top - th - 10, placement = 'top';
        if (top < 8) { top = r.bottom + 10; placement = 'bottom'; }
        tip.style.left = left + 'px'; tip.style.top = top + 'px';
        tip.style.setProperty('--_arrow', (r.left + r.width / 2 - left) + 'px');
        tip.setAttribute('data-placement', placement);
      }
      function show(delay) {
        clearTimeout(hideT); clearTimeout(showT);
        showT = setTimeout(function () { tip.hidden = false; place(); requestAnimationFrame(function () { tip.classList.add('is-visible'); }); }, delay);
      }
      function hide(delay) {
        clearTimeout(showT); clearTimeout(hideT);
        hideT = setTimeout(function () { tip.classList.remove('is-visible'); tip.hidden = true; }, delay);
      }
      trg.addEventListener('mouseenter', function () { show(300); });
      trg.addEventListener('mouseleave', function () { hide(120); });
      trg.addEventListener('focus', function () { show(0); });
      trg.addEventListener('blur', function () { hide(0); });
      tip.addEventListener('mouseenter', function () { clearTimeout(hideT); });
      tip.addEventListener('mouseleave', function () { hide(120); });
      doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !tip.hidden) hide(0); });
      window.addEventListener('scroll', function () { if (!tip.hidden) place(); }, true);
    });
  }

  /* ------------------------------------------------------------ Menu (Disclosure-Menü) */
  function initMenus(root) {
    qsa('[data-tuda-menu]', root).forEach(function (btn) {
      if (!once(btn, 'Menu')) return;
      var menu = doc.getElementById(btn.getAttribute('aria-controls'));
      if (!menu) return;
      btn.setAttribute('aria-haspopup', 'menu'); btn.setAttribute('aria-expanded', 'false');
      var items = function () { return qsa('[role="menuitem"]', menu); };
      function open(focusFirst) {
        menu.hidden = false; btn.setAttribute('aria-expanded', 'true');
        if (focusFirst !== false) { var it = items(); if (it.length) it[focusFirst === 'last' ? it.length - 1 : 0].focus(); }
        doc.addEventListener('pointerdown', outside, true);
      }
      function close(refocus) {
        menu.hidden = true; btn.setAttribute('aria-expanded', 'false');
        doc.removeEventListener('pointerdown', outside, true);
        if (refocus) btn.focus();
      }
      function outside(e) { if (!menu.contains(e.target) && !btn.contains(e.target)) close(false); }
      btn.addEventListener('click', function () { if (menu.hidden) open(true); else close(false); });
      btn.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); open(true); }
        if (e.key === 'ArrowUp') { e.preventDefault(); open('last'); }
      });
      menu.addEventListener('keydown', function (e) {
        var it = items(), i = it.indexOf(doc.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); it[(i + 1) % it.length].focus(); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); it[(i - 1 + it.length) % it.length].focus(); }
        else if (e.key === 'Home') { e.preventDefault(); it[0].focus(); }
        else if (e.key === 'End') { e.preventDefault(); it[it.length - 1].focus(); }
        else if (e.key === 'Escape') { e.preventDefault(); close(true); }
        else if (e.key === 'Tab') { close(false); }
      });
      menu.addEventListener('click', function (e) { if (e.target.closest('[role="menuitem"]')) close(true); });
    });
  }

  /* ------------------------------------------------------------ Date picker */
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function fmt(d) { return pad(d.getDate()) + '.' + pad(d.getMonth() + 1) + '.' + d.getFullYear(); }
  function parseDate(s) {
    var m = /^\s*(\d{1,2})\.(\d{1,2})\.(\d{2}|\d{4})\s*$/.exec(s || '');
    if (!m) return null;
    var y = +m[3]; if (y < 100) y += 2000;
    var d = new Date(y, +m[2] - 1, +m[1]);
    return d.getDate() === +m[1] && d.getMonth() === +m[2] - 1 ? d : null;
  }
  function iso(s) { if (!s) return null; var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function same(a, b) { return a && b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }
  function isoWeek(d) {
    var t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    var day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day);
    var y0 = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
    return Math.ceil(((t - y0) / 86400000 + 1) / 7);
  }
  function initDatepickers(root) {
    qsa('[data-tuda-datepicker]', root).forEach(function (wrap) {
      if (!once(wrap, 'Date')) return;
      var input = wrap.querySelector('input');
      var btn = wrap.querySelector('[data-tuda-datepicker-toggle]');
      var L = T[lang(wrap)];
      var locale = lang(wrap) === 'en' ? 'en-GB' : 'de-DE';
      var min = iso(wrap.getAttribute('data-min')), max = iso(wrap.getAttribute('data-max'));
      var cal = doc.createElement('div');
      cal.className = 'tuda-calendar'; cal.hidden = true;
      cal.setAttribute('role', 'dialog'); cal.setAttribute('aria-modal', 'true'); cal.setAttribute('aria-label', L.choose);
      wrap.appendChild(cal);
      var view, focusDate;
      btn.setAttribute('aria-haspopup', 'dialog'); btn.setAttribute('aria-expanded', 'false');
      function disabled(d) { return (min && d < min) || (max && d > max); }
      function render() {
        var sel = parseDate(input.value), today = new Date();
        var first = new Date(view.getFullYear(), view.getMonth(), 1);
        var start = new Date(first); start.setDate(1 - ((first.getDay() + 6) % 7));
        var title = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric' }).format(first);
        var full = new Intl.DateTimeFormat(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
        var h = '<div class="tuda-calendar__head">' +
          '<button type="button" class="tuda-btn tuda-btn--ghost tuda-btn--neutral tuda-btn--icon tuda-btn--sm" data-nav="-1" aria-label="' + L.prev + '">' + icon('chevron-left') + '</button>' +
          '<h2 class="tuda-calendar__title" aria-live="polite">' + esc(title) + '</h2>' +
          '<button type="button" class="tuda-btn tuda-btn--ghost tuda-btn--neutral tuda-btn--icon tuda-btn--sm" data-nav="1" aria-label="' + L.next + '">' + icon('chevron-right') + '</button></div>' +
          '<table class="tuda-calendar__grid" role="grid" aria-label="' + esc(title) + '"><thead><tr><th scope="col"><abbr title="' + L.weekLong + '">' + L.week + '</abbr></th>';
        for (var k = 0; k < 7; k++) h += '<th scope="col"><abbr title="' + L.daysLong[k] + '">' + L.days[k] + '</abbr></th>';
        h += '</tr></thead><tbody>';
        var d = new Date(start);
        for (var w = 0; w < 6; w++) {
          h += '<tr><td class="tuda-calendar__kw" aria-hidden="true">' + isoWeek(d) + '</td>';
          for (var j = 0; j < 7; j++) {
            var cls = 'tuda-calendar__day' + (d.getMonth() !== view.getMonth() ? ' is-outside' : '') + (same(d, today) ? ' is-today' : '');
            var label = full.format(d) + (same(d, today) ? L.todaySuffix : '');
            var dis = disabled(d);
            h += '<td role="gridcell" aria-selected="' + (same(d, sel) ? 'true' : 'false') + '"><button type="button" tabindex="-1" class="' + cls + '" data-date="' + d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate() + '" aria-label="' + esc(label) + '"' + (dis ? ' aria-disabled="true"' : '') + '>' + d.getDate() + '</button></td>';
            d.setDate(d.getDate() + 1);
          }
          h += '</tr>';
        }
        h += '</tbody></table><div class="tuda-calendar__foot"><button type="button" class="tuda-btn tuda-btn--ghost tuda-btn--sm" data-today>' + L.today + '</button><button type="button" class="tuda-btn tuda-btn--secondary tuda-btn--sm" data-closecal>' + L.close + '</button></div>';
        cal.innerHTML = h;
        var target = cal.querySelector('[data-date="' + focusDate.getFullYear() + '-' + (focusDate.getMonth() + 1) + '-' + focusDate.getDate() + '"]');
        if (target) target.tabIndex = 0;
        return target;
      }
      function open() {
        var sel = parseDate(input.value);
        focusDate = sel || new Date(); view = new Date(focusDate.getFullYear(), focusDate.getMonth(), 1);
        cal.hidden = false; btn.setAttribute('aria-expanded', 'true');
        var t = render(); if (t) t.focus();
        doc.addEventListener('pointerdown', outside, true);
      }
      function close(refocus) {
        cal.hidden = true; btn.setAttribute('aria-expanded', 'false');
        doc.removeEventListener('pointerdown', outside, true);
        if (refocus) btn.focus();
      }
      function outside(e) { if (!wrap.contains(e.target)) close(false); }
      function go(d) {
        focusDate = d;
        if (d.getMonth() !== view.getMonth() || d.getFullYear() !== view.getFullYear()) view = new Date(d.getFullYear(), d.getMonth(), 1);
        var t = render(); if (t) t.focus();
      }
      function choose(d) {
        if (disabled(d)) return;
        input.value = fmt(d);
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.removeAttribute('aria-invalid');
        close(true);
      }
      btn.addEventListener('click', function () { if (cal.hidden) open(); else close(true); });
      cal.addEventListener('click', function (e) {
        var nav = e.target.closest('[data-nav]');
        if (nav) { var n = +nav.getAttribute('data-nav'); view = new Date(view.getFullYear(), view.getMonth() + n, 1); focusDate = new Date(view); render(); cal.querySelector('[data-nav="' + n + '"]').focus(); return; }
        var day = e.target.closest('[data-date]');
        if (day) { var p = day.getAttribute('data-date').split('-'); choose(new Date(+p[0], +p[1] - 1, +p[2])); return; }
        if (e.target.closest('[data-today]')) { choose(new Date()); return; }
        if (e.target.closest('[data-closecal]')) close(true);
      });
      cal.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') { e.preventDefault(); close(true); return; }
        if (e.key === 'Tab') {
          var f = focusables(cal); if (!f.length) return;
          if (e.shiftKey && doc.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
          else if (!e.shiftKey && doc.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
          return;
        }
        if (!e.target.hasAttribute('data-date')) return;
        var d = new Date(focusDate), handled = true;
        switch (e.key) {
          case 'ArrowRight': d.setDate(d.getDate() + 1); break;
          case 'ArrowLeft': d.setDate(d.getDate() - 1); break;
          case 'ArrowDown': d.setDate(d.getDate() + 7); break;
          case 'ArrowUp': d.setDate(d.getDate() - 7); break;
          case 'Home': d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); break;
          case 'End': d.setDate(d.getDate() + (6 - (d.getDay() + 6) % 7)); break;
          case 'PageUp': d.setMonth(d.getMonth() - (e.shiftKey ? 12 : 1)); break;
          case 'PageDown': d.setMonth(d.getMonth() + (e.shiftKey ? 12 : 1)); break;
          case 'Enter': case ' ': choose(focusDate); break;
          default: handled = false;
        }
        if (handled) { e.preventDefault(); if (e.key !== 'Enter' && e.key !== ' ') go(d); }
      });
      input.addEventListener('blur', function () {
        if (input.value && !parseDate(input.value)) input.setAttribute('aria-invalid', 'true');
        else if (parseDate(input.value)) { input.value = fmt(parseDate(input.value)); input.removeAttribute('aria-invalid'); }
      });
    });
  }

  /* ------------------------------------------------------------ Combobox (Suche mit Vorschlägen) */
  function fold(s) { return String(s).toLowerCase().replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/ß/g, 'ss').normalize('NFD').replace(/[̀-ͯ]/g, ''); }
  function strip(s) { return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
  function highlight(label, q) {
    if (!q) return esc(label);
    var i = strip(label).indexOf(strip(q));
    if (i < 0) return esc(label);
    return esc(label.slice(0, i)) + '<mark class="tuda-mark">' + esc(label.slice(i, i + q.length)) + '</mark>' + esc(label.slice(i + q.length));
  }
  function combobox(wrap, cfg) {
    if (!once(wrap, 'Combo')) return;
    cfg = cfg || {};
    var input = wrap.querySelector('[role="combobox"]');
    var list = doc.getElementById(input.getAttribute('aria-controls'));
    var opts = cfg.options || [];
    if (!opts.length && wrap.getAttribute('data-options')) { try { opts = JSON.parse(wrap.getAttribute('data-options')); } catch (e) { opts = []; } }
    var L = T[lang(wrap)], active = -1, shown = [];
    function renderList() {
      var q = input.value.trim();
      shown = opts.filter(function (o) { return !q || fold(o.label + ' ' + (o.meta || '')).indexOf(fold(q)) > -1; }).slice(0, cfg.max || 8);
      var html = '', group = null;
      if (!shown.length) html = '<li class="tuda-listbox__empty" role="presentation">' + (lang(wrap) === 'en' ? 'No results for “' + esc(q) + '”' : 'Keine Treffer für „' + esc(q) + '“') + '</li>';
      shown.forEach(function (o, i) {
        if (o.group && o.group !== group) { group = o.group; html += '<li class="tuda-listbox__group" role="presentation">' + esc(group) + '</li>'; }
        html += '<li class="tuda-option" role="option" id="' + list.id + '-o' + i + '" aria-selected="false" data-i="' + i + '">' + (o.icon ? icon(o.icon) : '') +
          '<span class="tuda-option__text"><span>' + highlight(o.label, q) + '</span>' + (o.meta ? '<span class="tuda-option__meta">' + esc(o.meta) + '</span>' : '') + '</span></li>';
      });
      list.innerHTML = html;
      active = -1; input.removeAttribute('aria-activedescendant');
      announce(L.results(shown.length));
    }
    function openList() { renderList(); list.hidden = false; input.setAttribute('aria-expanded', 'true'); }
    function closeList() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; }
    function setActive(i) {
      var items = qsa('[role="option"]', list);
      items.forEach(function (it) { it.classList.remove('is-active'); });
      if (i < 0 || !items.length) return;
      active = (i + items.length) % items.length;
      items[active].classList.add('is-active');
      items[active].scrollIntoView({ block: 'nearest' });
      input.setAttribute('aria-activedescendant', items[active].id);
    }
    function pick(i) {
      var o = shown[i]; if (!o) return;
      input.value = o.label; closeList();
      wrap.dispatchEvent(new CustomEvent('tuda:select', { bubbles: true, detail: o }));
      if (cfg.onSelect) cfg.onSelect(o);
    }
    input.addEventListener('input', openList);
    input.addEventListener('focus', function () { if (cfg.openOnFocus) openList(); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (list.hidden) openList(); setActive(active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (list.hidden) openList(); setActive(active - 1); }
      else if (e.key === 'Enter') { if (!list.hidden && active > -1) { e.preventDefault(); pick(active); } }
      else if (e.key === 'Escape') { if (!list.hidden) { e.preventDefault(); closeList(); } else { input.value = ''; } }
    });
    list.addEventListener('pointerdown', function (e) { e.preventDefault(); });
    list.addEventListener('click', function (e) { var li = e.target.closest('[role="option"]'); if (li) pick(+li.getAttribute('data-i')); });
    input.addEventListener('blur', function () { setTimeout(closeList, 100); });
    var clear = wrap.querySelector('[data-tuda-clear]');
    if (clear) clear.addEventListener('click', function () { input.value = ''; input.focus(); closeList(); });
  }
  function initComboboxes(root) { qsa('[data-tuda-combobox]', root).forEach(function (w) { if (w.getAttribute('data-options')) combobox(w); }); }

  /* ------------------------------------------------------------ App shell: mobile Navigation & Sidebar */
  function initShell(root) {
    qsa('[data-tuda-nav-toggle]', root).forEach(function (btn) {
      if (!once(btn, 'Nav')) return;
      var shell = btn.closest('.tuda-shell') || doc.querySelector('.tuda-shell');
      if (!shell) return;
      var nav = shell.querySelector('.tuda-shell__nav');
      var scrim = shell.querySelector('.tuda-shell__scrim');
      btn.setAttribute('aria-expanded', 'false');
      function set(open) {
        shell.classList.toggle('is-nav-open', open); btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (open) { var f = focusables(nav)[0]; if (f) setTimeout(function () { f.focus(); }, 50); } else btn.focus();
      }
      btn.addEventListener('click', function () { set(!shell.classList.contains('is-nav-open')); });
      if (scrim) scrim.addEventListener('click', function () { set(false); });
      shell.addEventListener('keydown', function (e) { if (e.key === 'Escape' && shell.classList.contains('is-nav-open')) set(false); });
    });
    qsa('[data-tuda-sidebar-collapse]', root).forEach(function (btn) {
      if (!once(btn, 'Collapse')) return;
      var sb = doc.getElementById(btn.getAttribute('aria-controls')) || btn.closest('.tuda-sidebar');
      btn.setAttribute('aria-expanded', sb.classList.contains('is-collapsed') ? 'false' : 'true');
      btn.addEventListener('click', function () {
        var c = sb.classList.toggle('is-collapsed');
        btn.setAttribute('aria-expanded', c ? 'false' : 'true');
      });
    });
  }

  /* ------------------------------------------------------------ Kleinkram: Tags, Alerts, Zähler, Kopieren, Busy */
  function initMisc(root) {
    qsa('button.tuda-tag[aria-pressed]', root).forEach(function (tag) {
      if (!once(tag, 'Tag')) return;
      tag.addEventListener('click', function () { tag.setAttribute('aria-pressed', tag.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'); });
    });
    qsa('[data-tuda-remove-tag]', root).forEach(function (b) {
      if (!once(b, 'Rm')) return;
      b.addEventListener('click', function () {
        var tag = b.closest('.tuda-tag, li'); var next = tag && (tag.nextElementSibling || tag.previousElementSibling);
        if (tag) tag.remove();
        var f = next && next.querySelector('button'); if (f) f.focus();
      });
    });
    qsa('[data-tuda-dismiss]', root).forEach(function (b) {
      if (!once(b, 'Dismiss')) return;
      b.addEventListener('click', function () { var a = b.closest('.tuda-alert'); if (a) a.remove(); });
    });
    qsa('[data-tuda-counter]', root).forEach(function (field) {
      if (!once(field, 'Count')) return;
      var out = doc.getElementById(field.getAttribute('data-tuda-counter'));
      var max = +field.getAttribute('maxlength');
      function upd() { if (out) out.textContent = field.value.length + ' / ' + max; }
      field.addEventListener('input', upd); upd();
    });
    qsa('[data-tuda-copy]', root).forEach(function (b) {
      if (!once(b, 'Copy')) return;
      b.addEventListener('click', function () {
        var text = b.getAttribute('data-tuda-copy');
        var done = function () { toast({ title: T[lang(b)].copied, text: text, tone: 'success', timeout: 3000 }); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, done); else done();
      });
    });
    qsa('[data-tuda-demo-busy]', root).forEach(function (b) {
      if (!once(b, 'Busy')) return;
      b.addEventListener('click', function () {
        if (b.getAttribute('aria-busy') === 'true') return;
        b.setAttribute('aria-busy', 'true');
        if (!b.querySelector('.tuda-spinner')) b.insertAdjacentHTML('beforeend', '<span class="tuda-spinner" aria-hidden="true"></span>');
        setTimeout(function () {
          b.removeAttribute('aria-busy');
          var o = {}; try { o = JSON.parse(b.getAttribute('data-tuda-demo-busy')); } catch (e) { o = { title: b.getAttribute('data-tuda-demo-busy') }; }
          if (o.title) toast(Object.assign({ tone: 'success' }, o));
        }, 1400);
      });
    });
  }

  /* ------------------------------------------------------------ Tabelle: Sortieren & Auswahl */
  /* Zahl aus deutschem oder englischem Format („1.234,50“, „1,7“, „10“, „3.5“); sonst NaN (z. B. ISO-Datum) */
  function num(v) {
    var s = String(v).replace(/[\s\u00a0%€]/g, '');
    if (!/^-?\d{1,3}(\.\d{3})+(,\d+)?$|^-?\d+(,\d+)?$|^-?\d+\.\d+$/.test(s)) return NaN;
    if (s.indexOf(',') > -1) s = s.replace(/\./g, '').replace(',', '.');
    else if (/^-?\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
    return parseFloat(s);
  }
  function initTables(root) {
    qsa('table.tuda-table', root).forEach(function (table) {
      if (!once(table, 'Table')) return;
      var tbody = table.tBodies[0];
      qsa('th .tuda-th-sort', table).forEach(function (b) {
        b.addEventListener('click', function () {
          var th = b.closest('th'), idx = Array.prototype.indexOf.call(th.parentNode.children, th);
          var dir = th.getAttribute('aria-sort') === 'ascending' ? 'descending' : 'ascending';
          qsa('th[aria-sort]', table).forEach(function (o) { if (o !== th) o.setAttribute('aria-sort', 'none'); var ic = o.querySelector('svg[data-icon]'); if (ic && o !== th) { ic.setAttribute('data-icon', 'sort'); } });
          th.setAttribute('aria-sort', dir);
          var ic = b.querySelector('svg[data-icon]'); if (ic) ic.setAttribute('data-icon', dir === 'ascending' ? 'arrow-up' : 'arrow-down');
          hydrateIcons(table);
          var rows = Array.prototype.slice.call(tbody.rows);
          rows.sort(function (r1, r2) {
            var a = r1.cells[idx], c = r2.cells[idx];
            var va = a.getAttribute('data-sort') || a.textContent.trim(), vb = c.getAttribute('data-sort') || c.textContent.trim();
            var na = num(va), nb = num(vb);
            var r = (!isNaN(na) && !isNaN(nb)) ? na - nb : va.localeCompare(vb, lang(table) === 'en' ? 'en' : 'de', { numeric: true, sensitivity: 'base' });
            return dir === 'ascending' ? r : -r;
          });
          rows.forEach(function (r) { tbody.appendChild(r); });
          announce(T[lang(table)].sorted(b.textContent.trim(), dir));
        });
      });
      var all = table.querySelector('[data-tuda-select-all]');
      if (all) {
        var boxes = function () { return qsa('tbody input[type="checkbox"]', table); };
        var bar = table.closest('.tuda-table-wrap') && table.closest('.tuda-table-wrap').querySelector('.tuda-table__toolbar');
        var sync = function () {
          var b = boxes(), n = b.filter(function (x) { return x.checked; }).length;
          all.checked = n === b.length && n > 0; all.indeterminate = n > 0 && n < b.length;
          b.forEach(function (x) { x.closest('tr').setAttribute('aria-selected', x.checked ? 'true' : 'false'); });
          if (bar) {
            bar.classList.toggle('is-selection', n > 0);
            var c = bar.querySelector('[data-tuda-selection-count]'); if (c) c.textContent = T[lang(table)].selected(n);
          }
        };
        all.addEventListener('change', function () { boxes().forEach(function (x) { x.checked = all.checked; }); sync(); });
        tbody.addEventListener('change', function (e) { if (e.target.matches('input[type="checkbox"]')) sync(); });
        sync();
      }
    });
  }

  /* ------------------------------------------------------------ Formular-Validierung mit Fehlerübersicht */
  function initForms(root) {
    qsa('form[data-tuda-validate]', root).forEach(function (form) {
      if (!once(form, 'Form')) return;
      form.setAttribute('novalidate', '');
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var errors = [];
        qsa('[required]', form).forEach(function (f) {
          var field = f.closest('.tuda-field, .tuda-fieldset');
          var msgEl = field && field.querySelector('.tuda-error');
          var bad = f.type === 'checkbox' ? !f.checked : (f.type === 'radio' ? !form.querySelector('input[name="' + f.name + '"]:checked') : !f.value.trim() || (f.pattern && !new RegExp('^(?:' + f.pattern + ')$').test(f.value)));
          if (bad) {
            if (errors.some(function (x) { return x.name && x.name === f.name; })) return;
            var msg = f.getAttribute('data-error') || (lang(form) === 'en' ? 'Please fill in this field.' : 'Bitte fülle dieses Feld aus.');
            errors.push({ id: f.id, name: f.name, msg: msg });
            f.setAttribute('aria-invalid', 'true');
            if (msgEl) { msgEl.hidden = false; msgEl.querySelector('span').textContent = msg; }
          } else {
            f.removeAttribute('aria-invalid');
            if (msgEl) msgEl.hidden = true;
          }
        });
        var sum = form.querySelector('[data-tuda-error-summary]');
        if (errors.length) {
          if (sum) {
            var en = lang(form) === 'en';
            sum.hidden = false;
            sum.innerHTML = icon('alert-octagon') + '<div class="tuda-alert__content"><h2 class="tuda-alert__title">' + (en ? 'Please check ' + errors.length + (errors.length === 1 ? ' field' : ' fields') : (errors.length === 1 ? 'Bitte prüfe 1 Angabe' : 'Bitte prüfe ' + errors.length + ' Angaben')) + '</h2><ul class="tuda-alert__text" style="margin:0;padding-left:1.2em">' +
              errors.map(function (x) { return '<li><a class="tuda-link" href="#' + x.id + '">' + esc(x.msg) + '</a></li>'; }).join('') + '</ul></div>';
            sum.focus();
            qsa('a', sum).forEach(function (a) { a.addEventListener('click', function (ev) { ev.preventDefault(); var t = doc.getElementById(a.getAttribute('href').slice(1)); if (t) t.focus(); }); });
          }
        } else {
          if (sum) sum.hidden = true;
          form.dispatchEvent(new CustomEvent('tuda:valid', { bubbles: true }));
        }
      });
    });
  }

  /* ------------------------------------------------------------ Init */
  function init(root) {
    root = root || doc;
    hydrateIcons(root);
    initThemeControls(root); initTabs(root); initModals(root); initToastTriggers(root); initTooltips(root);
    initMenus(root); initDatepickers(root); initComboboxes(root); initShell(root); initMisc(root); initTables(root); initForms(root);
    return root;
  }

  var api = {
    version: '0.1.0', icons: ICONS, icon: icon, init: init, hydrateIcons: hydrateIcons,
    theme: theme, modal: modal, toast: toast, combobox: combobox, announce: announce,
    format: { date: fmt, parseDate: parseDate, isoWeek: isoWeek }
  };
  window.TUDa = Object.assign(window.TUDa || {}, api);
  if (!doc.documentElement.hasAttribute('data-theme')) theme.restore();
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', function () { init(doc); });
  else init(doc);
})();
