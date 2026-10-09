// Vercel Routing Middleware: PIN gate for the whole site (page + data.json).
// The PIN lives in the project env var DASHBOARD_PIN, never in this file.
// A correct PIN sets an HttpOnly cookie holding SHA-256(salt + PIN) for 30 days;
// changing DASHBOARD_PIN invalidates every existing cookie.

export const config = {
  // logo.jpg stays public so the PIN screen can show it.
  matcher: ['/((?!logo\\.jpg$|favicon\\.ico$).*)'],
};

const COOKIE = 'ts_pin';
const SALT = 'toyota-sasa-ads:v1:';
const MAX_AGE = 60 * 60 * 24 * 30;

async function sha256(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function readCookie(request, name) {
  const raw = request.headers.get('cookie') || '';
  for (const part of raw.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === name) return v.join('=');
  }
  return null;
}

function equal(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function page(error) {
  const msg = error ? '<p class="err">PIN ไม่ถูกต้อง ลองใหม่อีกครั้ง</p>' : '';
  return `<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Toyota Sasa — Ads Performance</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;
background:#f4f4f1;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#111}
.card{width:min(92vw,360px);background:#fff;border:1px solid #e1e1dc;border-top:4px solid #E3000F;border-radius:10px;padding:28px 24px;text-align:center}
.brand{background:#DDDDD5;border-radius:8px;padding:12px;margin-bottom:18px}.brand img{height:56px}
h1{font-size:18px;margin:0 0 4px;letter-spacing:.04em;text-transform:uppercase}p{margin:0 0 16px;color:#5f6368;font-size:14px}
input{width:100%;font-size:28px;letter-spacing:.5em;text-align:center;padding:10px;border:1px solid #c9c9c4;border-radius:8px;outline:none}
input:focus{border-color:#E3000F;box-shadow:0 0 0 3px rgba(227,0,15,.15)}
button{margin-top:14px;width:100%;padding:12px;font-size:15px;font-weight:600;color:#fff;background:#E3000F;border:0;border-radius:8px;cursor:pointer}
.err{color:#c4161c;margin:10px 0 0}
@media (prefers-color-scheme:dark){body{background:#141414;color:#ececec}.card{background:#1e1e1e;border-color:#333}p{color:#a3a3a3}
input{background:#141414;color:#ececec;border-color:#444}}
</style></head><body>
<form class="card" method="post" action="/__pin">
<div class="brand"><img src="/logo.jpg" alt="Toyota Sasa"></div>
<h1>Ads Performance</h1><p>กรอก PIN เพื่อเข้าดู dashboard</p>
<input name="pin" type="password" inputmode="numeric" autocomplete="current-password" maxlength="12" required autofocus aria-label="PIN">
<button type="submit">เข้าสู่ระบบ</button>${msg}
</form></body></html>`;
}

const html = (body, status) =>
  new Response(body, {
    status,
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'no-store',
      'x-robots-tag': 'noindex, nofollow',
    },
  });

export default async function middleware(request) {
  const pin = process.env.DASHBOARD_PIN;
  if (!pin) return html('<h1>Dashboard PIN is not configured.</h1>', 503);

  const expected = await sha256(SALT + pin);
  const url = new URL(request.url);

  if (url.pathname === '/__pin' && request.method === 'POST') {
    let given = '';
    try {
      const form = await request.formData();
      given = String(form.get('pin') || '').trim();
    } catch (_) {}
    if (equal(await sha256(SALT + given), expected)) {
      return new Response(null, {
        status: 303,
        headers: {
          location: '/',
          'cache-control': 'no-store',
          'set-cookie': `${COOKIE}=${expected}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    await new Promise((r) => setTimeout(r, 800)); // slow down guessing
    return html(page(true), 401);
  }

  if (equal(readCookie(request, COOKIE), expected)) {
    return new Response(null, { headers: { 'x-middleware-next': '1' } }); // continue to the site
  }
  return html(page(false), 401);
}
