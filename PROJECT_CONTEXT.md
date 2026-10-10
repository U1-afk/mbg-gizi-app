# PANDUAN DAN KONTEKS PROJEK AGENT ANTIGRAVITY (MBG GIZI APP)
# Disinkronkan dari Antigravity Conversation ID: 5f3b35d1-53c4-41e5-be53-bb39afcfe7cc

## 📌 Ringkasan Projek
Projek ini adalah **Media Interaktif Program Makan Bergizi Gratis (MBG)** berbasis Web dan Machine Learning/Computer Vision untuk penelitian publikasi jurnal ilmiah dosen dan mahasiswa (Mata Kuliah: Intelligent Multimedia Processing).

---

## 🎯 Topik & Judul Riset (Progress 1)
- **Judul Resmi:** Implementasi Computer Vision Berbasis Web Menggunakan Algoritma YOLOv11 untuk Deteksi Jenis Makanan pada Program Makan Bergizi Gratis (MBG)
- **Mahasiswa:** Dliyaul Haq (NPM: 2304111010099)
- **Kategori:** Intelligent Multimedia Processing (Visual Multimedia Deep Learning)

---

## 🧠 Model Machine Learning & Computer Vision Aktif

1. **Klasifikasi Status Gizi Siswa (K-Nearest Neighbors / KNN):**
   - **Algoritma:** K-Nearest Neighbors (KNN) dengan K = 5.
   - **Metrik Jarak:** Weighted Normalized Euclidean Distance dengan pembobotan fitur: [1.0, 0.5, 2.0, 1.5, 4.0] pada fitur [Umur, Jenis Kelamin, Berat Badan, Tinggi Badan, IMT].
   - **Standar Antropometri:** Kemenkes RI (Permenkes No. 2 Tahun 2020) & WHO 2007:
     1. Gizi Buruk (Severely Underweight)
     2. Gizi Kurang (Underweight)
     3. Normal / Gizi Baik (Ideal)
     4. Berisiko Gizi Lebih (Overweight)
     5. Obesitas (Obese)
   - **Lokasi Kode:** app.js (fungsi classifyNutritionalStatusKNN) & form rf-status-form di index.html.

2. **Deteksi Visual Menu Baki MBG (YOLOv11):**
   - **Arsitektur:** YOLOv11 Nano (yolo11n.pt) dari Ultralytics (5.5 MB).
   - **Dataset:** 2.127 citra baki MBG teranotasi di D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\results\dataset\.
   - **5 Kelas Deteksi:** buah, lauk, makanan_pokok, sayur, susu.
   - **Hasil Training di Google Colab (GPU Tesla T4, 30 Epochs):**
     - mAP@50: 99.2%
     - Precision: 96.7%
     - Recall: 100.0%
     - Bobot model tersimpan di Colab: /content/training_mbg_baru/yolo11_mbg_asli/weights/best.pt.

3. **Kalkulator Kebutuhan Energi & Dashboard Evaluasi Asupan Gizi:**
   - Menghitung BMR (Formula Schofield 1985 untuk usia 3–18 tahun), TEE (Faktor Aktivitas 1,55), target porsi makan siang MBG (33% TEE), dan distribusi makronutrien seimbang (60% Karbohidrat @ 4 kkal/g, 20% Protein @ 4 kkal/g, 20% Lemak @ 9 kkal/g).
   - Sinkronisasi otomatis antara profil siswa, hasil deteksi baki, dan evaluasi nutrisi.

---

## ⚠️ Aturan UI Hygiene (Penting untuk Jurnal & Laporan):
- DILARANG memunculkan teks: TA 1, TA 2, TA 3, Sistem MBG Terpadu, YOLO, VLM, Random Forest, BMR/TDEE di antarmuka web.
- Pertahankan seluruh 110 ID DOM JavaScript pada app.js dan index.html.
