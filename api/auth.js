// Vercel Serverless Function: Persistent Cross-Device Authentication (Register & Login)
// Penyimpanan utama: Upstash Redis / Vercel KV + Cloud JSON Storage (api.restful-api.dev)
// Sehingga akun yang didaftarkan dari perangkat/HP mana saja tersimpan terpusat di cloud
// dan langsung bisa digunakan login lintas perangkat tanpa bergantung pada localStorage lokal.

import crypto from 'node:crypto';

const CLOUD_STORAGE_URL = 'https://api.restful-api.dev/objects/ff808181a09d98f701a0ce45868a7b64';

const DEFAULT_USERS = [
    { nik: 'Admin', username: 'admin', name: 'Administrator', password: 'sppgunggul', role: 'Admin' },
    { nik: '12345', username: 'demo', name: 'Siswa / Karyawan Demo', password: 'sppg123', role: 'Employee' },
    { nik: '2304111010099', username: 'dliyaul', name: 'Dliyaul Haq', password: 'password123', role: 'Employee' },
    { nik: '2304111010006', username: 'siti', name: 'Siti Nurmasyitah', password: 'sppg123', role: 'Employee' },
    { nik: '123456789', username: 'fathin', name: 'fathin', password: '12345678', role: 'Employee' },
    { nik: '10021', username: 'ahmad', name: 'Ahmad Fauzi', password: 'sppg123', role: 'Employee' },
    { nik: '10045', username: 'rahma', name: 'Siti Rahma', password: 'sppg123', role: 'Employee' },
    { nik: '300666', username: 'yaka', name: 'yaka', password: 'terserah', role: 'Employee' }
];

if (!globalThis.__SPPG_AUTH_USERS__) {
    globalThis.__SPPG_AUTH_USERS__ = [...DEFAULT_USERS];
}

function redisConfig() {
    const url = (process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL || '').replace(/\/$/, '');
    const token = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN || '';
    return (url && token) ? { url, token } : null;
}

async function redisExec(cfg, args) {
    const r = await fetch(cfg.url, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${cfg.token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(args)
    });
    if (!r.ok) throw new Error('Redis HTTP ' + r.status);
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    return j.result;
}

const norm = (s) => String(s || '').trim().toLowerCase().replace(/\s+/g, '');

function deriveUsername(nik, name) {
    const n = norm(nik);
    if (/^\d+$/.test(n) && name) {
        const fromName = norm(name);
        if (fromName) return fromName;
    }
    return n;
}

function hashPass(password, salt) {
    return crypto.scryptSync(String(password), salt, 64).toString('hex');
}

function verifyPass(password, salt, expectedHex) {
    if (!salt || !expectedHex) return false;
    try {
        const a = Buffer.from(hashPass(password, salt), 'hex');
        const b = Buffer.from(expectedHex, 'hex');
        return a.length === b.length && crypto.timingSafeEqual(a, b);
    } catch (e) {
        return false;
    }
}

function isUserMatch(u, identifier) {
    if (!u || !identifier) return false;
    const target = String(identifier).trim().toLowerCase();
    if (!target) return false;
    const targetNoSpace = target.replace(/\s+/g, '');

    if (u.nik) {
        const uNik = String(u.nik).trim().toLowerCase();
        if (uNik === target || uNik.replace(/\s+/g, '') === targetNoSpace) return true;
    }
    if (u.username) {
        const uUser = String(u.username).trim().toLowerCase();
        if (uUser === target || uUser.replace(/\s+/g, '') === targetNoSpace) return true;
    }
    if (u.name) {
        const uName = String(u.name).trim().toLowerCase();
        if (uName === target || uName.replace(/\s+/g, '') === targetNoSpace) return true;
        const firstName = uName.split(/\s+/)[0];
        if (firstName && firstName === target) return true;
    }
    return false;
}

function mergeUsersList(...lists) {
    const merged = [...DEFAULT_USERS];
    for (const list of lists) {
        if (!Array.isArray(list)) continue;
        for (const u of list) {
            if (!u || (!u.nik && !u.username)) continue;
            const username = u.username || deriveUsername(u.nik, u.name);
            const normalizedUser = { ...u, username };
            const idx = merged.findIndex(item =>
                isUserMatch(item, normalizedUser.nik) ||
                (normalizedUser.username && isUserMatch(item, normalizedUser.username))
            );
            if (idx >= 0) {
                merged[idx] = { ...merged[idx], ...normalizedUser };
            } else {
                merged.push(normalizedUser);
            }
        }
    }
    return merged;
}

