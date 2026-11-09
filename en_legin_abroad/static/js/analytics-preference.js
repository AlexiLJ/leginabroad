(function () {
  'use strict';

  const preferenceKey = 'leginabroad.analytics';
  const measurementId = document.currentScript.dataset.measurementId;
  const controls = document.getElementById('analytics-preference');
  const status = document.getElementById('analytics-status');
  let preference;

  try {
    preference = localStorage.getItem(preferenceKey);
  } catch {
    if (status) status.textContent = 'This browser cannot store an analytics preference. Analytics is off.';
    return;
  }

  if (controls) {
    controls.hidden = false;
    status.textContent = preference === 'enabled' ? 'Analytics is on.' : 'Analytics is off.';
    for (const button of controls.querySelectorAll('[data-analytics-choice]')) {
      button.addEventListener('click', () => {
        try {
          localStorage.setItem(preferenceKey, button.dataset.analyticsChoice);
        } catch {
          status.textContent = 'This browser could not save your choice. You can clear site data in your browser settings.';
          return;
        }
        window['ga-disable-' + measurementId] = button.dataset.analyticsChoice !== 'enabled';
        window.location.reload();
      });
    }
  }

  if (controls || preference !== 'enabled') return;

  window.addEventListener('storage', event => {
    if (event.key === preferenceKey || event.key === null) {
      window['ga-disable-' + measurementId] = event.newValue !== 'enabled';
    }
  });
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', measurementId, {
    allow_google_signals: false,
    allow_ad_personalization_signals: false,
    page_location: document.querySelector('link[rel="canonical"]').href,
    page_referrer: document.referrer.split(/[?#]/, 1)[0],
  });

  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
  document.head.append(script);
}());
