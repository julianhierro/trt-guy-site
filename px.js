/* TRT Guy — Meta Pixel.
   One file for the whole site, so there is exactly one pixel everywhere and every
   page builds the same identity signals. Pages load it once in the <head>.

   Every conversion is sent twice on purpose: once from the browser (fast, but
   ad blockers and iPhones eat 20-40% of it) and once from the Cloudflare Worker,
   which Meta cannot be stopped from receiving. Both carry the same event_id, so
   Meta counts the conversion once and merges what each one knows. */
(function () {
  var PIXEL_ID = '1112141834609992';
  var CAPI     = 'https://trt-guy-onboarding.julianhierro.workers.dev/capi';

  // Meta's own list. Anything not on it has to go through trackCustom instead.
  var STANDARD = ['PageView','ViewContent','Lead','Schedule','SubmitApplication','Purchase',
                  'CompleteRegistration','Contact','InitiateCheckout','Subscribe','StartTrial','Search'];

  function cookie(name) {
    var m = ('; ' + document.cookie).split('; ' + name + '=');
    return m.length === 2 ? m.pop().split(';').shift() : null;
  }
  function setCookie(name, value, days) {
    try {
      document.cookie = name + '=' + value + '; max-age=' + (days * 86400) +
                        '; path=/; samesite=lax' + (location.protocol === 'https:' ? '; secure' : '');
    } catch (e) {}
  }
  function uuid() {
    try { if (crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (e) {}
    return 'e-' + Date.now() + '-' + Math.random().toString(36).slice(2);
  }

  /* _fbc is the click that brought them here — the single most valuable signal on
     paid traffic. The pixel writes it from ?fbclid= on its own, but not when it is
     blocked or loads late, so write it ourselves the moment the page opens. */
  (function captureClickId() {
    var m = /[?&]fbclid=([^&]+)/.exec(location.search);
    if (m && !cookie('_fbc')) setCookie('_fbc', 'fb.1.' + Date.now() + '.' + decodeURIComponent(m[1]), 90);
  })();

  /* A stable id for this browser so Meta can join today's anonymous read of the
     guide to the email the same person hands over next week. */
  function externalId() {
    var v = cookie('_tg_xid');
    if (!v) { v = uuid(); setCookie('_tg_xid', v, 365); }
    return v;
  }

  /* Once someone opts in we keep their email in a first-party cookie and attach it
     to every later event. That is what lifts match quality on the pages where they
     never type anything — the guide, the coaching page, the application. */
  function knownEmail() {
    try { return decodeURIComponent(cookie('_tg_em') || '') || null; } catch (e) { return null; }
  }
  function remember(email) {
    if (email) setCookie('_tg_em', encodeURIComponent(String(email).trim().toLowerCase()), 365);
  }

  // ---- Meta base code -------------------------------------------------------
  !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
  n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');

  var init = { external_id: externalId() };
  var em = knownEmail(); if (em) init.em = em;      // the pixel hashes this itself
  fbq('init', PIXEL_ID, init);
  fbq('track', 'PageView');

  /* Fire one conversion down both paths.
     `person` is whatever we actually know: {email, phone, firstName}. Nothing is
     invented — a field we do not have is simply left out. */
  function track(name, params, person) {
    var id = uuid();
    person = person || {};
    if (person.email) remember(person.email);

    var mail = person.email || knownEmail();
    var match = { eventID: id, external_id: externalId() };
    if (mail) match.em = mail;
    if (person.phone) match.ph = person.phone;
    if (person.firstName) match.fn = person.firstName;

    try {
      fbq(STANDARD.indexOf(name) === -1 ? 'trackCustom' : 'track', name, params || {}, match);
    } catch (e) {}

    // The server copy. Keepalive so it still goes out while the page is navigating
    // away — which is exactly what happens on every one of our conversions.
    try {
      fetch(CAPI, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
        body: JSON.stringify({
          event: name,
          event_id: id,
          source_url: location.href,
          email: mail || undefined,
          phone: person.phone || undefined,
          first_name: person.firstName || undefined,
          external_id: externalId(),
          fbp: cookie('_fbp') || undefined,
          fbc: cookie('_fbc') || undefined,
          custom: params || {}
        })
      }).catch(function () {});
    } catch (e) {}

    return id;
  }

  window.tgPx = { track: track, remember: remember, knownEmail: knownEmail };
})();