async function fetchCloudStoreObj() {
    try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 7000);
        const res = await fetch(CLOUD_STORAGE_URL, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: ctrl.signal
        });
        clearTimeout(t);
        if (res.ok) {
            const obj = await res.json();
            if (obj && obj.data) return obj.data;
        }
    } catch (e) {
        console.warn('Cloud store GET warning:', e.message);
    }
    return null;
}

async function saveCloudStoreUsers(usersList) {
    try {
        const existingData = (await fetchCloudStoreObj()) || {};
        const mergedUsers = mergeUsersList(existingData.users || [], usersList);
        globalThis.__SPPG_AUTH_USERS__ = mergedUsers;

        const payload = {
            name: 'sppg-mbg-cloud-database',
            data: {
                users: mergedUsers,
                history: Array.isArray(existingData.history) ? existingData.history : [],
                messages: Array.isArray(existingData.messages) ? existingData.messages : [],
                updatedAt: Date.now()
            }
        };

        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 8000);
        const res = await fetch(CLOUD_STORAGE_URL, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: ctrl.signal
        });
        clearTimeout(t);
        return res.ok;
    } catch (e) {
        console.warn('Cloud store PUT warning:', e.message);
        return false;
    }
}

async function findUserInRedis(cfg, identifier) {
    if (!cfg) return null;
    try {
        const raw = String(identifier || '').trim();
        const clean = norm(raw);
        if (!clean) return null;

        let id = await redisExec(cfg, ['GET', `sppg:idx:${clean}`]);
        if (!id && raw.includes(' ')) {
            const firstWord = norm(raw.split(/\s+/)[0]);
            if (firstWord) id = await redisExec(cfg, ['GET', `sppg:idx:${firstWord}`]);
        }
        const key = id ? `sppg:user:${id}` : `sppg:user:${clean}`;
        const json = await redisExec(cfg, ['GET', key]);
        if (!json) return null;
        return JSON.parse(json);
    } catch (e) {
        return null;
    }
}

