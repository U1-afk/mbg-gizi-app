# PANDUAN DAN KONTEKS PROJEK AGENT ANTIGRAVITY (MBG GIZI APP)
# Disinkronkan langsung dari Google Gemini Web Chat (Link: https://share.gemini.google/p8PDEEmRR4Ag)
# Topik: MBG (Intelligent Multimedia Processing & Skripsi Mahasiswa)

---

## 🏛️ 1. Riset Payung Dosen
- **Judul Resmi Penelitian Payung:**  
  *“Pengembangan Sistem Terintegrasi Berbasis Kecerdasan Buatan untuk Estimasi dan Evaluasi Nilai Gizi dalam Mendukung Program Makan Bergizi Gratis (MBG)”*
- **Lokasi & Mitra Studi Kasus:** SPPG Kabupaten Bener Meriah, Aceh.
- **Basis Data Primer Kuesioner:** 66 responden pemangku kepentingan MBG di Aceh (Kepala SPPG, Ahli Gizi/S.Gz, Chef/Koki MBG, Operator dapur, dan Guru/PIC Sekolah).
- **Validasi Kualitas:** Divalidasi langsung oleh Ahli Gizi resmi SPPG Kabupaten Bener Meriah.
- **Target Luaran Akademik & Kebijakan:**
  1. Artikel Ilmiah di Jurnal Internasional Bereputasi (Terindeks Scopus min. Q3).
  2. *Policy Brief* untuk Pemda & Badan Gizi Nasional (BGN).
  3. Publikasi di Media Massa Cetak/Online.
  4. Berita Acara Sidang Kelulusan 3 Mahasiswa Tugas Akhir.

---

## 🎓 2. Pemetaan 3 Modul Tugas Akhir (TA) Mahasiswa

| Modul TA | Fokus Utama & Domain | Algoritma / Metode | Input Data | Output & Peran Sistem |
| :--- | :--- | :--- | :--- | :--- |
| **TA 1 (Mahasiswa 1)** | **Computer Vision Porsi Baki** | **YOLOv11** (Nano / Ultralytics) | Citra/Foto Baki MBG (2D Piksel) | Deteksi 5 kelas menu (*buah, lauk, makanan_pokok, sayur, susu*) dan estimasi gramasi porsi visual. |
| **TA 2 (Mahasiswa 2)** | **Nutrition Engine & Evaluasi AKG** | **Matematika Komputasi & Rule-Based** | Numerik Gramasi & Profil Personal | Konversi gramasi ke zat gizi (TKPI), hitung BMR (Schofield 1985), TDEE (PAL 1.55), porsi MBG 33% TDEE, & analisis gap gizi. |
| **TA 3 (Mahasiswa 3)** | **Klasifikasi Status Gizi Antropometri** | **K-Nearest Neighbors (KNN)** ($K=5$) | Tabular (Umur, JK, BB, TB, IMT) | Klasifikasi 5 kategori status gizi Kemenkes RI (Permenkes No. 2/2020) & WHO 2007 via *Weighted Normalized Euclidean Distance*. |

---

## 🧠 3. Model Machine Learning & Detail Teknis Aktif

1. **Klasifikasi Status Gizi Siswa (K-Nearest Neighbors / KNN):**
   - **Algoritma:** K-Nearest Neighbors (KNN) dengan $K = 5$.
   - **Metrik Jarak:** *Weighted Normalized Euclidean Distance* dengan bobot fitur: `[1.0, 0.5, 2.0, 1.5, 4.0]` pada `[Umur, Jenis Kelamin, Berat Badan, Tinggi Badan, IMT]`.
   - **Alasan Pemilihan KNN (bukan CNN / Random Forest):** Data tabular antropometri 4–5 kolom tidak memiliki relasi piksel/spasial sehingga CNN tidak tepat dan rentan *overfitting*. KNN terbukti intuitif, berakurasi tinggi, cepat dihitung, dan mudah dipertanggungjawabkan saat sidang skripsi.
   - **5 Kelas Standar Antropometri (Kemenkes Permenkes No. 2/2020 & WHO 2007):**
     1. Gizi Buruk (*Severely Underweight*)
     2. Gizi Kurang (*Underweight*)
     3. Normal / Gizi Baik (*Ideal*)
     4. Berisiko Gizi Lebih (*Overweight*)
     5. Obesitas (*Obese*)
   - **Lokasi Kode:** `app.js` (fungsi `classifyNutritionalStatusKNN`) & form `#rf-status-form` di `index.html`.

2. **Deteksi Visual Menu Baki MBG (YOLOv11):**
   - **Arsitektur:** YOLOv11 Nano (`yolo11n.pt`) dari Ultralytics (5.5 MB).
   - **Dataset:** 2.127 citra baki MBG teranotasi di `D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\results\dataset\`.
   - **5 Kelas Deteksi:** `buah`, `lauk`, `makanan_pokok`, `sayur`, `susu`.
   - **Performa Training (Google Colab Tesla T4, 30 Epochs):**
     - mAP@50: 99.2%
     - Precision: 96.7%
     - Recall: 100.0%
     - Bobot model tersimpan di Colab: `/content/training_mbg_baru/yolo11_mbg_asli/weights/best.pt`.

3. **Kalkulator Kebutuhan Energi & Dashboard Evaluasi Asupan Gizi:**
   - Menghitung BMR (Formula Schofield 1985 untuk usia 3–18 tahun), TEE (Faktor Aktivitas 1,55), target porsi makan siang MBG (33% TEE), dan distribusi makronutrien seimbang (60% Karbohidrat @ 4 kkal/g, 15% Protein @ 4 kkal/g, 25% Lemak @ 9 kkal/g).
   - Sinkronisasi otomatis real-time antara kalkulator manual TKPI, hasil deteksi baki, dan evaluasi nutrisi.

---

## ⚠️ 4. Aturan UI Hygiene (Penting untuk Jurnal & Laporan):
- DILARANG memunculkan teks: `TA 1`, `TA 2`, `TA 3`, `Sistem MBG Terpadu`, `YOLO`, `VLM`, `Random Forest`, `BMR/TDEE` di antarmuka web pengguna.
- Pertahankan seluruh 110 ID DOM JavaScript pada `app.js` dan `index.html`.
