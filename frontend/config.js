/* ============================================================
   config.js  —  Single source of truth for the backend API URL.

   LOCAL DEV:    leave as-is, points to http://127.0.0.1:8000
   PRODUCTION:   set the env var VITE_API_URL (or just edit the
                 fallback string below to your Render service URL,
                 e.g. 'https://safesignal-api.onrender.com')

   All HTML files load this script first so they all share the
   same API_BASE constant.
   ============================================================ */

const API_BASE = (
  // Injected by Vercel build step if VITE_API_URL env var is set
  (typeof __VITE_API_URL__ !== 'undefined' && __VITE_API_URL__)
  || 'http://127.0.0.1:8000'   // ← replace with your Render URL for production
);
