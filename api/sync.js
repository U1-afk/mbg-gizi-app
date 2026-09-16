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

export default function handler(req, res) {
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
        } else if (body.action === 'add_history' && body.payload) {
            const h = body.payload;
            h.user = sanitizeString(h.user);
            h.nik = sanitizeString(h.nik);
            h.menu = sanitizeString(h.menu);
            h.portion = sanitizeString(h.portion);
            db.history.push(h);
        } else if (body.action === 'add_message' && body.payload) {
            const m = body.payload;
            m.fromNik = sanitizeString(m.fromNik);
            m.fromName = sanitizeString(m.fromName);
            m.text = sanitizeString(m.text);
            db.messages.push(m);
        } else if (body.action === 'reply_message' && body.payload) {
            const msg = db.messages.find(m => m.id === body.payload.id);
            if (msg) {
                msg.reply = sanitizeString(body.payload.reply);
            }
        } else if (body.action === 'user_reply_message' && body.payload) {
            const msg = db.messages.find(m => m.id === body.payload.id);
            if (msg) {
                const userAns = sanitizeString(body.payload.reply);
                msg.text = (msg.text || '') + '\n\n➡️ Tanggapan Pengguna: ' + userAns;
                msg.reply = ''; // kosongkan agar muncul tombol Balas lagi bagi admin
            }
        } else if (body.type === 'history' && Array.isArray(body.data)) {
            db.history = body.data;
        } else if (body.type === 'messages' && Array.isArray(body.data)) {
            db.messages = body.data;
        } else if (body.type === 'users' && Array.isArray(body.data)) {
            db.users = body.data;
        }
        res.status(200).json({ success: true, db });
    } else {
        res.status(405).json({ error: 'Method not allowed' });
    }
}
