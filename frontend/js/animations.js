/* ============================================================
   js/animations.js
   Sections 1-9: GSAP animations, cursor, progress bar, hero,
   red blocks, dark chapter, parallax, floating cards, scroll reveal.
   ============================================================ */

/* ══════════════════════════════════════════════════════════
   1. SETUP — register GSAP plugin
   ══════════════════════════════════════════════════════════ */
gsap.registerPlugin(ScrollTrigger);


/* ══════════════════════════════════════════════════════════
   2. CUSTOM CURSOR
   The browser's default cursor is hidden (cursor:none in CSS).
   We move this div to the mouse position on every mousemove.
   mix-blend-mode:difference inverts the cursor colour so it
   remains visible on any background.
   ══════════════════════════════════════════════════════════ */
const cursor = document.getElementById('cursor');

document.addEventListener('mousemove', e => {
  cursor.style.left = e.clientX + 'px';
  cursor.style.top  = e.clientY + 'px';
});

// Grow the cursor when hovering interactive elements
const interactiveEls = 'a, button, .bio-tab, .footer-link, .social-icon, .nav-chapters, .nav-menu';
document.querySelectorAll(interactiveEls).forEach(el => {
  el.addEventListener('mouseenter', () => cursor.classList.add('big'));
  el.addEventListener('mouseleave', () => cursor.classList.remove('big'));
});


/* ══════════════════════════════════════════════════════════
   3. PROGRESS BAR
   The thin red line at the top. self.progress goes 0→1 as
   the user scrolls from top to bottom.
   ══════════════════════════════════════════════════════════ */
ScrollTrigger.create({
  trigger: document.body,
  start: 'top top',
  end: 'bottom bottom',
  onUpdate: self => {
    document.getElementById('progress').style.width =
      (self.progress * 100) + '%';
  }
});


/* ══════════════════════════════════════════════════════════
   4. HERO ANIMATIONS

   4a. Entrance — title fades up from below on page load.
   4b. Scroll fade — gradient overlay fades in and title fades
       out as the user scrolls; scrub reverses on scroll up.
   ══════════════════════════════════════════════════════════ */

// 4a: Entrance animation — plays once on page load
gsap.from('#heroTitle', {
  y: 80,
  opacity: 0,
  duration: 1.4,
  ease: 'power4.out',
  delay: 0.3
});

// 4b: Gradient overlay fades in while scrolling through hero
gsap.to('#heroOverlay', {
  opacity: 1,
  scrollTrigger: {
    trigger: '#hero',
    start: 'top top',
    end: 'bottom top',
    scrub: true
  }
});

// 4b: Title fades out going down, comes BACK when scrolling up
gsap.to('#heroTitle', {
  opacity: 0,
  y: -60,
  scrollTrigger: {
    trigger: '#hero',
    start: '20% top',
    end: 'bottom top',
    scrub: true,
    onLeaveBack: () => {
      gsap.set('#heroTitle', { clearProps: 'opacity,y' });
    }
  }
});


/* ══════════════════════════════════════════════════════════
   5. RED RECTANGLES — CLIP-PATH WIPE
   Fired by the horizontal scroll trigger in section 12
   when panel 2 becomes visible.
   ══════════════════════════════════════════════════════════ */
/* (Animations fired programmatically from horizontal scroll group 1) */


/* ══════════════════════════════════════════════════════════
   6. DARK CHAPTER TITLE — SLIDE IN FROM LEFT
   ══════════════════════════════════════════════════════════ */
gsap.from('#darkTitle', {
  x: -100,
  opacity: 0,
  duration: 1.2,
  ease: 'power4.out',
  scrollTrigger: {
    trigger: '.dark-chapter',
    start: 'top 60%',
    toggleActions: 'play none none none'
  }
});


/* ══════════════════════════════════════════════════════════
   7. PHOTO PARALLAX
   Different elements move at different speeds to create depth.
   ══════════════════════════════════════════════════════════ */
gsap.to('.photo-card-1', {
  y: -60,
  ease: 'none',
  scrollTrigger: {
    trigger: '.photo-grid-section',
    start: 'top bottom',
    end: 'bottom top',
    scrub: 1
  }
});

gsap.to('.photo-card-2', {
  y: -120,
  ease: 'none',
  scrollTrigger: {
    trigger: '.photo-grid-section',
    start: 'top bottom',
    end: 'bottom top',
    scrub: 1.5
  }
});


/* ══════════════════════════════════════════════════════════
   8. FLOATING PHOTO CARDS
   stagger: 0.2 means each card starts 0.2 s after the previous.
   ══════════════════════════════════════════════════════════ */
gsap.from('.float-card', {
  y: 80,
  opacity: 0,
  duration: 1,
  stagger: 0.2,
  ease: 'power3.out',
  scrollTrigger: {
    trigger: '.racenight-section',
    start: 'top 60%',
    toggleActions: 'play none none none'
  }
});


/* ══════════════════════════════════════════════════════════
   9. SCROLL REVEAL — IntersectionObserver
   Elements with .reveal / .reveal-left start hidden (CSS).
   When ≥12% visible, class .in is added → CSS transitions in.
   ══════════════════════════════════════════════════════════ */
const revealObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal, .reveal-left').forEach(el => {
  revealObserver.observe(el);
});
