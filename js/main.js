/* =============================================================
   MAISON AMIRA — interactions
   Vanilla JS, no dependencies. All motion respects reduced-motion.
============================================================= */
(function () {
  "use strict";

  // Signals to CSS that JS is active (reveal elements start hidden only when true,
  // so content is never invisible if scripts fail to load).
  document.documentElement.classList.add("js");

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Loader ---------- */
  var loader = document.getElementById("loader");
  function dismissLoader() {
    if (!loader || loader.classList.contains("is-done")) return;
    loader.classList.add("is-done");
    document.body.classList.add("hero-ready"); // cue the hero entrance as the loader lifts
    document.body.style.overflow = "";
    window.setTimeout(function () { if (loader) loader.remove(); }, 1000);
  }
  // Lock scroll while the intro plays
  document.body.style.overflow = "hidden";
  var minShow = reduceMotion ? 300 : 2100;   // let the logo animation breathe
  var start = performance.now();
  window.addEventListener("load", function () {
    var elapsed = performance.now() - start;
    window.setTimeout(dismissLoader, Math.max(0, minShow - elapsed));
  });
  // Safety net: never trap the user if `load` is slow
  window.setTimeout(dismissLoader, 4500);

  /* ---------- Footer year ---------- */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- Nav: condense on scroll ---------- */
  var nav = document.getElementById("nav");
  function onScrollNav() {
    if (window.scrollY > 40) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  }
  onScrollNav();

  /* ---------- Mobile menu ---------- */
  var toggle = document.getElementById("navToggle");
  var mobileMenu = document.getElementById("mobileMenu");
  function closeMenu() {
    document.body.classList.remove("menu-open");
    toggle.setAttribute("aria-expanded", "false");
    mobileMenu.setAttribute("aria-hidden", "true");
  }
  function openMenu() {
    document.body.classList.add("menu-open");
    toggle.setAttribute("aria-expanded", "true");
    mobileMenu.setAttribute("aria-hidden", "false");
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      if (document.body.classList.contains("menu-open")) closeMenu();
      else openMenu();
    });
  }
  if (mobileMenu) {
    mobileMenu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", closeMenu);
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeMenu(); closeLightbox(); }
  });

  /* ---------- Scroll reveals ---------- */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));

  // Reveal any element that has entered (or nearly entered) the viewport.
  // Used as a failsafe so content is guaranteed to appear even if
  // IntersectionObserver never fires (e.g. non-compositing environments).
  function revealInView() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    for (var i = reveals.length - 1; i >= 0; i--) {
      var el = reveals[i];
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0) {
        el.classList.add("in-view");
        reveals.splice(i, 1); // reveal once, then stop tracking
      }
    }
  }

  if (reduceMotion) {
    reveals.forEach(function (el) { el.classList.add("in-view"); });
    reveals.length = 0;
  } else {
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            io.unobserve(entry.target);
            var idx = reveals.indexOf(entry.target);
            if (idx > -1) reveals.splice(idx, 1);
          }
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
      reveals.slice().forEach(function (el) { io.observe(el); });
    }
    // Failsafe layer: works with or without a live IntersectionObserver.
    revealInView();
    window.addEventListener("scroll", revealInView, { passive: true });
    window.addEventListener("resize", revealInView);
    window.addEventListener("load", revealInView);
  }

  /* ---------- Scrollspy: highlight active nav link ---------- */
  var sections = ["story", "menu", "gallery", "visit"].map(function (id) {
    return document.getElementById(id);
  }).filter(Boolean);
  var navLinks = Array.prototype.slice.call(
    document.querySelectorAll('.nav__links a[href^="#"]')
  );
  function setActive(id) {
    navLinks.forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === "#" + id);
    });
  }
  if ("IntersectionObserver" in window && sections.length) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach(function (s) { spy.observe(s); });
  }

  /* ---------- Hero parallax (rAF-throttled) ---------- */
  var parallaxEls = Array.prototype.slice.call(document.querySelectorAll("[data-parallax]"));
  var ticking = false;
  function applyParallax() {
    var y = window.scrollY;
    parallaxEls.forEach(function (el) {
      var speed = parseFloat(el.getAttribute("data-parallax")) || 0;
      el.style.transform = "translate3d(0," + (y * speed) + "px,0)";
    });
    ticking = false;
  }
  function onScroll() {
    onScrollNav();
    if (reduceMotion) return;
    if (!ticking) {
      window.requestAnimationFrame(applyParallax);
      ticking = true;
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });

  /* ---------- Lightbox ---------- */
  var lightbox = document.getElementById("lightbox");
  var lightboxImg = document.getElementById("lightboxImg");
  var lightboxClose = document.getElementById("lightboxClose");
  var lastFocused = null;

  function openLightbox(src, alt) {
    if (!lightbox) return;
    lastFocused = document.activeElement;
    lightboxImg.src = src;
    lightboxImg.alt = alt || "";
    lightbox.classList.add("open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";
    lightboxClose.focus();
  }
  function closeLightbox() {
    if (!lightbox || !lightbox.classList.contains("open")) return;
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.style.overflow = "";
    window.setTimeout(function () { lightboxImg.src = ""; }, 400);
    if (lastFocused) lastFocused.focus();
  }
  document.querySelectorAll(".gcard").forEach(function (card) {
    var full = card.getAttribute("data-src");
    var img = card.querySelector("img");
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", "View " + (img ? img.alt : "image"));
    function go() { openLightbox(full, img ? img.alt : ""); }
    card.addEventListener("click", go);
    card.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); }
    });
  });
  if (lightboxClose) lightboxClose.addEventListener("click", closeLightbox);
  if (lightbox) lightbox.addEventListener("click", function (e) {
    if (e.target === lightbox) closeLightbox();
  });

  /* ---------- Smooth anchor offset for fixed nav ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      var id = a.getAttribute("href");
      if (id === "#" || id === "#top") return;
      var target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      var top = target.getBoundingClientRect().top + window.scrollY - 70;
      window.scrollTo({ top: top, behavior: reduceMotion ? "auto" : "smooth" });
    });
  });

  /* ---------- Refined cursor interactions ---------- */
  // Only on devices with a precise pointer, and never when reduced motion is requested.
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  if (finePointer && !reduceMotion) initCursor();

  function initCursor() {
    var cursor = document.getElementById("cursor");
    var dot = document.getElementById("cursorDot");
    var label = cursor && cursor.querySelector(".cursor__label");
    if (!cursor || !dot) return;

    document.body.classList.add("has-cursor");

    var tx = window.innerWidth / 2, ty = window.innerHeight / 2;
    var rx = tx, ry = ty, shown = false;

    function reveal() {
      if (shown) return;
      shown = true;
      cursor.classList.add("is-visible");
      dot.classList.add("is-visible");
    }

    window.addEventListener("mousemove", function (e) {
      tx = e.clientX; ty = e.clientY;
      dot.style.transform = "translate(" + tx + "px," + ty + "px)";
      reveal();
    }, { passive: true });

    document.addEventListener("mouseleave", function () {
      shown = false;
      cursor.classList.remove("is-visible");
      dot.classList.remove("is-visible");
    });

    // Contextual states, recomputed as the pointer crosses elements.
    document.addEventListener("mouseover", function (e) {
      var t = e.target;
      if (!t || !t.closest) return;
      var gcard = t.closest(".gcard");
      var interactive = t.closest("a, button");
      var dark = t.closest('[data-cursor="dark"]');
      cursor.classList.toggle("is-view", !!gcard);
      cursor.classList.toggle("is-active", !!interactive && !gcard);
      dot.classList.toggle("is-hidden", !!interactive || !!gcard);
      cursor.classList.toggle("is-dark", !!dark);
      dot.classList.toggle("is-dark", !!dark);
      if (gcard && label) label.textContent = "View";
    }, { passive: true });

    // Ring trails the pointer with easing; dot tracks exactly.
    (function loop() {
      rx += (tx - rx) * 0.18;
      ry += (ty - ry) * 0.18;
      cursor.style.transform = "translate(" + rx + "px," + ry + "px)";
      window.requestAnimationFrame(loop);
    })();

    // Magnetic pull toward the cursor.
    function magnetic(el, strength) {
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var mx = e.clientX - (r.left + r.width / 2);
        var my = e.clientY - (r.top + r.height / 2);
        el.style.transform = "translate(" + (mx * strength) + "px," + (my * strength) + "px)";
      });
      el.addEventListener("mouseleave", function () { el.style.transform = ""; });
    }
    document.querySelectorAll(".btn").forEach(function (b) { magnetic(b, 0.22); });
    document.querySelectorAll(".footer__social a").forEach(function (b) { magnetic(b, 0.34); });

    // Subtle tilt toward the cursor.
    function tilt(el, maxDeg, lift) {
      el.addEventListener("mouseenter", function () { el.style.transition = "transform .2s ease-out"; });
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        el.style.transform =
          "perspective(900px) rotateX(" + (-py * maxDeg).toFixed(2) + "deg) rotateY(" +
          (px * maxDeg).toFixed(2) + "deg) translateY(" + lift + "px)";
      });
      el.addEventListener("mouseleave", function () {
        el.style.transition = "transform .6s cubic-bezier(.16,1,.3,1)";
        el.style.transform = "";
      });
    }
    document.querySelectorAll(".feat").forEach(function (c) { tilt(c, 5, -6); });
    document.querySelectorAll(".gcard").forEach(function (c) { tilt(c, 4, -4); });
    var storyFrame = document.querySelector(".story__media .img-frame");
    if (storyFrame) tilt(storyFrame, 4, 0);
  }
})();
