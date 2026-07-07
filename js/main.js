/* Modern site JS — vanilla, no jQuery */
(function () {
  'use strict';

  /* ── Navbar scroll effect ── */
  var nav = document.querySelector('.nav');
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle('nav--scrolled', window.scrollY > 60);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── Mobile menu toggle ── */
  var toggle = document.querySelector('.nav__toggle');
  var links = document.querySelector('.nav__links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      toggle.classList.toggle('active');
      links.classList.toggle('open');
    });
    // Close menu when a link is clicked
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        toggle.classList.remove('active');
        links.classList.remove('open');
      });
    });
  }

  /* ── Smooth scroll for anchor links ── */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        var offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-height')) || 72;
        window.scrollTo({
          top: target.offsetTop - offset,
          behavior: 'smooth'
        });
      }
    });
  });

  /* ── Fade-in on scroll (Intersection Observer) ── */
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.fade-in').forEach(function (el) {
      observer.observe(el);
    });
  } else {
    // Fallback: show everything immediately
    document.querySelectorAll('.fade-in').forEach(function (el) {
      el.classList.add('visible');
    });
  }

  /* ── Contact form ──
     The form submits with a native POST (no fetch / preventDefault) so Formspree
     can serve its reCAPTCHA challenge; on success Formspree redirects to the
     thank-you page named in the form's hidden _next field. Kept JS-free on
     purpose — no Google reCAPTCHA scripts ever load on this domain. */
})();
