# Custom Domain Setup Guide

## Step 1 — Buy a domain
Recommended registrars (cheapest to most):
- **Namecheap**: ~₹800/yr for .com, ~₹500/yr for .in
- **GoDaddy**: similar pricing
- Suggested names: `safesignal.in`, `safesignal.co.in`, `safesignalai.com`

## Step 2 — Add domain to Vercel (frontend)
Run this command (replace with your domain):
```bash
vercel domains add yourdomain.com --cwd frontend
```

Then in your domain registrar's DNS settings, add:
| Type  | Name | Value                        |
|-------|------|------------------------------|
| CNAME | www  | cname.vercel-dns.com         |
| A     | @    | 76.76.21.21                  |

## Step 3 — Add domain to Render (backend API)
In Render dashboard → safesignal-api → Settings → Custom Domains:
- Add: `api.yourdomain.com`
- Then in DNS add:
  | Type  | Name | Value                              |
  |-------|------|------------------------------------|
  | CNAME | api  | safesignal-api.onrender.com        |

## Step 4 — Update config.js
After adding the API subdomain, update frontend/config.js:
```js
|| 'https://api.yourdomain.com'
```

## Step 5 — Update CORS on Render
In Render env vars, update:
```
ALLOWED_ORIGINS = https://yourdomain.com,https://www.yourdomain.com
```

Tell Claude your domain name and it will run Steps 2 and 4 automatically.
