// Vercel Serverless Function: Autentikasi akun (Daftar & Masuk) dengan database cloud permanen
// Endpoint: POST /api/auth   body: { action: 'register' | 'login' | 'status', ... }
//
// Penyimpanan : Redis (Upstash / Vercel KV) lewat REST API.
//   Env yang dibaca (salah satu pasangan):
//     KV_REST_API_URL + KV_REST_API_TOKEN            (Vercel Marketplace -> Upstash Redis / KV)
//     UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN
//   Env opsional: ADMIN_PASSWORD (default lama 'sppgunggul' dipertahankan agar tidak memutus akses)
// Keamanan    : password di-hash scrypt + salt acak, perbandingan timing-safe,
//               pendaftaran atomik (HSETNX) agar akun tidak saling menimpa, rate limit per IP,
//               role pendaftar selalu 'Employee' (tidak bisa mendaftar sebagai Admin),
//               password tidak pernah dikirim kembali ke browser.

import { scryptSync, randomBytes, timingSafeEqual } from 'crypto';

const REDIS_URL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL || '';
const REDIS_TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN || '';

const USERS_KEY = 'mbg:users';   // hash: id -> JSON akun (password ter-hash)
const INDEX_KEY = 'mbg:ids';     // hash: NIK / username (ternormalisasi) -> id akun

const MAX_ATTEMPTS = 25;         // percobaan login/daftar per IP
const WINDOW_SEC = 600;          // per 10 menit

// Akun bawaan lama (dipertahankan agar tidak ada yang terkunci). Hanya dipakai saat migrasi/login.
const LEGACY_SEED = [
    { nik: '12345', username: 'demo', name: 'Siswa / Karyawan Demo', password: 'sppg123', role: 'Employee' },
    { nik: '2304111010099', username: 'dliyaul', name: 'Dliyaul Haq', password: 'password123', role: 'Employee' },
    { nik: '2304111010006', username: 'siti', name: 'Siti Nurmasyitah', password: 'sppg123', role: 'Employee' },
    { nik: '123456789', username: 'fathin', name: 'fathin', password: '12345678', role: 'Employee' },
    { nik: '10021', username: 'ahmad', name: 'Ahmad Fauzi', password: 'sppg123', role: 'Employee' },
    { nik: '10045', username: 'rahma', name: 'Siti Rahma', password: 'sppg123', role: 'Employee' },
    { nik: '300666', username: 'yaka', name: 'yaka', password: 'terserah', role: 'Employee' }
];
const LEGACY_CLOUD_URL = 'https://api.restful-api.dev/objects/ff808181a09d98f701a0ce45868a7b64';

// ---------- Helper ----------
function configured() { return !!(REDIS_URL && REDIS_TOKEN); }

