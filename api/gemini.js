// Vercel Serverless Function: Google Gemini Vision Food Tray Analyzer & Custom Food Nutrition AI
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
        const { image, apiKey, action, foodName, gram } = req.body || {};

        const rawKey = apiKey || process.env.GEMINI_API_KEY || '';
        const effectiveKey = rawKey.replace('AIzaSyAQ.', 'AQ.').trim();

        const modelsToTry = [
            'gemini-flash-lite-latest',
            'gemini-2.5-flash-lite',
            'gemini-3.5-flash-lite',
            'gemini-2.0-flash',
            'gemini-1.5-flash'
        ];

        // ============================================================
        // A. PENCARIAN & PERHITUNGAN NUTRISI MAKANAN KUSTOM DENGAN AI
        // ============================================================
        if (action === 'lookup_food' || (!image && foodName)) {
            const cleanFood = String(foodName || '').trim().toLowerCase();
            const foodGram = Math.max(1, parseFloat(gram) || 100);
            const ratio = foodGram / 100.0;

            const TKPI_LOOKUP = {
                "bubur ayam": { kal: 155, pro: 6.5, kar: 24.0, lem: 3.8 },
                "soto ayam": { kal: 120, pro: 9.5, kar: 6.0, lem: 6.5 },
                "bakso": { kal: 190, pro: 12.0, kar: 14.0, lem: 9.5 },
                "gado-gado": { kal: 145, pro: 6.8, kar: 16.0, lem: 6.8 },
                "mie ayam": { kal: 185, pro: 7.8, kar: 28.0, lem: 4.5 },
                "nasi uduk": { kal: 180, pro: 3.8, kar: 34.0, lem: 3.5 },
                "nasi kuning": { kal: 175, pro: 3.5, kar: 33.0, lem: 3.2 },
                "nasi liwet": { kal: 170, pro: 3.6, kar: 32.0, lem: 3.0 },
                "rendang": { kal: 260, pro: 22.0, kar: 6.0, lem: 16.5 },
                "sate ayam": { kal: 210, pro: 18.0, kar: 8.0, lem: 11.5 },
                "rawon": { kal: 160, pro: 14.0, kar: 5.0, lem: 9.5 },
                "gulai": { kal: 175, pro: 13.0, kar: 4.5, lem: 11.5 },
                "siomay": { kal: 160, pro: 8.5, kar: 18.0, lem: 6.0 },
                "pempek": { kal: 180, pro: 7.5, kar: 27.0, lem: 4.5 },
                "martabak telur": { kal: 240, pro: 11.0, kar: 18.0, lem: 14.0 },
                "martabak manis": { kal: 280, pro: 5.5, kar: 46.0, lem: 8.5 },
                "pizza": { kal: 266, pro: 11.0, kar: 33.0, lem: 10.0 },
                "burger": { kal: 250, pro: 13.0, kar: 26.0, lem: 11.0 },
                "spaghetti": { kal: 158, pro: 5.8, kar: 30.0, lem: 1.5 },
                "kentang goreng": { kal: 280, pro: 3.5, kar: 36.0, lem: 14.0 },
                "sosis": { kal: 260, pro: 12.0, kar: 4.0, lem: 22.0 },
                "nugget": { kal: 250, pro: 13.5, kar: 16.0, lem: 14.5 },
                "roti bakar": { kal: 220, pro: 6.0, kar: 40.0, lem: 4.5 },
                "pisang goreng": { kal: 195, pro: 2.0, kar: 35.0, lem: 5.5 },
                "kacang hijau": { kal: 140, pro: 7.0, kar: 24.0, lem: 1.5 },
                "ayam goreng": { kal: 230, pro: 22.5, kar: 8.0, lem: 12.0 },
                "telur dadar": { kal: 150, pro: 10.0, kar: 2.0, lem: 11.5 },
                "tempe orek": { kal: 180, pro: 14.0, kar: 12.0, lem: 8.0 },
                "tahu isi": { kal: 160, pro: 8.0, kar: 15.0, lem: 7.5 },
                "kerupuk": { kal: 500, pro: 3.5, kar: 65.0, lem: 26.0 },
                "crackers": { kal: 500, pro: 3.5, kar: 65.0, lem: 26.0 },
                "finna": { kal: 500, pro: 3.5, kar: 65.0, lem: 26.0 },
                "susu": { kal: 65, pro: 3.2, kar: 4.8, lem: 3.5 },
                "puding": { kal: 80, pro: 1.0, kar: 18.0, lem: 0.5 },
                "semangka": { kal: 32, pro: 0.6, kar: 7.6, lem: 0.2 },
                "telur mata sapi": { kal: 185, pro: 12.4, kar: 0.8, lem: 14.2 }
            };

            // Coba panggil Gemini AI jika key tersedia
            if (effectiveKey) {
                const promptLookup = `Kamu adalah pakar gizi kuliner Indonesia Kemenkes RI. Berapa estimasi zat gizi untuk makanan Indonesia "${foodName}" seberat ${foodGram} gram?
Kembalikan HANYA format JSON valid persis berikut tanpa markdown atau backtick:
{"name": "${foodName}", "gram": ${foodGram}, "kal": 180, "pro": 12.5, "kar": 20.0, "lem": 6.5, "source": "Google Gemini AI"}`;

                for (const modelName of modelsToTry) {
                    try {
                        const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${encodeURIComponent(effectiveKey)}`;
                        const gRes = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                contents: [{ parts: [{ text: promptLookup }] }],
                                generationConfig: { temperature: 0.1, responseMimeType: 'application/json' }
                            })
                        });
                        if (gRes.ok) {
                            const data = await gRes.json();
                            const txt = data.candidates?.[0]?.content?.parts?.[0]?.text;
                            if (txt) {
                                const parsed = JSON.parse(txt.replace(/```json|```/g, '').trim());
                                return res.status(200).json({ success: true, data: parsed, model: modelName });
                            }
                        }
                    } catch (e) {}
                }
            }

            // Fallback ke basis data standar TKPI Kemenkes RI
            for (const [k, v] of Object.entries(TKPI_LOOKUP)) {
                if (cleanFood.includes(k)) {
                    return res.status(200).json({
                        success: true,
                        data: {
                            name: foodName,
                            gram: foodGram,
                            kal: Math.round(v.kal * ratio),
                            pro: parseFloat((v.pro * ratio).toFixed(1)),
                            kar: parseFloat((v.kar * ratio).toFixed(1)),
                            lem: parseFloat((v.lem * ratio).toFixed(1)),
                            source: 'Standar TKPI Kemenkes RI'
                        }
                    });
                }
            }

            // Heuristik Terstandarisasi
            let baseKal = 150.0, basePro = 5.0, baseKar = 22.0, baseLem = 4.0;
            if (/daging|ayam|sapi|kambing|ikan|udang|telur/i.test(cleanFood)) {
                baseKal = 210.0; basePro = 20.0; baseKar = 3.0; baseLem = 13.0;
            } else if (/kerupuk|krupuk|cracker|garlic|rempeyek|emping|peyek/i.test(cleanFood)) {
                baseKal = 500.0; basePro = 3.5; baseKar = 65.0; baseLem = 26.0;
            } else if (/nasi|mie|roti|bihun|kentang/i.test(cleanFood)) {
                baseKal = 175.0; basePro = 4.0; baseKar = 36.0; baseLem = 1.5;
            } else if (/sayur|sup|sop|bayam|kangkung|wortel|buncis/i.test(cleanFood)) {
                baseKal = 45.0; basePro = 2.0; baseKar = 7.0; baseLem = 0.5;
            } else if (/buah|apel|jeruk|semangka|pisang|melon/i.test(cleanFood)) {
                baseKal = 60.0; basePro = 1.0; baseKar = 14.0; baseLem = 0.3;
            } else if (/susu|milk/i.test(cleanFood)) {
                baseKal = 65.0; basePro = 3.2; baseKar = 4.8; baseLem = 3.5;
            } else if (/puding|agar/i.test(cleanFood)) {
                baseKal = 80.0; basePro = 1.0; baseKar = 18.0; baseLem = 0.5;
            }

            return res.status(200).json({
                success: true,
                data: {
                    name: foodName,
                    gram: foodGram,
                    kal: Math.round(baseKal * ratio),
                    pro: parseFloat((basePro * ratio).toFixed(1)),
                    kar: parseFloat((baseKar * ratio).toFixed(1)),
                    lem: parseFloat((baseLem * ratio).toFixed(1)),
                    source: 'Estimasi Komposisi Pangan Terstandarisasi'
                }
            });
        }

        // ============================================================
        // B. PEMINDAIAN & ANALISIS CITRA BAKI MAKANAN (VISION)
        // ============================================================
        if (!image) {
            return res.status(400).json({ error: 'Gambar tidak ditemukan dalam request' });
        }

        if (!effectiveKey) {
            return res.status(400).json({ error: 'GEMINI_API_KEY belum dikonfigurasi di Vercel atau form' });
        }

        const cleanBase64 = image.includes(',') ? image.split(',')[1] : image;

        const promptText = `Kamu adalah pakar computer vision dan sistem visual multimodal AI gizi Program Makan Bergizi Gratis (MBG) Kemenkes RI.
Tugasmu adalah menganalisis citra baki makanan kompartemen stainless ini secara sangat cermat, objektif, dan mendalam.
Kenali SETIAP makanan, lauk, sayur, buah, minuman, maupun kemasan kerupuk/snack/puding yang ada di SEMUA sekat baki.

ATURAN DETEKSI LENGKAP:
1. Kemasan / Kerupuk / Camilan: Periksa sekat yang berisi kemasan bungkusan makanan, kerupuk, keripik, atau snack! Baca teks/merek pada kemasan jika ada (misal: 'FINNA Garlic Crackers / Kerupuk Bawang Goreng', 'Kerupuk Udang', 'Kerupuk Putih', dll.). JANGAN LEWATKAN kemasan kerupuk atau camilan ini!
2. Susu / Puding / Pencuci Mulut: Jika ada susu kemasan kotak (UHT), susu cup, atau puding/agar-agar cup, identifikasi jenis dan rasanya.
3. Makanan Pokok: Identifikasi jenis & bentuk nasi (misal: Nasi Kuning Gurih, Nasi Putih Pulen Bentuk Hati, Nasi Goreng, Mie, Kentang, dll.).
4. Lauk Hewani: Kenali olahan lauk hewani secara tepat (Telur Mata Sapi / Ceplok, Paha Ayam Masak Saus Gurih, Ayam Lengkuas, Daging Semur/Rendang, Udang, Ikan Filet, dll.).
5. Lauk Nabati: (Tempe Orek Dadu, Tempe Goreng Gurih, Tahu Goreng Kotak, Perkedel, dll.).
6. Sayuran: (Tumis Buncis Hijau, Sayur Capcay, Sayur Sop, Lalapan Selada/Timun, dll.).
7. Buah-buahan: Kenali buah dan warnanya (Buah Semangka Kuning Segar jika daging buahnya kuning, Semangka Merah, Buah Kelengkeng Segar, Jeruk, Pisang, dll.).

Kembalikan HANYA format JSON valid persis berikut tanpa markdown atau backtick:
{
  "packageName": "Nama Menu Lengkap MBG (sebutkan semua komponen termasuk kerupuk/pelengkap)",
  "items": [
    {
      "category": "Makanan Pokok / Karbohidrat",
      "name": "Nama Makanan Pokok Spesifik",
      "gram": 150,
      "kal": 210,
      "pro": 4.2,
      "kar": 41.5,
      "lem": 3.2,
      "conf": "99.2%"
    },
    {
      "category": "Protein Hewani",
      "name": "Nama Lauk Hewani",
      "gram": 60,
      "kal": 95,
      "pro": 6.3,
      "kar": 0.6,
      "lem": 7.2,
      "conf": "99.5%"
    },
    {
      "category": "Protein Nabati",
      "name": "Nama Lauk Nabati",
      "gram": 45,
      "kal": 105,
      "pro": 8.5,
      "kar": 7.5,
      "lem": 4.8,
      "conf": "98.2%"
    },
    {
      "category": "Sayuran",
      "name": "Nama Sayuran",
      "gram": 75,
      "kal": 25,
      "pro": 1.2,
      "kar": 4.5,
      "lem": 0.5,
      "conf": "98.7%"
    },
    {
      "category": "Buah-buahan",
      "name": "Nama Buah (misal: Buah Semangka Kuning Segar)",
      "gram": 100,
      "kal": 30,
      "pro": 0.6,
      "kar": 7.5,
      "lem": 0.2,
      "conf": "99.2%"
    },
    {
      "category": "Pelengkap / Kerupuk",
      "name": "Kerupuk Bawang Finna (Garlic Crackers)",
      "gram": 15,
      "kal": 70,
      "pro": 0.5,
      "kar": 11.0,
      "lem": 2.8,
      "conf": "99.0%"
    }
  ],
  "karbo": {"name": "Nasi Kuning Gurih", "val": "210", "gram": 150, "kal": 210, "pro": 4.2, "kar": 41.5, "lem": 3.2, "conf": "99.2%"},
  "prohew": {"name": "Telur Mata Sapi", "val": "92", "gram": 60, "kal": 95, "pro": 6.3, "kar": 0.6, "lem": 7.2, "conf": "99.5%"},
  "pronab": {"name": "Tempe Orek Dadu", "val": "110", "gram": 45, "kal": 105, "pro": 8.5, "kar": 7.5, "lem": 4.8, "conf": "98.2%"},
  "sayur": {"name": "Tumis Buncis Hijau", "val": "32", "gram": 75, "kal": 25, "pro": 1.2, "kar": 4.5, "lem": 0.5, "conf": "98.7%"},
  "buah": {"name": "Buah Semangka Kuning Segar", "gram": 100, "kal": 30, "pro": 0.6, "kar": 7.5, "lem": 0.2, "conf": "99.2%"},
  "pelengkap": {"name": "Kerupuk Bawang Finna (Garlic Crackers)", "gram": 15, "kal": 70, "pro": 0.5, "kar": 11.0, "lem": 2.8, "conf": "99.0%"},
  "analysis": "Porsi dan komposisi makanan teranalisis otomatis sesuai standar gizi resmi Kemenkes RI."
}`;

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
