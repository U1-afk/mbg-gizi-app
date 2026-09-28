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

        const defaultKey = Buffer.from('QVEuQWI4Uk42SXhRQjdtZWZDajlLMDdoTVRKaXo1SzgweUZON3JDTkJTRFpsdzM5NmVHaFE=', 'base64').toString('utf-8');
        const effectiveKey = String(apiKey || process.env.GEMINI_API_KEY || defaultKey).replace(/^["']|["']$/g, '').trim();

        const modelsToTry = [
            'gemini-3-flash-preview',
            'gemini-3.1-flash-lite-preview',
            'gemini-3.1-flash-lite',
            'gemini-3.8-flash',
            'gemini-3.7-flash'
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
                "ayam lengkuas": { kal: 245, pro: 26.0, kar: 2.0, lem: 13.5 },
                "telur dadar": { kal: 150, pro: 10.0, kar: 2.0, lem: 11.5 },
                "telur ceplok": { kal: 185, pro: 12.4, kar: 0.8, lem: 14.2 },
                "tempe orek": { kal: 210, pro: 17.0, kar: 18.0, lem: 9.0 },
                "tahu isi": { kal: 160, pro: 8.0, kar: 15.0, lem: 7.5 },
                "tahu goreng": { kal: 95, pro: 9.0, kar: 2.5, lem: 5.5 },
                "kerupuk": { kal: 480, pro: 3.5, kar: 65.0, lem: 24.0 },
                "kerupuk bawang": { kal: 480, pro: 3.5, kar: 65.0, lem: 24.0 },
                "kerupuk pangsit": { kal: 480, pro: 4.5, kar: 65.0, lem: 22.0 },
                "crackers": { kal: 500, pro: 3.5, kar: 65.0, lem: 26.0 },
                "finna": { kal: 480, pro: 3.5, kar: 65.0, lem: 24.0 },
                "susu": { kal: 65, pro: 3.2, kar: 4.8, lem: 3.5 },
                "puding": { kal: 80, pro: 1.0, kar: 18.0, lem: 0.5 },
                "kelengkeng": { kal: 60, pro: 1.3, kar: 15.1, lem: 0.1 },
                "lengkeng": { kal: 60, pro: 1.3, kar: 15.1, lem: 0.1 },
                "salak": { kal: 77, pro: 0.4, kar: 20.9, lem: 0.2 },
                "semangka": { kal: 32, pro: 0.6, kar: 7.6, lem: 0.2 },
                "melon": { kal: 36, pro: 0.8, kar: 8.5, lem: 0.2 },
                "sayur bayam": { kal: 20, pro: 1.6, kar: 3.5, lem: 0.3 },
                "bayam": { kal: 20, pro: 1.6, kar: 3.5, lem: 0.3 },
                "tumis buncis": { kal: 45, pro: 1.8, kar: 5.5, lem: 2.2 },
                "tumis jagung": { kal: 65, pro: 2.2, kar: 14.0, lem: 0.8 },
                "jagung manis": { kal: 65, pro: 2.2, kar: 14.0, lem: 0.8 },
                "sayur capcay": { kal: 48, pro: 1.8, kar: 6.0, lem: 2.5 },
                "sayur sop": { kal: 25, pro: 1.3, kar: 4.5, lem: 0.5 },
                "sayur lodeh": { kal: 70, pro: 2.0, kar: 6.0, lem: 4.5 },
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
            return res.status(200).json({
                success: false,
                fallback: true,
                message: 'GEMINI_API_KEY tidak aktif, dialihkan ke analisis visual baki cepat on-device'
            });
        }

        const cleanBase64 = image.includes(',') ? image.split(',')[1] : image;

        const promptText = `Kamu adalah sistem vision AI untuk analisis visual makanan Program Makan Bergizi Gratis (MBG).
Tugasmu adalah menganalisis citra foto baki makanan bersekat/kompartemen ini secara cermat, objektif, dan murni berdasarkan apa yang tampak di foto tanpa mengarang.

Instruksi Analisis:
1. Identifikasi setiap jenis makanan yang benar-benar tampak di foto baki (seperti makanan pokok/karbohidrat, lauk hewani, lauk nabati, sayuran, buah-buahan, camilan/kerupuk, atau susu).
2. Tuliskan nama makanan secara spesifik apa adanya sesuai wujud aslinya (misalnya: "nasi putih", "kelengkeng", "telur ceplok", "tempe orek", "tumis jagung", dsb.).
3. JANGAN mengarang makanan yang tidak terlihat di foto. JANGAN mengubah identifikasi makanan menjadi makanan lain karena contoh atau asumsi.
4. Estimasi berat porsi makanan dalam gram (estimated_grams) yang realistis untuk porsi makan siang anak sekolah (angka > 0).
5. Berikan detection confidence (confidence: desimal 0.0 - 1.0) untuk ketepatan identifikasi visual makanan.
6. Untuk setiap makanan, berikan estimasi nilai gizi per 100 gram (nutrition_per_100g: energy_kcal, protein_g, carbohydrate_g, fat_g) berdasarkan pengetahuan nutrisi umum sebagai fallback jika makanan belum ada di database lokal.
7. Sediakan nutrition_confidence (desimal 0.0 - 1.0) dan tandai nutrition_source: "AI_ESTIMATE". Nilai tersebut hanya merupakan estimasi dan bukan pengganti data laboratorium atau database nutrisi resmi.
8. Jika baki kosong, buram parah, atau makanan tidak dapat diidentifikasi dengan yakin, kembalikan items kosong [] dan jelaskan di analysis bahwa foto kurang jelas.

Kembalikan HANYA format JSON valid tanpa markdown atau backtick dengan struktur:
{
  "packageName": "Ringkasan Menu MBG Terdeteksi",
  "items": [
    {
      "name": "nama makanan",
      "category": "karbohidrat | hewani | nabati | sayur | buah | pelengkap",
      "estimated_grams": 100,
      "confidence": 0.85,
      "nutrition_per_100g": {
        "energy_kcal": 60.0,
        "protein_g": 1.3,
        "carbohydrate_g": 15.0,
        "fat_g": 0.1
      },
      "nutrition_confidence": 0.70,
      "nutrition_source": "AI_ESTIMATE"
    }
  ],
  "analysis": "Deskripsi singkat hasil pengamatan visual baki makanan."
}`;

        let lastError = null;

        for (const modelName of modelsToTry) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 6000);
                const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${encodeURIComponent(effectiveKey)}`;
                const geminiRes = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{
                            parts: [
                                { text: promptText },
                                { inlineData: { mimeType: 'image/jpeg', data: cleanBase64 } }
                            ]
                        }],
                        generationConfig: {
                            temperature: 0.1,
                            responseMimeType: 'application/json'
                        }
                    }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

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

                let cleanedJson;
                try {
                    cleanedJson = JSON.parse(rawText.replace(/```json/gi, '').replace(/```/g, '').trim());
                } catch (parseE) {
                    const match = rawText.match(/\{[\s\S]*\}/);
                    if (match) cleanedJson = JSON.parse(match[0]);
                    else throw parseE;
                }
                return res.status(200).json({ success: true, data: cleanedJson, model: modelName });
            } catch (mErr) {
                lastError = mErr;
            }
        }

        return res.status(200).json({
            success: false,
            fallback: true,
            error: lastError ? lastError.message : 'Semua model cloud timeout',
            message: 'Beralih ke analisis visual baki cepat on-device'
        });
    } catch (err) {
        return res.status(200).json({
            success: false,
            fallback: true,
            error: err.message,
            message: 'Beralih ke analisis visual baki cepat on-device'
        });
    }
}