async function saveUserInRedis(cfg, user) {
    if (!cfg) return false;
    try {
        const id = norm(user.nik);
        const uName = norm(user.username || deriveUsername(user.nik, user.name));
        const fullName = norm(user.name);
        const firstWord = norm(String(user.name || '').trim().split(/\s+/)[0]);

        const record = {
            nik: String(user.nik).trim(),
            username: uName,
            name: String(user.name).trim(),
            role: user.role || 'Employee',
            salt: user.salt,
            passHash: user.passHash,
            password: user.password,
            createdAt: user.createdAt || new Date().toISOString()
        };

        await redisExec(cfg, ['SET', `sppg:user:${id}`, JSON.stringify(record)]);
        await redisExec(cfg, ['SET', `sppg:idx:${id}`, id]);
        if (uName) await redisExec(cfg, ['SET', `sppg:idx:${uName}`, id]);
        if (fullName) await redisExec(cfg, ['SET', `sppg:idx:${fullName}`, id]);
        if (firstWord && firstWord.length >= 3) {
            const existing = await redisExec(cfg, ['GET', `sppg:idx:${firstWord}`]);
            if (!existing) await redisExec(cfg, ['SET', `sppg:idx:${firstWord}`, id]);
        }
        await redisExec(cfg, ['SADD', 'sppg:users:all', id]);
        return true;
    } catch (e) {
        return false;
    }
}

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Cache-Control', 'no-store');

    if (req.method === 'OPTIONS') return res.status(200).end();

    const cfg = redisConfig();

    if (req.method === 'GET') {
        const cloudData = await fetchCloudStoreObj();
        const allUsers = mergeUsersList(
            globalThis.__SPPG_AUTH_USERS__,
            cloudData && Array.isArray(cloudData.users) ? cloudData.users : []
        );
        globalThis.__SPPG_AUTH_USERS__ = allUsers;
        return res.status(200).json({
            success: true,
            users: allUsers.map(u => ({
                nik: u.nik,
                username: u.username || deriveUsername(u.nik, u.name),
                name: u.name,
                role: u.role || 'Employee'
            }))
        });
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ success: false, message: 'Method not allowed' });
    }

    try {
        const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
        const { action } = body;

        // ============================================================
        // 1. REGISTRASI AKUN BARU (TERSIMPAN KE CLOUD LINTAS PERANGKAT)
        // ============================================================
        if (action === 'register') {
            const nik = String(body.nik || '').trim();
            const name = String(body.name || '').trim();
            const password = String(body.password || '').trim();

            if (!nik || !name || !password) {
                return res.status(400).json({
                    success: false,
                    message: 'NIK/Username, Nama Lengkap, dan Kata Sandi wajib diisi.'
                });
            }
            if (nik.length > 64 || name.length > 100 || password.length > 128) {
                return res.status(400).json({
                    success: false,
                    message: 'Data input melebihi batas panjang karakter.'
                });
            }

            const username = deriveUsername(nik, name);

            // Ambil data cloud terbaru
            const cloudData = await fetchCloudStoreObj();
            const allUsers = mergeUsersList(
                globalThis.__SPPG_AUTH_USERS__,
                cloudData && Array.isArray(cloudData.users) ? cloudData.users : []
            );
            globalThis.__SPPG_AUTH_USERS__ = allUsers;

            // Cek apakah sudah terdaftar di Redis atau Cloud Store
            const existingRedis = await findUserInRedis(cfg, nik) || (username !== norm(nik) ? await findUserInRedis(cfg, username) : null);
            const existingCloud = allUsers.find(u =>
                String(u.nik).trim().toLowerCase() === nik.toLowerCase() ||
                (u.username && String(u.username).trim().toLowerCase() === username.toLowerCase())
            );

            if (existingRedis || existingCloud) {
                return res.status(409).json({
                    success: false,
                    error: 'already_exists',
                    message: `NIK atau Username "${nik}" sudah terdaftar di sistem. Silakan langsung masuk menggunakan akun Anda.`
                });
            }

            const salt = crypto.randomBytes(16).toString('hex');
            const passHash = hashPass(password, salt);

            const newUser = {
                nik,
                username,
                name,
                role: 'Employee',
                salt,
                passHash,
                password,
                createdAt: new Date().toISOString()
            };

            // Simpan ke Redis (jika ada) dan Cloud Store
            await saveUserInRedis(cfg, newUser);
            allUsers.push(newUser);
            globalThis.__SPPG_AUTH_USERS__ = allUsers;
            await saveCloudStoreUsers(allUsers);

            return res.status(200).json({
                success: true,
                user: { nik: newUser.nik, username: newUser.username, name: newUser.name, role: newUser.role }
            });
        }

        // ============================================================
        // 2. LOGIN LINTAS PERANGKAT
        // ============================================================
        if (action === 'login') {
            const identifier = String(body.identifier || body.nik || '').trim();
            const password = String(body.password || '').trim();

            if (!identifier || !password) {
                return res.status(400).json({
                    success: false,
                    message: 'Harap masukkan NIK/Username dan Kata Sandi.'
                });
            }

            // 1. Cek di Redis terlebih dahulu jika tersedia
            const redisUser = await findUserInRedis(cfg, identifier);
            if (redisUser) {
                const validHash = redisUser.salt && redisUser.passHash && verifyPass(password, redisUser.salt, redisUser.passHash);
                const validPlain = redisUser.password && String(redisUser.password).trim() === password;
                if (validHash || validPlain) {
                    return res.status(200).json({
                        success: true,
                        user: {
                            nik: redisUser.nik,
                            username: redisUser.username || deriveUsername(redisUser.nik, redisUser.name),
                            name: redisUser.name,
                            role: redisUser.role || 'Employee'
                        }
                    });
                }
            }

            // 2. Cek di Cloud Storage & Memori Global
            const cloudData = await fetchCloudStoreObj();
            const allUsers = mergeUsersList(
                globalThis.__SPPG_AUTH_USERS__,
                cloudData && Array.isArray(cloudData.users) ? cloudData.users : []
            );
            globalThis.__SPPG_AUTH_USERS__ = allUsers;

            const matchedUsers = allUsers.filter(u => isUserMatch(u, identifier));
            if (matchedUsers.length === 0) {
                return res.status(401).json({
                    success: false,
                    error: 'invalid_credentials',
                    message: 'NIK/Username atau Kata Sandi salah, atau akun belum terdaftar.'
                });
            }

            for (const candidate of matchedUsers) {
                const validHash = candidate.salt && candidate.passHash && verifyPass(password, candidate.salt, candidate.passHash);
                const validPlain = candidate.password !== undefined && String(candidate.password).trim() === password;
                if (validHash || validPlain) {
                    return res.status(200).json({
                        success: true,
                        user: {
                            nik: candidate.nik,
                            username: candidate.username || deriveUsername(candidate.nik, candidate.name),
                            name: candidate.name,
                            role: candidate.role || 'Employee'
                        }
                    });
                }
            }

            return res.status(401).json({
                success: false,
                error: 'invalid_credentials',
                message: 'Kata Sandi yang Anda masukkan salah.'
            });
        }

        return res.status(400).json({ success: false, message: 'Action tidak dikenal.' });
    } catch (e) {
        console.error('Auth error:', e);
        return res.status(500).json({ success: false, error: 'server_error', message: 'Gangguan server autentikasi.' });
    }
}
