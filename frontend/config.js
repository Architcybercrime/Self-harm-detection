/* ============================================================
   config.js  —  Single source of truth for the backend API URL.

   LOCAL DEV:    leave as-is, points to http://127.0.0.1:8000
   PRODUCTION:   set the env var VITE_API_URL (or just edit the
                 fallback string below to your Render service URL,
                 e.g. 'https://safesignal-api.onrender.com')

   All HTML files load this script first so they all share the
   same API_BASE constant.
   ============================================================ */

/* Root URL — no trailing slash, no /api suffix */
const _API_ROOT = (
  (typeof __VITE_API_URL__ !== 'undefined' && __VITE_API_URL__)
  || 'https://safesignal-api-prod.onrender.com'
);

/* API_BASE includes /api — used by analysis.js, camera.js and dashboard.html */
const API_BASE = _API_ROOT + '/api';
