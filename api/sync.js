// Vercel Serverless Function: Persistent Multi-Device Synchronizer
// Endpoint: /api/sync

const CLOUD_USERS_ID = 'ff808181a09d98f701a0ce45868a7b64';
const CLOUD_HIST_ID = 'ff808181a09d98f701a0ce509a637b83';
const CLOUD_MSG_ID = 'ff808181a09d98f701a0ce509bc17b84';

let db = {
    history: [
        {
            id: 1725200001001,
            user: "Karyawan Demo",
            nik: "12345",
            menu: "Paket 1: Ayam Lengkuas + Tahu Kuning + Labu Siam + Semangka",
            portion: "Habis Semua",
            rating: "5",
            date: "Senin, 1 September 2026",
            time: "12:15"
        },
        {
            id: 1725200001002,
            user: "Ahmad Fauzi",
            nik: "10021",
            menu: "Paket 6: Udang Masak Kuah + Tempe Orek + Sayur Capcay + Semangka",
            portion: "Habis Semua",
            rating: "5",
            date: "Senin, 1 September 2026",
            time: "12:30"
        },
        {
            id: 1725200001003,
            user: "Siti Rahma",
            nik: "10045",
            menu: "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk",
            portion: "Habis Semua",
            rating: "4",
            date: "Senin, 1 September 2026",
            time: "12:45"
        }
    ],
    messages: [
        {
            id: 1725200002000,
            fromNik: "300604",
            fromName: "UL",
            text: "tes",
            reply: null,
            date: "16/9/2026, 21.09.18"
        },
        {
            id: 1725200002001,
            fromNik: "12345",
            fromName: "Karyawan Demo",
            text: "Porsi makan bergizi hari ini sangat pas dan lauk udang kuahnya enak sekali!",
            reply: "Terima kasih atas masukannya! Kami terus menjaga standar kecukupan AKG untuk seluruh karyawan.",
            date: "01/09/2026, 13.00"
        }
    ],
    users: [
        { nik: 'Admin', name: 'Administrator', password: 'sppgunggul', role: 'Admin' },
        { nik: '12345', name: 'Karyawan Demo', password: 'sppg123', role: 'Employee' },
        { nik: '10021', name: 'Ahmad Fauzi', password: 'sppg123', role: 'Employee' },
        { nik: '10045', name: 'Siti Rahma', password: 'sppg123', role: 'Employee' }
    ]
};

function sanitizeString(str) {
    if (typeof str !== 'string') return str;
    return str.replace(/<[^>]*>?/gm, '').trim();
}

async function fetchCloudUsers() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`https://api.restful-api.dev/objects/${CLOUD_USERS_ID}`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (res.ok) {
            const data = await res.json();
            if (data && data.data && Array.isArray(data.data.users)) {
                return data.data.users;
            }
        }
    } catch (e) {}
    return null;
}

async function saveCloudUsers(usersList) {
    try {
        await fetch(`https://api.restful-api.dev/objects/${CLOUD_USERS_ID}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            body: JSON.stringify({
                name: 'MBG_SPPG_USERS_PERSISTENT',
                data: { users: usersList }
            })
        });
    } catch (e) {}
}

async function fetchCloudHistory() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`https://api.restful-api.dev/objects/${CLOUD_HIST_ID}`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (res.ok) {
            const data = await res.json();
            if (data && data.data && Array.isArray(data.data.history)) {
                return data.data.history;
            }
        }
    } catch (e) {}
    return null;
}

