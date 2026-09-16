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

        const rawKey = apiKey || process.env.GEMINI_API_KEY || '';
        const effectiveKey = rawKey.replace('AIzaSyAQ.', 'AQ.').trim();
        if (!effectiveKey) {
            return res.status(400).json({ error: 'GEMINI_API_KEY belum dikonfigurasi di Vercel atau form' });
        }

        const cleanBase64 = image.includes(',') ? image.split(',')[1] : image;

        const promptText = `Kamu adalah pakar computer vision gizi Program Makan Bergizi Gratis (MBG) Kemenkes RI.
Analisis citra baki makanan kompartemen stainless ini secara sangat cermat dan objektif.
Identifikasi setiap masakan di sekat baki:
1. Makanan Pokok: (contoh: Nasi Putih Pulen Bentuk Hati, Nasi Goreng, dll)
2. Lauk Hewani: Perhatikan dengan seksama! Jika terlihat potongan paha ayam / daging ayam berbumbu saus/kuah, sebut 'Paha Ayam Masak Saus Gurih' atau nama ayam aslinya. DILARANG menyebut Telur jika yang tersaji adalah potongan ayam!
3. Lauk Nabati: (contoh: Tempe Goreng Gurih, Tempe Orek, Tahu Goreng)
4. Sayuran: Perhatikan jenis sayurnya! Jika terlihat buncis hijau panjang ditumis, sebut 'Tumis Buncis Hijau'. DILARANG menyebut Capcay jika berupa buncis!
5. Buah: Perhatikan buahnya! Jika terlihat butiran kelengkeng cokelat bulat, sebut 'Buah Kelengkeng Segar'.

Kembalikan HANYA format JSON valid persis berikut tanpa markdown atau backtick:
{
  "packageName": "Nama Menu Lengkap MBG",
  "karbo": {"name": "Nasi Putih Pulen", "val": "150", "gram": 150, "kal": 195, "pro": 4.0, "kar": 43.0, "lem": 0.5, "conf": "99.2%"},
  "prohew": {"name": "Nama Lauk Hewani Asli", "val": "200", "gram": 85, "kal": 215, "pro": 24.0, "kar": 1.5, "lem": 12.5, "conf": "98.8%"},
  "pronab": {"name": "Nama Lauk Nabati Asli", "val": "120", "gram": 50, "kal": 115, "pro": 9.5, "kar": 8.0, "lem": 5.0, "conf": "98.0%"},
  "sayur": {"name": "Nama Sayuran Asli", "val": "20", "gram": 75, "kal": 25, "pro": 1.2, "kar": 4.5, "lem": 0.5, "conf": "98.5%"},
  "buah": {"name": "Nama Buah Asli", "gram": 75, "kal": 45, "pro": 1.0, "kar": 11.3, "lem": 0.1, "conf": "99.0%"},
  "analysis": "Porsi dan komposisi makanan teranalisis otomatis sesuai standar gizi resmi Kemenkes RI."
}`;

        const modelsToTry = [
            'gemini-flash-lite-latest',
            'gemini-2.5-flash-lite',
            'gemini-3.5-flash-lite',
            'gemini-2.0-flash',
            'gemini-1.5-flash'
        ];

        let lastError = null;

        for (const modelName of modelsToTry) {
            try {
                const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${encodeURIComponent(effectiveKey)}`;
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
                            responseMimeType: 'application/json'
                        }
                    })
                });

                if (!geminiRes.ok) {
                    const errText = await geminiRes.text();
                    lastError = new Error(`Model ${modelName} returned HTTP ${geminiRes.status}: ${errText}`);
                    continue;
                }

                const data = await geminiRes.json();
                const rawText = data.candidates?.[0]?.content?.parts?.[0]?.text;
                if (!rawText) {
                    lastError = new Error(`Empty response from ${modelName}`);
                    continue;
                }

                const cleanedJson = JSON.parse(rawText.replace(/```json|```/g, '').trim());
                return res.status(200).json({ success: true, data: cleanedJson, model: modelName });
            } catch (mErr) {
                lastError = mErr;
            }
        }

        return res.status(500).json({ error: lastError ? lastError.message : 'Semua model Gemini gagal merespons' });
    } catch (err) {
        return res.status(500).json({ error: err.message || 'Internal Server Error' });
    }
}
