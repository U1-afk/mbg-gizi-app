// Vercel Serverless Function: Google Gemini Vision Food Tray Analyzer
// Endpoint: /api/gemini

export default async function handler(req, res) {
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,POST');
    res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const { image, apiKey } = req.body || {};
        if (!image) {
            return res.status(400).json({ error: 'Gambar tidak ditemukan dalam request' });
        }

        const effectiveKey = apiKey || process.env.GEMINI_API_KEY;
        if (!effectiveKey) {
            return res.status(400).json({ error: 'GEMINI_API_KEY belum dikonfigurasi di Vercel atau form' });
        }

        const promptText = `Anda adalah Ahli Gizi Profesional yang menganalisis baki makanan program MBG (Makan Bergizi Gratis) Indonesia.
Tugas Anda:
1. Identifikasi secara akurat jenis makanan di setiap sekat baki ompreng stainless:
   - Karbohidrat (contoh: Nasi Putih Pulen, Nasi Merah, dll)
   - Lauk Hewani (contoh: Ayam Goreng Lengkuas, Ikan Masak Bumbu, Udang Kuah Kuning, Telur Rebus, Telur Balado, Dadu Ayam)
   - Lauk Nabati (contoh: Tempe Orek Dadu, Tahu Goreng Kuning, Tahu Kotak, Tempe Goreng)
   - Sayuran (contoh: Sayur Sop Wortel Kol, Tumis Kangkung, Sayur Capcay, Tumis Buncis, Labu Siam)
   - Buah / Pelengkap (contoh: Buah Kelengkeng Segar, Buah Semangka Merah, Buah Jeruk, Buah Melon, Pisang)
2. Estimasi gramatur porsi standar makan siang siswa (TKPI Kemenkes RI) dan hitung Kalori, Protein, Karbohidrat, Lemak.
3. Berikan output HANYA berupa JSON murni tanpa markdown, tanpa backtick, format persis berikut:
{
  "packageName": "Nama Menu Lengkap MBG",
  "karbo": {"name": "Nasi Putih Pulen", "val": "150", "gram": 150, "kal": 195, "pro": 4.0, "kar": 43.0, "lem": 0.5, "conf": "98.5%"},
  "prohew": {"name": "Nama Lauk Hewani", "val": "200", "gram": 85, "kal": 215, "pro": 24.0, "kar": 1.5, "lem": 12.5, "conf": "97.0%"},
  "pronab": {"name": "Nama Lauk Nabati", "val": "120", "gram": 50, "kal": 115, "pro": 9.5, "kar": 8.0, "lem": 5.0, "conf": "96.2%"},
  "sayur": {"name": "Nama Sayuran", "val": "20", "gram": 75, "kal": 25, "pro": 1.2, "kar": 4.5, "lem": 0.5, "conf": "95.0%"},
  "buah": {"name": "Nama Buah / Pelengkap", "gram": 75, "kal": 45, "pro": 1.0, "kar": 11.3, "lem": 0.1, "conf": "97.5%"},
  "analysis": "Porsi dan komposisi makanan teranalisis otomatis sesuai standar gizi resmi."
}`;

        const cleanBase64 = image.includes(',') ? image.split(',')[1] : image;
        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${encodeURIComponent(effectiveKey)}`;

        const geminiRes = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contents: [{
                    parts: [
                        { text: promptText },
                        { inline_data: { mime_type: 'image/jpeg', data: cleanBase64 } }
                    ]
                }],
                generationConfig: {
                    temperature: 0.1,
                    responseMimeType: "application/json"
                }
            })
        });

        if (!geminiRes.ok) {
            const errBody = await geminiRes.text();
            return res.status(geminiRes.status).json({ error: 'Gemini API Error: ' + errBody });
        }

        const data = await geminiRes.json();
        const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text;
        if (!rawText) {
            return res.status(500).json({ error: 'Tidak ada respons teks dari Gemini API' });
        }

        const cleanedJson = JSON.parse(rawText.replace(/```json|```/g, '').trim());
        return res.status(200).json({ success: true, data: cleanedJson });
    } catch (err) {
        return res.status(500).json({ error: err.message || 'Internal Server Error' });
    }
}