async function saveCloudHistory(histList) {
    try {
        await fetch(`https://api.restful-api.dev/objects/${CLOUD_HIST_ID}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            body: JSON.stringify({
                name: 'MBG_SPPG_HISTORY_PERSISTENT',
                data: { history: histList }
            })
        });
    } catch (e) {}
}

async function fetchCloudMessages() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const res = await fetch(`https://api.restful-api.dev/objects/${CLOUD_MSG_ID}`, {
            headers: { 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (res.ok) {
            const data = await res.json();
            if (data && data.data && Array.isArray(data.data.messages)) {
                return data.data.messages;
            }
        }
    } catch (e) {}
    return null;
}

async function saveCloudMessages(msgList) {
    try {
        await fetch(`https://api.restful-api.dev/objects/${CLOUD_MSG_ID}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0' },
            body: JSON.stringify({
                name: 'MBG_SPPG_MESSAGES_PERSISTENT',
                data: { messages: msgList }
            })
        });
    } catch (e) {}
}

export default async function handler(req, res) {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader(
        'Access-Control-Allow-Headers',
        'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version'
    );

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    if (req.method === 'GET') {
        // Ambil data persisten dari cloud
        const cloudUsers = await fetchCloudUsers();
        if (cloudUsers && cloudUsers.length > 0) {
            for (const cUser of cloudUsers) {
                if (!db.users.find(u => u.nik.toLowerCase() === cUser.nik.toLowerCase())) {
                    db.users.push(cUser);
                }
            }
        }

        const cloudHist = await fetchCloudHistory();
        if (cloudHist && cloudHist.length > 0) {
            for (const ch of cloudHist) {
                if (!db.history.find(h => h.id === ch.id)) {
                    db.history.push(ch);
                }
            }
        }

        const cloudMsg = await fetchCloudMessages();
        if (cloudMsg && cloudMsg.length > 0) {
            for (const cm of cloudMsg) {
                const existing = db.messages.find(m => m.id === cm.id);
                if (!existing) {
                    db.messages.push(cm);
                } else if (cm.reply && !existing.reply) {
                    existing.reply = cm.reply;
                }
            }
        }

        res.status(200).json(db);
    } else if (req.method === 'POST') {
        const body = req.body || {};
        
        // Support both action payload format and type data format
        if (body.action === 'add_user' && body.payload) {
            const p = body.payload;
            p.nik = sanitizeString(p.nik);
            p.name = sanitizeString(p.name);
            p.password = sanitizeString(p.password);
            if (!db.users.find(u => u.nik.toLowerCase() === p.nik.toLowerCase())) {
                db.users.push(p);
            }
            // Simpan permanen ke cloud store
            await saveCloudUsers(db.users);
        } else if (body.action === 'add_history' && body.payload) {
            const h = body.payload;
            h.user = sanitizeString(h.user);
            h.nik = sanitizeString(h.nik);
            h.menu = sanitizeString(h.menu);
            h.portion = sanitizeString(h.portion);
            db.history.push(h);
            await saveCloudHistory(db.history);
        } else if (body.action === 'add_message' && body.payload) {
            const m = body.payload;
            m.fromNik = sanitizeString(m.fromNik);
            m.fromName = sanitizeString(m.fromName);
            m.text = sanitizeString(m.text);
            db.messages.push(m);
            await saveCloudMessages(db.messages);
        } else if (body.action === 'reply_message' && body.payload) {
            const msg = db.messages.find(m => m.id === body.payload.id);
            if (msg) {
                msg.reply = sanitizeString(body.payload.reply);
                await saveCloudMessages(db.messages);
            }
        } else if (body.action === 'user_reply_message' && body.payload) {
            const msg = db.messages.find(m => m.id === body.payload.id);
            if (msg) {
                const userAns = sanitizeString(body.payload.reply);
                msg.text = (msg.text || '') + '\n\n➡️ Tanggapan Pengguna: ' + userAns;
                msg.reply = ''; // kosongkan agar muncul tombol Balas lagi bagi admin
                await saveCloudMessages(db.messages);
            }
        } else if (body.type === 'history' && Array.isArray(body.data)) {
            db.history = body.data;
            await saveCloudHistory(db.history);
        } else if (body.type === 'messages' && Array.isArray(body.data)) {
            db.messages = body.data;
            await saveCloudMessages(db.messages);
        } else if (body.type === 'users' && Array.isArray(body.data)) {
            db.users = body.data;
            await saveCloudUsers(db.users);
        }
        res.status(200).json({ success: true, db });
    } else {
        res.status(405).json({ error: 'Method not allowed' });
    }
}