async function redis(...cmd) {
    const r = await fetch(REDIS_URL, {
        method: 'POST',
        headers: { Authorization: `Bearer ${REDIS_TOKEN}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(cmd)
    });
    const data = await r.json();
    if (!r.ok || data.error) throw new Error(data.error || `Redis HTTP ${r.status}`);
    return data.result;
}

function clean(str, max = 120) {
    if (typeof str !== 'string') return '';
    return str.replace(/<[^>]*>?/gm, '').replace(/[\u0000-\u001f]/g, '').trim().slice(0, max);
}

function norm(str) { return String(str || '').trim().toLowerCase().replace(/\s+/g, ''); }

function deriveUsername(nik, name) {
    if (/^\d+$/.test(nik) && name) return norm(name);
    return norm(nik);
}

function hashPassword(password) {
    const salt = randomBytes(16);
    const hash = scryptSync(password, salt, 64);
    return `scrypt$${salt.toString('hex')}$${hash.toString('hex')}`;
}

function verifyPassword(password, stored) {
    try {
        const [scheme, saltHex, hashHex] = String(stored).split('$');
        if (scheme !== 'scrypt') return false;
        const expected = Buffer.from(hashHex, 'hex');
        const actual = scryptSync(password, Buffer.from(saltHex, 'hex'), expected.length);
        return timingSafeEqual(actual, expected);
    } catch (e) { return false; }
}

function publicUser(u) {
    return { nik: u.nik, username: u.username, name: u.name, role: u.role || 'Employee' };
}

function clientIp(req) {
    const xf = req.headers['x-forwarded-for'];
    return (xf ? String(xf).split(',')[0] : (req.socket && req.socket.remoteAddress) || 'unknown').trim();
}

async function rateLimited(req) {
    try {
        const key = `mbg:rl:${clientIp(req)}`;
        const n = await redis('INCR', key);
        if (n === 1) await redis('EXPIRE', key, WINDOW_SEC);
        return n > MAX_ATTEMPTS;
    } catch (e) { return false; }
}

async function findUserId(identifier) {
    const key = norm(identifier);
    if (!key) return null;
    return await redis('HGET', INDEX_KEY, key);
}

async function loadUser(id) {
    const raw = await redis('HGET', USERS_KEY, id);
    return raw ? JSON.parse(raw) : null;
}

// Simpan akun baru secara atomik. Mengembalikan false jika NIK/username sudah dipakai.
async function createUser(user) {
    const id = norm(user.nik);
    const first = await redis('HSETNX', INDEX_KEY, id, id);
    if (first !== 1) return false;
    if (user.username && norm(user.username) !== id) {
        const second = await redis('HSETNX', INDEX_KEY, norm(user.username), id);
        if (second !== 1) { await redis('HDEL', INDEX_KEY, id); return false; }
    }
    await redis('HSET', USERS_KEY, id, JSON.stringify({ ...user, id }));
    return true;
}

// Cari akun di data lama (seed bawaan + cloud publik lama) lalu migrasikan ke database baru.
async function migrateLegacy(identifier, password) {
    const target = norm(identifier);
    const pools = [LEGACY_SEED];
    try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 5000);
        const r = await fetch(LEGACY_CLOUD_URL, { headers: { Accept: 'application/json' }, signal: ctrl.signal });
        clearTimeout(t);
        if (r.ok) {
            const d = await r.json();
            if (d && d.data && Array.isArray(d.data.users)) pools.push(d.data.users);
        }
    } catch (e) { /* abaikan, layanan lama boleh mati */ }

    for (const pool of pools) {
        for (const u of pool) {
            if (!u || !u.nik || !u.password) continue;
            const hit = norm(u.nik) === target || norm(u.username) === target || norm(u.name) === target;
            if (!hit || String(u.password).trim() !== password) continue;
            const name = clean(String(u.name || u.nik));
            const nik = clean(String(u.nik));
            const record = {
                nik, name, role: 'Employee',
                username: norm(u.username) || deriveUsername(nik, name),
                passwordHash: hashPassword(password),
                createdAt: new Date().toISOString(), migrated: true
            };
            await createUser(record); // jika sudah ada (race), tidak masalah
            const id = await findUserId(nik);
            return id ? await loadUser(id) : record;
        }
    }
    return null;
}

// ---------- Handler ----------
export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Cache-Control', 'no-store');

    if (req.method === 'OPTIONS') return res.status(200).end();
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const body = req.body || {};
    const action = body.action;

    if (action === 'status') {
        return res.status(200).json({ configured: configured() });
    }

    if (!configured()) {
        return res.status(503).json({
            error: 'db_not_configured',
            message: 'Database cloud belum dihubungkan di server (Upstash Redis / Vercel KV).'
        });
    }

    try {
        if (await rateLimited(req)) {
            return res.status(429).json({ error: 'rate_limited', message: 'Terlalu banyak percobaan. Coba lagi dalam 10 menit.' });
        }

        if (action === 'register') {
            const nik = clean(body.nik, 40);
            const name = clean(body.name, 80);
            const password = typeof body.password === 'string' ? body.password.trim() : '';
            if (!nik || !name || !password) {
                return res.status(400).json({ error: 'invalid', message: 'Semua kolom wajib diisi.' });
            }
            if (password.length < 6) {
                return res.status(400).json({ error: 'weak_password', message: 'Kata sandi minimal 6 karakter.' });
            }
            const reserved = ['admin', 'administrator'];
            if (reserved.includes(norm(nik)) || reserved.includes(norm(deriveUsername(nik, name)))) {
                return res.status(409).json({ error: 'exists', message: 'NIK/Username tidak tersedia.' });
            }
            const username = deriveUsername(nik, name);
            const record = {
                nik, username, name, role: 'Employee',
                passwordHash: hashPassword(password),
                createdAt: new Date().toISOString()
            };
            const ok = await createUser(record);
            if (!ok) {
                return res.status(409).json({ error: 'exists', message: 'NIK atau Username sudah terdaftar.' });
            }
            return res.status(200).json({ success: true, user: publicUser(record) });
        }

        if (action === 'login') {
            const identifier = clean(body.identifier, 80);
            const password = typeof body.password === 'string' ? body.password.trim() : '';
            if (!identifier || !password) {
                return res.status(400).json({ error: 'invalid', message: 'NIK/Username dan kata sandi wajib diisi.' });
            }

            // Administrator
            if (norm(identifier) === 'admin' || norm(identifier) === 'administrator') {
                const adminPass = process.env.ADMIN_PASSWORD || 'sppgunggul';
                if (password === adminPass) {
                    return res.status(200).json({ success: true, user: { nik: 'Admin', username: 'admin', name: 'Administrator', role: 'Admin' } });
                }
                return res.status(401).json({ error: 'invalid_credentials', message: 'NIK/Username atau kata sandi salah.' });
            }

            let user = null;
            const id = await findUserId(identifier);
            if (id) {
                const stored = await loadUser(id);
                if (stored && verifyPassword(password, stored.passwordHash)) user = stored;
            } else {
                user = await migrateLegacy(identifier, password);
            }

            if (!user) {
                return res.status(401).json({ error: 'invalid_credentials', message: 'NIK/Username atau kata sandi salah, atau akun belum terdaftar.' });
            }
            return res.status(200).json({ success: true, user: publicUser(user) });
        }

        return res.status(400).json({ error: 'unknown_action' });
    } catch (err) {
        console.error('auth error:', err && err.message);
        return res.status(500).json({ error: 'server_error', message: 'Terjadi gangguan pada server database. Coba lagi sebentar.' });
    }
}
