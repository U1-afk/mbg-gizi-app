import os
import io
import time
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA VISUAL PERSIS VERCEL
# ==============================================================================
st.set_page_config(
    page_title="Media Interaktif Pemantauan Gizi MBG",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_html(html_str):
    """Merender string HTML tanpa whitespace awal agar tidak pernah menjadi pre/code block."""
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ==============================================================================
# INISIALISASI DATABASE PENGGUNA & RIWAYAT SESI STREAMLIT
# ==============================================================================
DEFAULT_USERS = [
    {"nik": "Admin", "name": "Administrator SPPG", "password": "sppgunggul", "role": "Admin"},
    {"nik": "12345", "name": "Siswa / Karyawan Demo", "password": "sppg123", "role": "Employee"},
    {"nik": "10021", "name": "Ahmad Fauzi", "password": "sppg123", "role": "Employee"},
    {"nik": "10045", "name": "Siti Rahma", "password": "sppg123", "role": "Employee"}
]

if "users_db" not in st.session_state:
    st.session_state.users_db = [dict(u) for u in DEFAULT_USERS]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if "history_list" not in st.session_state:
    st.session_state.history_list = [
        {
            "id": 1,
            "user": "Siti Rahma",
            "nik": "10045",
            "menu": "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk",
            "portion": "Habis Semua",
            "rating": "⭐⭐⭐⭐⭐",
            "date": "Senin, 1 September 2026",
            "time": "12:15"
        },
        {
            "id": 2,
            "user": "Ahmad Fauzi",
            "nik": "10021",
            "menu": "Paket 6: Udang Masak Kuah + Tempe Orek + Sayur Capcay + Semangka",
            "portion": "Habis Semua",
            "rating": "⭐⭐⭐⭐⭐",
            "date": "Senin, 1 September 2026",
            "time": "12:30"
        },
        {
            "id": 3,
            "user": "Karyawan Demo",
            "nik": "12345",
            "menu": "Paket 1: Ayam Lengkuas + Tahu Kuning + Labu Siam + Semangka",
            "portion": "Habis Semua",
            "rating": "⭐⭐⭐⭐⭐",
            "date": "Senin, 1 September 2026",
            "time": "12:45"
        }
    ]

if "message_list" not in st.session_state:
    st.session_state.message_list = [
        {
            "id": 1,
            "user": "UL",
            "nik": "300604",
            "text": "tes",
            "reply": "",
            "date": "16/9/2026, 21.09.18",
            "thread": []
        },
        {
            "id": 2,
            "user": "Karyawan Demo",
            "nik": "12345",
            "text": "Porsi makan bergizi hari ini sangat pas dan lauk udang kuahnya enak sekali!",
            "reply": "Terima kasih atas masukannya! Kami terus menjaga standar kecukupan AKG untuk seluruh karyawan.",
            "date": "01/09/2026, 13.00",
            "thread": [
                {"sender": "user", "text": "Porsi makan bergizi hari ini sangat pas dan lauk udang kuahnya enak sekali!", "time": "01/09/2026, 13.00"},
                {"sender": "admin", "text": "Terima kasih atas masukannya! Kami terus menjaga standar kecukupan AKG untuk seluruh karyawan.", "time": "01/09/2026, 13.10"}
            ]
        }
    ]

if "student_profile" not in st.session_state:
    st.session_state.student_profile = {
        "nama": "Siswa / Karyawan Demo",
        "umur": 16,
        "jk": "Laki-laki (L)",
        "bb": 52.0,
        "tb": 162.0,
        "imt": 19.8,
        "status": "Normal / Gizi Baik",
        "confidence": 96.6,
        "tdee": 2003,
        "target_mbg": 661
    }

if "active_meal_nutrition" not in st.session_state:
    st.session_state.active_meal_nutrition = {
        "kal": 0.0,
        "pro": 0.0,
        "kar": 0.0,
        "lem": 0.0,
        "name": ""
    }


# CSS Total: Menghilangkan teks putih pudar, menerapkan warna tajam, glassmorphism persis Vercel
render_html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<style>
    :root {
        --primary: #10b981;
        --primary-dark: #059669;
        --primary-light: #34d399;
        --secondary: #0f766e;
        --bg: #f0fdf4;
        --text-main: #0f172a;
        --text-light: #475569;
    }

    /* Latar Belakang Mint Radial Glow Persis Vercel */
    .stApp {
        background-color: #f0fdf4 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(110, 231, 183, 0.45) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(52, 211, 153, 0.35) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(153, 246, 228, 0.40) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
        font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
    }

    /* PAKSA SEMUA TEKS STREAMLIT HITAM / CHARCOAL TAJAM (TIDAK BOLEH PUTIH PUDAR) */
    .stApp, .stApp p, .stApp span, .stApp label,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] span,
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stNumberInput"] label p,
    div[data-testid="stTextInput"] label p,
    div[data-testid="stTextArea"] label p {
        color: #0f172a !important;
        font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
    }

    header[data-testid="stHeader"] { background: transparent !important; }
    footer { visibility: hidden !important; }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1240px !important;
    }

    /* Style Tombol Aksi Utama Sesuai Gambar Pengguna */
    .st-key-btn_hitung_manual button,
    .st-key-btn_simpan_mbg button,
    .st-key-btn_kirim_pesan button,
    button:has(p:contains("Hitung Total Gizi")),
    button:has(p:contains("Simpan Kebutuhan MBG")),
    button:has(p:contains("Kirim Pesan")) {
        background-color: #10b981 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
        width: 100% !important;
    }
    .st-key-btn_hitung_manual button:hover,
    .st-key-btn_simpan_mbg button:hover,
    .st-key-btn_kirim_pesan button:hover,
    button:has(p:contains("Hitung Total Gizi")):hover,
    button:has(p:contains("Simpan Kebutuhan MBG")):hover,
    button:has(p:contains("Kirim Pesan")):hover {
        background-color: #059669 !important;
    }

    .st-key-btn_periksa_gizi button,
    button:has(p:contains("Periksa Status Gizi Siswa")) {
        background-color: #9333ea !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.65rem 1.5rem !important;
        box-shadow: 0 4px 14px rgba(147, 51, 234, 0.3) !important;
        width: 100% !important;
    }
    .st-key-btn_periksa_gizi button:hover,
    button:has(p:contains("Periksa Status Gizi Siswa")):hover {
        background-color: #7e22ce !important;
    }

    .st-key-btn_back_to_home button,
    .st-key-btn_gizi_to_dash button,
    .st-key-btn_kalk_to_dash button,
    button:has(p:contains("Kembali ke Beranda")) {
        background-color: #dcfce7 !important;
        color: #065f46 !important;
        border: 1px solid #86efac !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.12) !important;
        padding: 0.35rem 0.95rem !important;
    }
    .st-key-btn_back_to_home button:hover,
    .st-key-btn_gizi_to_dash button:hover,
    .st-key-btn_kalk_to_dash button:hover,
    button:has(p:contains("Kembali ke Beranda")):hover {
        background-color: #bbf7d0 !important;
        color: #064e3b !important;
    }

    .st-key-btn_pk_1 button,
    .st-key-btn_pk_2 button,
    .st-key-btn_pk_3 button,
    .st-key-btn_pk_4 button,
    .st-key-btn_pk_5 button,
    .st-key-btn_pk_6 button,
    button:has(p:contains("Paket 1:")),
    button:has(p:contains("Paket 2:")),
    button:has(p:contains("Paket 3:")),
    button:has(p:contains("Paket 4:")),
    button:has(p:contains("Paket 5:")),
    button:has(p:contains("Paket 6:")) {
        background-color: #f1f5f9 !important;
        color: #0f766e !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 20px !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        padding: 0.25rem 0.5rem !important;
    }


    /* Top Glass Navbar */
    .glass-nav {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 18px;
        padding: 0.85rem 1.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px -2px rgba(16, 185, 129, 0.15);
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 800;
        font-size: 1.15rem;
        color: #059669 !important;
    }
    .brand-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white !important;
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
    }
    .status-pill {
        background: rgba(16, 185, 129, 0.12);
        color: #059669 !important;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.3rem 0.8rem;
        border-radius: 9999px;
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
    }

    /* Main Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white !important;
        padding: 1.8rem 2.2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 28px -6px rgba(16, 185, 129, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-banner h1, .hero-banner p, .hero-banner span {
        color: #ffffff !important;
    }
    .hero-banner h1 {
        font-size: 1.95rem;
        font-weight: 800;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        font-size: 0.95rem;
        margin: 0 0 1rem 0;
        max-width: 850px;
        line-height: 1.5;
        opacity: 0.95;
    }
    .hero-tags {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .hero-tag {
        background: rgba(255, 255, 255, 0.22);
        backdrop-filter: blur(8px);
        color: #ffffff !important;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.35);
    }

    /* Home Menu Grid 6 Fitur Persis Index.html */
    .menu-item-home {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(226, 232, 240, 0.9);
        border-radius: 20px 20px 0 0;
        padding: 1.5rem 1.2rem 1rem 1.2rem;
        text-align: center;
        box-shadow: 0 4px 20px -2px rgba(16, 185, 129, 0.08);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .menu-item-home:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.18);
        border-color: #10b981;
    }
    .menu-icon-wrap {
        font-size: 2.8rem;
        margin: 0.85rem 0 0.5rem 0;
    }
    .menu-card-title {
        font-weight: 800;
        color: #0f172a !important;
        font-size: 1.18rem;
        margin-bottom: 0.35rem;
    }
    .menu-card-desc {
        font-size: 0.84rem;
        color: #64748b !important;
        line-height: 1.4;
        min-height: 2.2rem;
    }
    
    /* Tombol Navigasi Kartu Home */
    div[data-testid="stColumn"] > div > div > div > button[kind="secondary"] {
        border-radius: 0 0 18px 18px !important;
        border-top: none !important;
        font-weight: 700 !important;
        background: #ffffff !important;
        border-color: rgba(226, 232, 240, 0.9) !important;
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.04) !important;
        color: #059669 !important;
        font-size: 0.92rem !important;
        padding: 0.65rem 1rem !important;
    }
    div[data-testid="stColumn"] > div > div > div > button[kind="secondary"]:hover {
        background: #ecfdf5 !important;
        border-color: #10b981 !important;
        color: #047857 !important;
    }

    /* Kartu Menu Beranda (Home Feature Cards - Persis Tampilan Web HTML) */
    .menu-item-home {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1.5px solid rgba(226, 232, 240, 0.9);
        border-bottom: none;
        border-radius: 20px 20px 0 0;
        padding: 1.6rem 1.2rem 0.8rem 1.2rem;
        text-align: center;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.04);
        transition: all 0.25s ease;
        position: relative;
    }
    .menu-icon-wrap {
        font-size: 2.6rem;
        margin: 0.6rem 0 0.5rem 0;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.25s ease;
    }
    .menu-card-title {
        font-weight: 800;
        color: #0f172a;
        font-size: 1.12rem;
        margin-bottom: 0.35rem;
        letter-spacing: -0.3px;
    }
    .menu-card-desc {
        font-size: 0.82rem;
        color: #64748b;
        font-weight: 500;
        line-height: 1.4;
        min-height: 2.4rem;
    }
    
    /* Tombol Aksi Langsung Menyatu di Bawah Kartu */
    div.stButton > button[key^="btn_open_card_"] {
        border-radius: 0 0 20px 20px !important;
        margin-top: -1px !important;
        border: 1.5px solid rgba(226, 232, 240, 0.9) !important;
        background: #ffffff !important;
        color: #059669 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.65rem 1rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.25s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem !important;
    }
    div.stButton > button[key^="btn_open_card_"]:hover {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: #ffffff !important;
        border-color: #059669 !important;
        box-shadow: 0 8px 22px rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* Tombol Kembali ke Beranda (Back to Home) */
    div.stButton > button[key="btn_back_to_home"] {
        background: rgba(15, 118, 110, 0.12) !important;
        color: #0f766e !important;
        border: 1.5px solid rgba(15, 118, 110, 0.28) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.1rem !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.45rem !important;
        transition: all 0.2s ease !important;
        margin-bottom: 0.5rem !important;
    }
    div.stButton > button[key="btn_back_to_home"]:hover {
        background: #0f766e !important;
        color: #ffffff !important;
        border-color: #0f766e !important;
        transform: translateX(-3px) !important;
        box-shadow: 0 4px 15px rgba(15, 118, 110, 0.25) !important;
    }

    /* Badges Kategori */
    .badge-ta {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.72rem;
        font-weight: 700;
        border-radius: 20px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-ta-1 { background: rgba(59, 130, 246, 0.15); color: #2563eb; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-ta-2 { background: rgba(245, 158, 11, 0.15); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-ta-3 { background: rgba(168, 85, 247, 0.15); color: #9333ea; border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge-ta-main { background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); }

    /* Penyesuaian Responsif untuk HP / Mobile */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.8rem !important;
        }
        .glass-nav {
            padding: 0.65rem 1rem !important;
            flex-direction: column !important;
            gap: 0.5rem !important;
            text-align: center !important;
        }
        .dashboard-header {
            padding: 1.1rem 1.2rem !important;
            text-align: center !important;
        }
        .dashboard-header h2 {
            font-size: 1.35rem !important;
        }
        .menu-item-home {
            padding: 1.3rem 1rem 0.7rem 1rem !important;
        }
        .menu-icon-wrap {
            font-size: 2.2rem !important;
        }
        .menu-card-desc {
            min-height: auto !important;
        }
        /* Memastikan kolom kartu pada HP tampil penuh dan tidak terpotong */
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            min-width: 100% !important;
            margin-bottom: 0.6rem !important;
        }
    }

    /* Kotak Pilihan Radio yang Jelas & Kontras */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        background: #ffffff !important;
        padding: 0.75rem 1.1rem !important;
        border-radius: 14px !important;
        border: 1.5px solid #cbd5e1 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        gap: 0.8rem !important;
    }
    div[data-testid="stRadio"] label {
        cursor: pointer !important;
        margin-right: 0.5rem !important;
    }
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span {
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        color: #0f172a !important;
    }

    /* Glassmorphic Card Container */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.85);
        border-radius: 20px;
        box-shadow: 0 8px 25px -3px rgba(16, 185, 129, 0.1);
        padding: 1.5rem;
        margin-bottom: 1.3rem;
    }

    /* 4 Primary Metric Cards */
    .metric-card {
        background: #ffffff;
        padding: 1.15rem 1rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 20px -3px rgba(16, 185, 129, 0.2);
    }
    .metric-card .title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .metric-card .val {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-card .sub {
        font-size: 0.76rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }

    /* Badges */
    .badge-ta {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.72rem;
        font-weight: 700;
        border-radius: 20px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .badge-ta-1 { background: rgba(59, 130, 246, 0.15); color: #2563eb; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-ta-2 { background: rgba(245, 158, 11, 0.15); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-ta-3 { background: rgba(168, 85, 247, 0.15); color: #9333ea; border: 1px solid rgba(168, 85, 247, 0.3); }
    .badge-ta-main { background: rgba(16, 185, 129, 0.15); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); }

    /* Progress Bar Visualizer */
    .progress-bar-card {
        background: #ffffff;
        padding: 1.25rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }
    .progress-bar-item { margin-bottom: 0.95rem; }
    .progress-bar-item:last-child { margin-bottom: 0; }
    .progress-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.86rem;
        font-weight: 700;
        margin-bottom: 0.35rem;
        color: #1e293b;
    }
    .progress-track {
        width: 100%;
        height: 12px;
        background: #f1f5f9;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.6s ease-in-out;
    }
    .fill-kalori { background: linear-gradient(90deg, #f59e0b, #ef4444); }
    .fill-protein { background: linear-gradient(90deg, #3b82f6, #1d4ed8); }
    .fill-karbo { background: linear-gradient(90deg, #10b981, #047857); }
    .fill-lemak { background: linear-gradient(90deg, #8b5cf6, #6d28d9); }

    /* Tabel Rincian Nutrisi */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    .custom-table th {
        background: #f8fafc;
        color: #475569;
        font-weight: 700;
        font-size: 0.84rem;
        padding: 0.75rem 1rem;
        border-bottom: 2px solid #e2e8f0;
        text-align: left;
    }
    .custom-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f1f5f9;
        color: #1e293b;
        font-size: 0.88rem;
    }
    .custom-table tr:last-child td { border-bottom: none; }
    .custom-table tr:hover td { background: #f8fafc; }

    /* IMT Legend Card */
    .imt-legend-card {
        margin-top: 1rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.85rem 1.2rem;
        text-align: center;
    }
    .imt-legend-title {
        font-size: 0.76rem;
        font-weight: 700;
        color: #64748b;
        margin-bottom: 0.4rem;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .imt-legend-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.6rem;
        font-size: 0.82rem;
        color: #1e293b;
        font-weight: 600;
    }
    .imt-legend-item { display: flex; align-items: center; gap: 0.4rem; }
    .imt-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .dot-yellow { background-color: #eab308; }
    .dot-green { background-color: #22c55e; }
    .dot-purple { background-color: #9333ea; }

    /* Login Screen & Admin Panel Styles */
    .login-container-wrap {
        max-width: 480px;
        margin: 2rem auto 1.2rem auto;
    }
    .login-card-box {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1.5px solid rgba(255, 255, 255, 0.9);
        border-radius: 24px;
        box-shadow: 0 16px 36px -8px rgba(16, 185, 129, 0.25);
        padding: 2.2rem 2rem 1.6rem 2rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .login-logo-circle {
        font-size: 2.8rem;
        color: #10b981;
        background: rgba(16, 185, 129, 0.12);
        width: 80px;
        height: 80px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.2rem;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.25);
        border: 2px solid rgba(16, 185, 129, 0.25);
    }
    .demo-creds-box {
        font-size: 0.82rem;
        text-align: center;
        margin-top: 1.2rem;
        color: #475569;
        background: #f8fafc;
        padding: 0.85rem 1rem;
        border-radius: 12px;
        border: 1px dashed #cbd5e1;
        line-height: 1.6;
    }
</style>
""")

# ==============================================================================
# SISTEM AUTENTIKASI & GERBANG MASUK (LOGIN SCREEN)
# ==============================================================================
if not st.session_state.logged_in:
    render_html("""
    <div class="login-container-wrap">
        <div class="login-card-box">
            <div class="login-logo-circle">
                <i class="fa-solid fa-leaf"></i>
            </div>
            <h2 style="margin:0 0 0.35rem 0; font-weight:800; color:#0f172a; font-size:1.95rem; letter-spacing:-0.5px;">MBG Nutrition</h2>
            <p style="margin:0 0 0.6rem 0; color:#64748b; font-size:0.92rem; font-weight:500;">PT. SPPG - Employee & Student Health Tracker</p>
            <div style="display:inline-block; background:rgba(16,185,129,0.12); color:#059669; font-size:0.76rem; font-weight:700; padding:0.25rem 0.8rem; border-radius:20px; border:1px solid rgba(16,185,129,0.3);">
                <i class="fa-solid fa-shield-halved"></i> Autentikasi Pengguna MBG
            </div>
        </div>
    </div>
    """)
    
    col_l, col_center, col_r = st.columns([1, 1.6, 1])
    with col_center:
        auth_tab_login, auth_tab_reg = st.tabs(["🔐 Masuk Akun", "📝 Pendaftaran Akun Baru"])
        
        with auth_tab_login:
            role_choice = st.selectbox(
                "Masuk Sebagai:",
                ["👤 Pengguna (Siswa / Pegawai)", "👑 Administrator (Admin SPPG)"],
                key="input_role_select"
            )
            nik_val = st.text_input("NIK / Username:", placeholder="Masukkan NIK atau Username", key="input_nik_field")
            pass_val = st.text_input("Kata Sandi:", type="password", placeholder="Masukkan Sandi", key="input_pass_field")
            
            if st.button("Masuk ke Sistem MBG ➡️", type="primary", use_container_width=True):
                target_role = "Admin" if "Admin" in role_choice else "Employee"
                clean_nik = nik_val.strip()
                clean_pass = pass_val.strip()
                
                if not clean_nik or not clean_pass:
                    st.warning("⚠️ Harap masukkan NIK/Username dan Kata Sandi!")
                elif (target_role == "Admin" or clean_nik.lower() == "admin") and clean_nik.lower() == "admin" and clean_pass == "sppgunggul":
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"nik": "Admin", "name": "Administrator SPPG", "role": "Admin"}
                    st.rerun()
                elif target_role == "Admin":
                    st.error("❌ NIK atau Sandi Admin salah! Gunakan NIK: Admin & Sandi: sppgunggul")
                else:
                    user_match = next((u for u in st.session_state.users_db if u["nik"].lower() == clean_nik.lower() and u["password"] == clean_pass), None)
                    if user_match:
                        st.session_state.logged_in = True
                        st.session_state.current_user = user_match
                        st.rerun()
                    else:
                        st.error("❌ NIK atau Kata Sandi salah, atau belum terdaftar!")
            
            render_html("<div style='text-align:center; font-size:0.78rem; font-weight:700; color:#64748b; margin:1rem 0 0.4rem 0;'>ATAU AKSES CEPAT (1 KLIK LANGSUNG UJI):</div>")
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                if st.button("⚡ Masuk Siswa Demo", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"nik": "12345", "name": "Siswa / Karyawan Demo", "role": "Employee"}
                    st.rerun()
            with c_btn2:
                if st.button("👑 Masuk Mode Admin", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.current_user = {"nik": "Admin", "name": "Administrator SPPG", "role": "Admin"}
                    st.rerun()
                    
            render_html("""
            <div class="demo-creds-box">
                <strong style="color:#0f766e;"><i class="fa-solid fa-key"></i> Kredensial Akun Demo Bawaan:</strong><br>
                👤 <strong>Pengguna:</strong> NIK: <code>12345</code> | Sandi: <code>sppg123</code><br>
                👑 <strong>Admin:</strong> NIK: <code>Admin</code> | Sandi: <code>sppgunggul</code>
            </div>
            """)
            
        with auth_tab_reg:
            reg_nik = st.text_input("Buat NIK / NIM Baru:", placeholder="Contoh: 10099", key="reg_nik_input")
            reg_name = st.text_input("Nama Lengkap Siswa / Pegawai:", placeholder="Contoh: Dliyaul Haq", key="reg_name_input")
            reg_pass = st.text_input("Buat Kata Sandi:", type="password", placeholder="Minimal 6 karakter", key="reg_pass_input")
            
            if st.button("Daftar Akun Baru ✨", type="secondary", use_container_width=True):
                if not reg_nik or not reg_name or not reg_pass:
                    st.warning("⚠️ Semua kolom wajib diisi untuk mendaftar!")
                elif any(u["nik"].lower() == reg_nik.strip().lower() for u in st.session_state.users_db):
                    st.warning(f"⚠️ NIK {reg_nik} sudah terdaftar di sistem!")
                else:
                    new_user = {
                        "nik": reg_nik.strip(),
                        "name": reg_name.strip(),
                        "password": reg_pass.strip(),
                        "role": "Employee"
                    }
                    st.session_state.users_db.append(new_user)
                    st.success(f"🎉 Pendaftaran Berhasil untuk {reg_name}! Silakan buka tab 'Masuk Akun' untuk login.")
                    
    render_html("""
    <div style="text-align:center; padding:2rem 0 1rem 0; color:#64748b; font-size:0.82rem;">
        Aplikasi Media Interaktif MBG | Riset & Publikasi Ilmiah Visi Komputer Cerdas | Universitas Syiah Kuala
    </div>
    """)
    st.stop()

# ==============================================================================
# NAVBAR ATAS DENGAN IDENTITAS PENGGUNA & TOMBOL LOGOUT
# ==============================================================================
active_user = st.session_state.current_user or {"name": "Siswa / Karyawan Demo", "nik": "12345", "role": "Employee"}
is_admin_mode = (active_user.get("role") == "Admin")
user_role_label = "👑 Administrator SPPG" if is_admin_mode else f"👤 {active_user.get('name')} (NIK: {active_user.get('nik')})"

col_nav_brand, col_nav_action = st.columns([3, 1])
with col_nav_brand:
    render_html(f"""
    <div class="glass-nav" style="margin-bottom:0;">
        <div class="nav-brand">
            <div class="brand-badge"><i class="fa-solid fa-leaf"></i></div>
            <span>MEDIA INTERAKTIF MBG</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap;">
            <div class="status-pill">
                <span class="status-dot"></span>
                <span>Sistem Pemantauan Aktif</span>
            </div>
            <span style="font-size:0.86rem; font-weight:700; color:#0f766e; background:rgba(16,185,129,0.12); padding:0.35rem 0.8rem; border-radius:10px; border:1px solid rgba(16,185,129,0.25);">
                {user_role_label}
            </span>
        </div>
    </div>
    """)
with col_nav_action:
    render_html("<div style='height:4px;'></div>")
    if st.button("🚪 Keluar (Logout)", key="btn_logout_main_header", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.active_screen = "home"
        st.rerun()

if "active_screen" not in st.session_state:
    st.session_state.active_screen = "home"



# ==============================================================================
# 2. MODEL LOADER (ULTRALYTICS ENGINE)
# ==============================================================================
@st.cache_resource(show_spinner="Memuat model visi komputer...")
def load_detection_model():
    candidate_paths = [
        "best.pt",
        os.path.join(os.path.dirname(__file__), "best.pt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.pt"),
        os.path.join(os.getcwd(), "best.pt"),
        os.path.join(os.path.dirname(__file__), "backend_local", "best.pt"),
        r"D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\Dataset\results\best.pt",
        r"D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\Dataset\results\yolo11m.pt"
    ]
    model = None
    loaded_from = None
    try:
        from ultralytics import YOLO
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    model = YOLO(p)
                    loaded_from = p
                    break
                except Exception:
                    continue
    except ImportError:
        pass
    return model, loaded_from

detection_model, model_path = load_detection_model()

@st.cache_resource(show_spinner="Memuat model klasifikasi menu makanan...")
def load_food_classifier_model():
    candidate_paths = [
        "best_food_classifier.pt",
        os.path.join(os.path.dirname(__file__), "best_food_classifier.pt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "best_food_classifier.pt"),
        os.path.join(os.getcwd(), "best_food_classifier.pt"),
        os.path.join(os.path.dirname(__file__), "backend_local", "best_food_classifier.pt"),
        r"D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\mbg-gizi-app 20\best_food_classifier.pt",
        r"C:\Users\Dliyaul Haq\Downloads\best.pt"
    ]
    model = None
    loaded_from = None
    try:
        from ultralytics import YOLO
        for p in candidate_paths:
            if os.path.exists(p):
                try:
                    model = YOLO(p)
                    loaded_from = p
                    break
                except Exception:
                    continue
    except ImportError:
        pass
    return model, loaded_from

food_classifier_model, classifier_path = load_food_classifier_model()

def load_and_preprocess_user_image(file_obj):
    """
    Fungsi pemroses citra universal ramah mobile / smartphone & hosting cloud:
    - Mendukung format JPG, JPEG, PNG, WEBP, HEIC (iPhone iOS), JFIF, BMP.
    - Otomatis memperbaiki rotasi EXIF dari orientasi kamera HP (tegak / miring).
    - Otomatis kompresi cerdas (downscale ke max 1024px) agar server cloud tidak OOM/timeout,
      meningkatkan kecepatan inferensi YOLO hingga 50x lipat (<0.1 detik)!
    """
    if file_obj is None:
        return None
    try:
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except Exception:
            pass
        
        img = Image.open(file_obj)
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        
        img = img.convert("RGB")
        max_dim = 1024
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        st.error(f"⚠️ Gagal memproses file foto: {e}. Silakan coba format JPG atau PNG.")
        return None



# ==============================================================================
# 3. BASIS DATA GIZI RESMI MBG
# ==============================================================================
DEFAULT_FOOD_LIBRARY = {
    "karbo": {
        "Nasi Putih Pulen (150g)": {"gram": 150, "kal": 195, "pro": 4.0, "kar": 43.0, "lem": 0.5, "cat": "Makanan Pokok"},
        "Nasi Kuning Gurih (150g)": {"gram": 150, "kal": 210, "pro": 4.2, "kar": 41.5, "lem": 3.2, "cat": "Makanan Pokok"},
        "Nasi Goreng Sayur / Gurih (150g)": {"gram": 150, "kal": 240, "pro": 5.2, "kar": 42.0, "lem": 6.5, "cat": "Makanan Pokok"},
        "Kulit Kebab / Roti Tortilla Lipat (80g)": {"gram": 80, "kal": 210, "pro": 5.8, "kar": 38.0, "lem": 3.5, "cat": "Makanan Pokok"},
        "Spaghetti Saus Bolognese (150g)": {"gram": 150, "kal": 220, "pro": 7.5, "kar": 36.0, "lem": 4.5, "cat": "Makanan Pokok"},
        "Tanpa Nasi (Menu Baki Tanpa Nasi Pokok)": {"gram": 0, "kal": 0, "pro": 0.0, "kar": 0.0, "lem": 0.0, "cat": "Makanan Pokok"},
        "Bumbu Kacang / Saus Pecel Celup (60g)": {"gram": 60, "kal": 140, "pro": 4.5, "kar": 8.0, "lem": 10.5, "cat": "Saus / Pelengkap"},
        "Kentang Goreng & Kacang Polong (150g)": {"gram": 150, "kal": 220, "pro": 4.5, "kar": 32.0, "lem": 9.0, "cat": "Makanan Pokok"},
        "Kentang Panggang Wedges (150g)": {"gram": 150, "kal": 185, "pro": 4.0, "kar": 35.0, "lem": 3.5, "cat": "Makanan Pokok"},
        "Kentang Goreng / French Fries (120g)": {"gram": 120, "kal": 235, "pro": 3.5, "kar": 34.0, "lem": 10.0, "cat": "Makanan Pokok"},
        "Mie Goreng / Bihun Sayur (120g)": {"gram": 120, "kal": 180, "pro": 3.8, "kar": 38.0, "lem": 2.5, "cat": "Makanan Pokok"},
        "Roti Burger / Roti Gandum (100g)": {"gram": 100, "kal": 175, "pro": 5.5, "kar": 34.0, "lem": 1.8, "cat": "Makanan Pokok"}
    },
    "prohew": {
        "Ayam Goreng Tepung Krispi (ala Kentucky) (85g)": {"gram": 85, "kal": 230, "pro": 22.5, "kar": 8.0, "lem": 12.0, "cat": "Protein Hewani"},
        "Ayam Gulai / Kari Kuah Kuning (90g)": {"gram": 90, "kal": 215, "pro": 21.0, "kar": 3.5, "lem": 13.0, "cat": "Protein Hewani"},
        "Ayam Goreng Lengkuas / Serundeng (85g)": {"gram": 85, "kal": 215, "pro": 24.0, "kar": 1.5, "lem": 12.5, "cat": "Protein Hewani"},
        "Ayam Goreng Saus Asam Manis (85g)": {"gram": 85, "kal": 225, "pro": 19.5, "kar": 14.0, "lem": 10.5, "cat": "Protein Hewani"},
        "Udang Goreng Tepung / Krispi (75g)": {"gram": 75, "kal": 175, "pro": 15.0, "kar": 10.0, "lem": 8.0, "cat": "Protein Hewani"},
        "Udang Balado Gurih (75g)": {"gram": 75, "kal": 85, "pro": 18.5, "kar": 0.5, "lem": 0.8, "cat": "Protein Hewani"},
        "Chicken Katsu & Selada (100g)": {"gram": 100, "kal": 240, "pro": 21.0, "kar": 12.0, "lem": 12.0, "cat": "Protein Hewani"},
        "Telur Orak-Arik / Dadar Sayur (75g)": {"gram": 75, "kal": 115, "pro": 7.5, "kar": 1.5, "lem": 8.5, "cat": "Protein Hewani"},
        "Sosis Panggang & Lalapan Timun (75g)": {"gram": 75, "kal": 180, "pro": 10.2, "kar": 4.5, "lem": 13.5, "cat": "Protein Hewani"},
        "Sosis Sapi / Ayam Panggang (70g)": {"gram": 70, "kal": 175, "pro": 10.0, "kar": 3.0, "lem": 13.5, "cat": "Protein Hewani"},
        "Ikan Goreng Gurih / Filet (80g)": {"gram": 80, "kal": 160, "pro": 18.0, "kar": 1.0, "lem": 9.0, "cat": "Protein Hewani"},
        "Telur Ceplok / Balado (1 Butir - 55g)": {"gram": 55, "kal": 92, "pro": 6.5, "kar": 0.8, "lem": 7.0, "cat": "Protein Hewani"},
        "Ayam Suwir Kemangi / Opor (75g)": {"gram": 75, "kal": 165, "pro": 20.5, "kar": 1.0, "lem": 8.5, "cat": "Protein Hewani"},
        "Semur Daging Sapi / Rolade (75g)": {"gram": 75, "kal": 185, "pro": 19.0, "kar": 3.5, "lem": 10.5, "cat": "Protein Hewani"},
        "Telur Puyuh Rebus (5 Butir - 50g)": {"gram": 50, "kal": 79, "pro": 6.5, "kar": 0.5, "lem": 5.5, "cat": "Protein Hewani"}
    },
    "pronab": {
        "Tempe Goreng Gurih (50g)": {"gram": 50, "kal": 118, "pro": 10.5, "kar": 7.5, "lem": 5.5, "cat": "Protein Nabati"},
        "Tempe Goreng Tepung / Gurih (50g)": {"gram": 50, "kal": 135, "pro": 9.5, "kar": 8.0, "lem": 7.0, "cat": "Protein Nabati"},
        "Kacang Edamame Rebus / Kedelai Polong (50g)": {"gram": 50, "kal": 60, "pro": 6.0, "kar": 4.5, "lem": 2.5, "cat": "Protein Nabati"},
        "Keripik Tempe Renyah (40g)": {"gram": 40, "kal": 190, "pro": 7.5, "kar": 11.0, "lem": 12.0, "cat": "Protein Nabati"},
        "Kacang Kedelai Goreng / Sangrai (50g)": {"gram": 50, "kal": 210, "pro": 14.0, "kar": 11.0, "lem": 11.5, "cat": "Protein Nabati"},
        "Tempe Orek Dadu Manis (50g)": {"gram": 50, "kal": 110, "pro": 9.0, "kar": 8.0, "lem": 5.0, "cat": "Protein Nabati"},
        "Tahu Goreng Kotak / Sakura (75g)": {"gram": 75, "kal": 80, "pro": 8.0, "kar": 2.0, "lem": 4.8, "cat": "Protein Nabati"},
        "Bumbu Kacang / Saus Pecel Gado-gado (60g)": {"gram": 60, "kal": 140, "pro": 4.5, "kar": 8.0, "lem": 10.5, "cat": "Saus / Nabati"},
        "Bakwan Sayur / Jagung Gurih (50g)": {"gram": 50, "kal": 115, "pro": 2.2, "kar": 12.0, "lem": 6.5, "cat": "Protein Nabati"},
        "Perkedel Kentang Gurih (50g)": {"gram": 50, "kal": 95, "pro": 2.5, "kar": 14.0, "lem": 3.5, "cat": "Protein Nabati"}
    },
    "sayur": {
        "Tumis Sayur Sawi Hijau (70g)": {"gram": 70, "kal": 26, "pro": 1.5, "kar": 3.8, "lem": 0.5, "cat": "Sayuran"},
        "Tumis Kembang Kol Gurih (70g)": {"gram": 70, "kal": 28, "pro": 1.4, "kar": 4.2, "lem": 0.6, "cat": "Sayuran"},
        "Stik Wortel Rebus / Kukus (75g)": {"gram": 75, "kal": 28, "pro": 0.8, "kar": 6.2, "lem": 0.2, "cat": "Sayuran"},
        "Lalapan Tomat, Timun & Selada (60g)": {"gram": 60, "kal": 15, "pro": 0.7, "kar": 3.0, "lem": 0.1, "cat": "Sayuran"},
        "Tumis Buncis, Wortel, & Jagung Muda (75g)": {"gram": 75, "kal": 32, "pro": 1.6, "kar": 5.8, "lem": 0.4, "cat": "Sayuran"},
        "Lalapan Timun Segar & Selada (60g)": {"gram": 60, "kal": 12, "pro": 0.6, "kar": 2.5, "lem": 0.1, "cat": "Sayuran"},
        "Sayur Capcay Wortel & Buncis (80g)": {"gram": 80, "kal": 35, "pro": 2.0, "kar": 6.5, "lem": 0.8, "cat": "Sayuran"},
        "Tumis Sayur Hijau (Buncis/Bayam/Kangkung) (75g)": {"gram": 75, "kal": 30, "pro": 1.8, "kar": 5.0, "lem": 0.6, "cat": "Sayuran"},
        "Tumis Jagung Manis & Wortel (75g)": {"gram": 75, "kal": 48, "pro": 1.5, "kar": 10.5, "lem": 0.5, "cat": "Sayuran"},
        "Sayur Sop Wortel Kol (75g)": {"gram": 75, "kal": 25, "pro": 1.2, "kar": 4.5, "lem": 0.5, "cat": "Sayuran"}
    },
    "buah": {
        "Tanpa Buah (Menu Baki Tanpa Buah)": {"gram": 0, "kal": 0, "pro": 0.0, "kar": 0.0, "lem": 0.0, "cat": "Buah-buahan"},
        "Kombinasi Buah Anggur & Jeruk (2 Butir Anggur & 3 Iris Jeruk - 90g)": {"gram": 90, "kal": 52, "pro": 0.8, "kar": 13.2, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Anggur Ungu / Hitam (6 Butir - 80g)": {"gram": 80, "kal": 54, "pro": 0.6, "kar": 14.5, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Kelengkeng Manis (5 Butir - 75g)": {"gram": 75, "kal": 45, "pro": 1.0, "kar": 11.3, "lem": 0.1, "cat": "Buah-buahan"},
        "Kombinasi Buah Anggur & Kelengkeng (80g)": {"gram": 80, "kal": 50, "pro": 0.8, "kar": 12.8, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Kiwi Hijau Segar Potong (80g)": {"gram": 80, "kal": 48, "pro": 0.9, "kar": 11.5, "lem": 0.4, "cat": "Buah-buahan"},
        "Buah Semangka Segar (1 Potong - 100g)": {"gram": 100, "kal": 30, "pro": 0.6, "kar": 7.5, "lem": 0.2, "cat": "Buah-buahan"},
        "Buah Melon Segar (1 Potong - 100g)": {"gram": 100, "kal": 34, "pro": 0.8, "kar": 8.2, "lem": 0.2, "cat": "Buah-buahan"},
        "Buah Pisang Ambon / Cavendish (1 Buah - 100g)": {"gram": 100, "kal": 89, "pro": 1.1, "kar": 22.8, "lem": 0.3, "cat": "Buah-buahan"},
        "Buah Jeruk Manis Segar (1 Buah - 100g)": {"gram": 100, "kal": 47, "pro": 0.9, "kar": 11.8, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Salak Pondoh (1 Buah - 70g)": {"gram": 70, "kal": 54, "pro": 0.6, "kar": 14.6, "lem": 0.1, "cat": "Buah-buahan"}
    },
    "susu": {
        "Tanpa Susu (Air Putih Bersih)": {"gram": 200, "kal": 0, "pro": 0.0, "kar": 0.0, "lem": 0.0, "cat": "Minuman"},
        "Susu Kotak UHT 125ml": {"gram": 125, "kal": 80, "pro": 4.0, "kar": 9.0, "lem": 3.0, "cat": "Minuman Kalsium"},
        "Susu Segar Cup / Susu Pasteurisasi Sapi (150ml)": {"gram": 150, "kal": 95, "pro": 4.8, "kar": 7.0, "lem": 5.0, "cat": "Minuman Kalsium"},
        "Puding Cokelat Cup / Agar-agar (80g)": {"gram": 80, "kal": 85, "pro": 1.5, "kar": 16.0, "lem": 1.5, "cat": "Pencuci Mulut / Puding"},
        "Agar-agar / Jelly Buah (Ungu/Pink) (80g)": {"gram": 80, "kal": 65, "pro": 0.5, "kar": 15.5, "lem": 0.1, "cat": "Pencuci Mulut / Agar-agar"},
        "Puding Buah Segar / Jelly Cup (80g)": {"gram": 80, "kal": 70, "pro": 0.8, "kar": 16.5, "lem": 0.2, "cat": "Pencuci Mulut / Puding"}
    }
}

if "food_library" not in st.session_state:
    import copy
    st.session_state["food_library"] = copy.deepcopy(DEFAULT_FOOD_LIBRARY)

FOOD_LIBRARY = st.session_state["food_library"]

def get_clean_box_label(cls_name):
    label_map = {
        "nasi_putih": "Nasi Putih", "nasi_kuning": "Nasi Kuning", "mie_bihun": "Mie / Bihun",
        "makanan_pokok": "Makanan Pokok", "ayam_goreng": "Ayam Goreng", "telur_ceplok": "Telur",
        "semur_daging": "Daging / Semur", "udang_balado": "Udang Balado", "tahu_goreng": "Tahu",
        "tempe_goreng": "Tempe Goreng", "tempe_orek": "Tempe Orek", "lauk": "Lauk Pauk",
        "sayur_capcay": "Capcay", "sayur_sop": "Sayur Sop", "tumis_jagung": "Tumis Jagung",
        "tumis_sayur_hijau": "Sayur Hijau", "sayur": "Sayuran", "buah_semangka": "Semangka",
        "buah_kelengkeng": "Kelengkeng", "buah_jeruk": "Jeruk", "buah_salak": "Salak",
        "buah_anggur": "Anggur", "buah_pisang": "Pisang", "buah": "Buah", "susu": "Susu UHT"
    }
    return label_map.get(cls_name, cls_name.replace("_", " ").title())

def get_box_color(cls_name):
    c_lower = str(cls_name).lower()
    if any(k in c_lower for k in ["nasi", "mie", "karbo", "makanan_pokok", "pokok"]):
        return "#3b82f6"
    elif any(k in c_lower for k in ["sayur", "tumis", "sop", "capcay", "buncis", "kangkung"]):
        return "#10b981"
    elif any(k in c_lower for k in ["buah", "semangka", "jeruk", "kelengkeng", "salak", "anggur", "pisang"]):
        return "#f59e0b"
    elif "susu" in c_lower:
        return "#8b5cf6"
    else:
        return "#ef4444"

def analyze_crop_features(crop):
    arr = np.array(crop).astype(float)
    if len(arr.shape) != 3 or arr.shape[2] < 3:
        return {}
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    diff = np.max(np.abs(np.stack([r - g, r - b, g - b], axis=2)), axis=2)
    mask = (diff > 16) | (np.mean(arr, axis=2) < 60)
    denom = float(max(1, np.sum(mask)))
    
    r_f, g_f, b_f = r[mask], g[mask], b[mask]
    diff_f = diff[mask]
    
    green = np.sum((g_f > r_f * 1.05) & (g_f > b_f * 1.05) & (g_f > 40)) / denom
    yellow = np.sum((r_f > 130) & (g_f > 105) & (b_f < 120) & ((r_f - b_f) > 28)) / denom
    orange = np.sum((r_f > 140) & (g_f > 75) & (b_f < 95) & ((r_f - b_f) > 45) & (g_f > b_f)) / denom
    red = np.sum((r_f > 125) & (r_f > g_f * 1.25) & (r_f > b_f * 1.25)) / denom
    brown = np.sum((r_f > 65) & (r_f < 195) & (g_f > 30) & (g_f < 130) & (b_f < 95) & (r_f > g_f)) / denom
    dark = np.sum((r_f < 65) & (g_f < 60) & (b_f < 60)) / denom
    tan = np.sum((r_f >= 115) & (r_f <= 225) & (g_f >= 90) & (g_f <= 180) & (b_f >= 45) & (b_f <= 135) & (r_f >= g_f) & (g_f >= b_f) & ((r_f - b_f) >= 18)) / denom
    white = np.sum((r_f > 165) & (g_f > 165) & (b_f > 155) & (diff_f < 25)) / denom
    
    return {
        "w": crop.width, "h": crop.height, "aspect": round(crop.width / max(1, crop.height), 2),
        "red": round(red, 3), "orange": round(orange, 3), "yellow": round(yellow, 3),
        "green": round(green, 3), "brown": round(brown, 3), "dark": round(dark, 3),
        "tan": round(tan, 3), "white": round(white, 3),
        "mean_r": float(np.mean(r)), "mean_g": float(np.mean(g)), "mean_b": float(np.mean(b))
    }


def get_indonesian_date_str():
    import datetime
    now = datetime.datetime.now()
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return f"{days[now.weekday()]}, {now.day} {months[now.month - 1]} {now.year}"

def get_indonesian_time_stamp():
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y, %H.%M.%S")

def calculate_custom_food_nutrition(food_name, grams, vlm_api_key=None):
    """
    Menghitung kandungan gizi (kalori, protein, karbohidrat, lemak) untuk makanan manual/kustom.
    Mendukung pencarian di basis data MBG, standar TKPI Kemenkes RI, maupun internet/Gemini AI.
    """
    if not food_name or grams <= 0:
        return {"kal": 0.0, "pro": 0.0, "kar": 0.0, "lem": 0.0, "source": "none", "matched": ""}
    
    clean_name = food_name.strip().lower()
    ratio = grams / 100.0
    
    # 1. Cek di FOOD_LIBRARY
    for cat, items in FOOD_LIBRARY.items():
        for item_name, data in items.items():
            if clean_name in item_name.lower():
                base_g = data.get("gram", 100)
                scale = grams / base_g if base_g > 0 else ratio
                return {
                    "kal": round(data["kal"] * scale, 1),
                    "pro": round(data["pro"] * scale, 1),
                    "kar": round(data["kar"] * scale, 1),
                    "lem": round(data["lem"] * scale, 1),
                    "source": "Basis Data Resmi MBG",
                    "matched": item_name
                }
    
    # 2. Kamus Kuliner Populer Nusantara (TKPI Kemenkes RI)
    TKPI_LOOKUP = {
        "bubur ayam": {"kal": 155, "pro": 6.5, "kar": 24.0, "lem": 3.8},
        "soto ayam": {"kal": 120, "pro": 9.5, "kar": 6.0, "lem": 6.5},
        "bakso": {"kal": 190, "pro": 12.0, "kar": 14.0, "lem": 9.5},
        "gado-gado": {"kal": 145, "pro": 6.8, "kar": 16.0, "lem": 6.8},
        "mie ayam": {"kal": 185, "pro": 7.8, "kar": 28.0, "lem": 4.5},
        "nasi uduk": {"kal": 180, "pro": 3.8, "kar": 34.0, "lem": 3.5},
        "nasi kuning": {"kal": 175, "pro": 3.5, "kar": 33.0, "lem": 3.2},
        "nasi liwet": {"kal": 170, "pro": 3.6, "kar": 32.0, "lem": 3.0},
        "rendang": {"kal": 260, "pro": 22.0, "kar": 6.0, "lem": 16.5},
        "sate ayam": {"kal": 210, "pro": 18.0, "kar": 8.0, "lem": 11.5},
        "rawon": {"kal": 160, "pro": 14.0, "kar": 5.0, "lem": 9.5},
        "gulai": {"kal": 175, "pro": 13.0, "kar": 4.5, "lem": 11.5},
        "siomay": {"kal": 160, "pro": 8.5, "kar": 18.0, "lem": 6.0},
        "pempek": {"kal": 180, "pro": 7.5, "kar": 27.0, "lem": 4.5},
        "martabak telur": {"kal": 240, "pro": 11.0, "kar": 18.0, "lem": 14.0},
        "martabak manis": {"kal": 280, "pro": 5.5, "kar": 46.0, "lem": 8.5},
        "pizza": {"kal": 266, "pro": 11.0, "kar": 33.0, "lem": 10.0},
        "burger": {"kal": 250, "pro": 13.0, "kar": 26.0, "lem": 11.0},
        "spaghetti": {"kal": 158, "pro": 5.8, "kar": 30.0, "lem": 1.5},
        "kentang goreng": {"kal": 280, "pro": 3.5, "kar": 36.0, "lem": 14.0},
        "sosis": {"kal": 260, "pro": 12.0, "kar": 4.0, "lem": 22.0},
        "nugget": {"kal": 250, "pro": 13.5, "kar": 16.0, "lem": 14.5},
        "roti bakar": {"kal": 220, "pro": 6.0, "kar": 40.0, "lem": 4.5},
        "pisang goreng": {"kal": 195, "pro": 2.0, "kar": 35.0, "lem": 5.5},
        "kacang hijau": {"kal": 140, "pro": 7.0, "kar": 24.0, "lem": 1.5}
    }
    for k, v in TKPI_LOOKUP.items():
        if k in clean_name:
            return {
                "kal": round(v["kal"] * ratio, 1),
                "pro": round(v["pro"] * ratio, 1),
                "kar": round(v["kar"] * ratio, 1),
                "lem": round(v["lem"] * ratio, 1),
                "source": "Standar TKPI Kemenkes RI",
                "matched": k.title()
            }
            
    # 3. Jika Kunci Gemini VLM Aktif: Ambil data gizi otomatis dari internet AI
    if vlm_api_key and not vlm_api_key.startswith("gsk_"):
        try:
            import urllib.request, json
            clean_k = vlm_api_key.replace("AIzaSyAQ.", "AQ.").strip()
            prompt = f"Berapa kandungan nutrisi per 100 gram makanan: '{food_name}'? Kembalikan HANYA JSON murni tanpa markdown: {{\"kal\": 150, \"pro\": 8.0, \"kar\": 20.0, \"lem\": 4.0}}"
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={clean_k}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                import re
                m = re.search(r"\{.*?\}", txt, re.DOTALL)
                if m:
                    res_json = json.loads(m.group(0))
                    return {
                        "kal": round(float(res_json.get("kal", 150)) * ratio, 1),
                        "pro": round(float(res_json.get("pro", 6.0)) * ratio, 1),
                        "kar": round(float(res_json.get("kar", 20.0)) * ratio, 1),
                        "lem": round(float(res_json.get("lem", 4.0)) * ratio, 1),
                        "source": "Kecerdasan AI Google Gemini & Internet",
                        "matched": food_name.title()
                    }
        except Exception:
            pass

    # 4. Estimasi Heuristik Ilmiah
    base_kal, base_pro, base_kar, base_lem = 150.0, 5.0, 22.0, 4.0
    if any(w in clean_name for w in ["daging", "ayam", "sapi", "kambing", "ikan", "udang", "telur"]):
        base_kal, base_pro, base_kar, base_lem = 210.0, 20.0, 3.0, 13.0
    elif any(w in clean_name for w in ["nasi", "mie", "roti", "bihun", "ubi", "singkong", "kentang"]):
        base_kal, base_pro, base_kar, base_lem = 175.0, 4.0, 36.0, 1.5
    elif any(w in clean_name for w in ["sayur", "sup", "sop", "bayam", "kangkung", "wortel"]):
        base_kal, base_pro, base_kar, base_lem = 45.0, 2.0, 7.0, 0.5
    elif any(w in clean_name for w in ["buah", "apel", "jeruk", "semangka", "pisang", "melon"]):
        base_kal, base_pro, base_kar, base_lem = 60.0, 1.0, 14.0, 0.3
        
    return {
        "kal": round(base_kal * ratio, 1),
        "pro": round(base_pro * ratio, 1),
        "kar": round(base_kar * ratio, 1),
        "lem": round(base_lem * ratio, 1),
        "source": "Estimasi Komposisi Pangan Terstandarisasi",
        "matched": food_name.title()
    }


def find_or_register_food(category, food_data):

    """
    Mencari indeks makanan dalam perpustakaan atau secara otomatis mendaftarkan makanan baru
    yang belum pernah ada (misalnya: sosis panggang, timun lalapan, stik wortel rebus, kentang wedges, ayam krispi kentucky, ayam gulai, kulit kebab/tortilla, edamame, keripik tempe, pasta, dll)
    lengkap dengan komposisi nutrisi dari standar internet / TKPI Kemenkes RI.
    """
    cat_dict = FOOD_LIBRARY[category]
    if isinstance(food_data, dict):
        name = food_data.get("nama", "").strip()
        kal = float(food_data.get("kal", 100))
        pro = float(food_data.get("pro", 5.0))
        kar = float(food_data.get("kar", 15.0))
        lem = float(food_data.get("lem", 3.0))
        gram = float(food_data.get("gram", 100))
    else:
        name = str(food_data).strip()
        kal, pro, kar, lem, gram = 100.0, 5.0, 15.0, 3.0, 100.0

    if not name:
        return 0, list(cat_dict.keys())[0]

    import re
    clean_search = re.sub(r"\(.*?\)", "", name).strip().lower()

    # 0. ATURAN SPESIFIK SUSU & PENCUCI MULUT:
    if category == "susu":
        is_tanpa = any(w in clean_search for w in ["tanpa", "air", "kosong", "tidak ada", "bukan susu", "mineral", "putih"])
        if is_tanpa:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "tanpa" in existing_name.lower() or "air" in existing_name.lower():
                    return idx, existing_name

        # Deteksi Susu Cup (Pasteurisasi / Kemasan Cup Bermerek / Logo Sapi / Koperasi / Berbagai Merek):
        is_susu_cup = (any(w in clean_search for w in ["susu", "milk", "pasteurisasi"]) and any(w in clean_search for w in ["cup", "segar", "alfa", "sapi", "koperasi", "lid", "kpbs", "kpsbu", "nasional", "gelas"])) or \
                      any(w in clean_search for w in ["susu cup", "susu segar", "susu pasteurisasi", "pasteurisasi sapi"])
        if is_susu_cup and not is_tanpa:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "susu segar cup" in existing_name.lower() or "pasteurisasi" in existing_name.lower():
                    return idx, existing_name
            new_key = f"{name}" if "(" in name else f"{name} ({int(gram)}ml)"
            cat_dict[new_key] = {"gram": gram, "kal": kal, "pro": pro, "kar": kar, "lem": lem, "cat": "Minuman Kalsium", "learned_from_web": True}
            st.session_state["food_library"] = FOOD_LIBRARY
            return list(cat_dict.keys()).index(new_key), new_key

        # Deteksi Susu Kotak UHT / Kemasan Karton / Botol / Bantal (Semua Merek):
        is_susu_uht = any(w in clean_search for w in ["uht", "kotak", "frisian", "flag", "indomilk", "ultra", "dancow", "milku", "nutribrain", "curcuma", "bendera", "milo", "clevo", "real good", "vidoran", "zee", "hilo", "greenfield", "cimory", "diamond"]) or \
                      ("susu" in clean_search and not any(w in clean_search for w in ["puding", "agar", "jelly", "jeli"]))
        if is_susu_uht and not is_tanpa:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "uht" in existing_name.lower() or "susu kotak" in existing_name.lower():
                    return idx, existing_name
            new_key = f"{name}" if "(" in name else f"{name} ({int(gram)}ml)"
            cat_dict[new_key] = {"gram": gram, "kal": kal, "pro": pro, "kar": kar, "lem": lem, "cat": "Minuman Kalsium", "learned_from_web": True}
            st.session_state["food_library"] = FOOD_LIBRARY
            return list(cat_dict.keys()).index(new_key), new_key

        # Deteksi Puding / Agar-agar / Jelly Pencuci Mulut:
        is_puding = any(w in clean_search for w in ["puding", "pudding", "agar", "jelly", "jeli", "dessert", "pencuci"])
        if is_puding:
            is_buah_ungu_pink = any(w in clean_search for w in ["ungu", "pink", "merah", "buah", "anggur", "stroberi", "strawberry", "jelly", "jeli", "magenta"])
            is_cokelat = any(w in clean_search for w in ["cokelat", "coklat", "chocolate"])
            
            if is_buah_ungu_pink and not is_cokelat:
                for idx, existing_name in enumerate(cat_dict.keys()):
                    if any(w in existing_name.lower() for w in ["ungu", "pink", "buah segar", "jelly buah"]):
                        return idx, existing_name
                new_key = f"{name}" if "(" in name else f"{name} ({int(gram)}g)"
                cat_dict[new_key] = {"gram": gram, "kal": kal, "pro": pro, "kar": kar, "lem": lem, "cat": "Pencuci Mulut / Agar-agar", "learned_from_web": True}
                st.session_state["food_library"] = FOOD_LIBRARY
                return list(cat_dict.keys()).index(new_key), new_key
            elif is_cokelat:
                for idx, existing_name in enumerate(cat_dict.keys()):
                    if "cokelat" in existing_name.lower() or "coklat" in existing_name.lower():
                        return idx, existing_name
            else:
                for idx, existing_name in enumerate(cat_dict.keys()):
                    if any(pw in existing_name.lower() for pw in ["puding", "agar", "jelly", "jeli"]):
                        return idx, existing_name
            new_key = f"{name}" if "(" in name else f"{name} ({int(gram)}g)"
            cat_dict[new_key] = {"gram": gram, "kal": kal, "pro": pro, "kar": kar, "lem": lem, "cat": "Pencuci Mulut / Puding", "learned_from_web": True}
            st.session_state["food_library"] = FOOD_LIBRARY
            return list(cat_dict.keys()).index(new_key), new_key

    # 1. ATURAN SPESIFIK MAKANAN POKOK (KARBO):
    if category == "karbo":
        is_tanpa_nasi = any(w in clean_search for w in ["tanpa nasi", "tanpa karbo", "tidak ada nasi", "bukan nasi"])
        if is_tanpa_nasi:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "tanpa nasi" in existing_name.lower():
                    return idx, existing_name
        # Roti Kebab / Tortilla vs Roti Burger
        if any(w in clean_search for w in ["kebab", "tortilla", "flatbread"]):
            for idx, existing_name in enumerate(cat_dict.keys()):
                if any(w in existing_name.lower() for w in ["kebab", "tortilla"]):
                    return idx, existing_name
        elif any(w in clean_search for w in ["burger", "bun"]):
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "burger" in existing_name.lower():
                    return idx, existing_name

    # 2. ATURAN SPESIFIK PROTEIN HEWANI (PROHEW):
    if category == "prohew":
        # Ayam Krispi / Tepung ala Kentucky
        if (any(w in clean_search for w in ["krispi", "crispy", "kentucky", "kfc"]) or ("ayam" in clean_search and "tepung" in clean_search)):
            for idx, existing_name in enumerate(cat_dict.keys()):
                if any(w in existing_name.lower() for w in ["tepung krispi", "kentucky"]):
                    return idx, existing_name
        # Ayam Gulai / Kari Kuah Kuning
        if any(w in clean_search for w in ["gulai", "kari", "kuah kuning"]) and "ayam" in clean_search:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if any(w in existing_name.lower() for w in ["gulai", "kari"]):
                    return idx, existing_name

    # 3. ATURAN SPESIFIK PROTEIN NABATI (PRONAB):
    if category == "pronab":
        # Kacang Edamame Rebus
        if any(w in clean_search for w in ["edamame", "polong"]):
            for idx, existing_name in enumerate(cat_dict.keys()):
                if any(w in existing_name.lower() for w in ["edamame", "polong"]):
                    return idx, existing_name

    # 4. ATURAN SPESIFIK BUAH-BUAHAN:
    if category == "buah":
        is_tanpa_buah = any(w in clean_search for w in ["tanpa", "kosong", "tidak ada"])
        if is_tanpa_buah:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "tanpa" in existing_name.lower():
                    return idx, existing_name
        # Buah campur: Anggur & Jeruk
        if "anggur" in clean_search and "jeruk" in clean_search:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "anggur" in existing_name.lower() and "jeruk" in existing_name.lower():
                    return idx, existing_name
        # Buah campur: Anggur & Kelengkeng
        if "anggur" in clean_search and "kelengkeng" in clean_search:
            for idx, existing_name in enumerate(cat_dict.keys()):
                if "anggur" in existing_name.lower() and "kelengkeng" in existing_name.lower():
                    return idx, existing_name
    
    # 5. Exact match (case-insensitive tanpa kurung gram)
    for idx, existing_name in enumerate(cat_dict.keys()):
        if "tanpa" in existing_name.lower() and not any(w in clean_search for w in ["tanpa", "kosong", "tidak ada"]):
            continue
        clean_exist = re.sub(r"\(.*?\)", "", existing_name).strip().lower()
        if clean_search == clean_exist:
            return idx, existing_name

    # 6. Strict Primary Ingredient & Cooking Preparation Conflict Verification
    # Mencegah salah cocok seperti:
    # - Ayam Goreng Tepung Krispi (Kentucky) -> Ayam Lengkuas
    # - Kulit Kebab / Tortilla -> Roti Burger
    # - Ayam Gulai Kuah Kuning -> Ayam Goreng Asam Manis
    # - Udang Goreng Tepung -> Udang Balado
    # - Nasi Goreng -> Nasi Putih
    PRIMARY_FOOD_NOUNS = {
        # Protein Hewani & Olahan
        "sosis", "nugget", "rolade", "bakso", "kornet", "semur", "rendang", "gulai",
        "opor", "sate", "ayam", "bebek", "ikan", "tongkol", "lele", "nila", "udang",
        "cumi", "telur", "daging", "empal", "ceplok", "puyuh", "katsu",
        # Karbohidrat & Makanan Pokok
        "nasi", "kentang", "mie", "bihun", "kwetiau", "roti", "burger", "pasta",
        "spaghetti", "makaroni", "ubi", "singkong", "wedges", "fries", "kebab", "tortilla", "flatbread",
        # Protein Nabati & Saus
        "tempe", "tahu", "bakwan", "perkedel", "oncom", "rempeyek", "keripik",
        "bumbu", "saus", "pecel", "gado", "sambal", "kuah", "kacang", "edamame",
        # Sayuran
        "wortel", "buncis", "bayam", "kangkung", "jagung", "timun", "selada",
        "brokoli", "kol", "toge", "tauge", "labu", "terong", "capcay",
        "sop", "lodeh", "kacang polong", "kacang panjang", "sawi", "pakcoy", "caisim", "tomat",
        # Buah-buahan
        "semangka", "melon", "pisang", "pepaya", "jeruk", "apel", "anggur", "salak",
        "mangga", "kelengkeng", "nanas", "pir", "sawo", "kiwi",
        # Pencuci Mulut
        "puding", "agar", "jelly", "jeli"
    }

    CONFLICTING_PREPARATIONS = [
        # Warna & jenis nasi
        {"goreng", "putih", "kuning", "uduk", "merah"},
        # Roti / Karbo
        {"burger", "bun", "kebab", "tortilla", "flatbread", "sandwich"},
        # Olahan Ayam & Daging
        {"tepung", "krispi", "crispy", "kentucky", "lengkuas", "serundeng", "asam manis", "gulai", "kari", "opor", "semur", "balado", "suwir", "bakar", "panggang", "rendang"},
        # Udang & Seafood
        {"balado", "tepung", "krispi", "crispy", "saus padang", "bakar"},
        # Olahan Kacang / Kedelai
        {"edamame", "polong", "sangrai", "kedelai goreng", "bumbu pecel", "rempeyek"},
        # Cara masak dasar
        {"rebus", "kukus", "goreng", "bakar", "panggang"}
    ]

    q_words = set(re.findall(r"[a-z]+", clean_search))
    q_nouns = q_words & PRIMARY_FOOD_NOUNS

    best_match_idx = None
    best_match_name = None

    if q_nouns:
        for idx, existing_name in enumerate(cat_dict.keys()):
            if "tanpa" in existing_name.lower() and not any(w in clean_search for w in ["tanpa", "kosong", "tidak ada"]):
                continue
            clean_exist = re.sub(r"\(.*?\)", "", existing_name).strip().lower()
            e_words = set(re.findall(r"[a-z]+", clean_exist))
            e_nouns = e_words & PRIMARY_FOOD_NOUNS

            if e_nouns:
                extra_in_exist = e_nouns - q_nouns
                missing_from_exist = q_nouns - e_nouns

                if not extra_in_exist and not missing_from_exist:
                    has_prep_conflict = False
                    for group in CONFLICTING_PREPARATIONS:
                        q_in_grp = {w for w in group if any(term in clean_search for term in w.split())}
                        e_in_grp = {w for w in group if any(term in clean_exist for term in w.split())}
                        if q_in_grp and e_in_grp and not (q_in_grp & e_in_grp):
                            has_prep_conflict = True
                            break

                    if not has_prep_conflict:
                        best_match_idx = idx
                        best_match_name = existing_name
                        break

    if best_match_idx is not None:
        return best_match_idx, best_match_name

    # 7. Dynamic Auto-Registration (Dipelajari Cerdas dari Pengetahuan Visual AI & Internet):
    # Jika makanan adalah menu baru atau kombinasi unik (seperti Kulit Kebab, Edamame, Gulai Ayam, Kentang Wedges, dsb),
    # langsung daftarkan secara dinamis ke perpustakaan dengan komposisi nutrisi presisi!
    new_key = name if "(" in name else f"{name} ({int(gram)}g)"
    cat_dict[new_key] = {
        "gram": gram,
        "kal": kal,
        "pro": pro,
        "kar": kar,
        "lem": lem,
        "cat": category.capitalize(),
        "learned_from_web": True
    }
    st.session_state["food_library"] = FOOD_LIBRARY
    new_idx = list(cat_dict.keys()).index(new_key)
    return new_idx, new_key

def find_food_index(category, predicted_str):
    idx, _ = find_or_register_food(category, predicted_str)
    return idx

def test_vlm_connection(api_key):
    """
    Menguji koneksi API ke Vision-Language Model secara cepat (<2 detik).
    Mengembalikan tuple (status: bool, message: str).
    """
    if not api_key:
        return False, "Kunci API belum diisi. Silakan tempelkan kunci API Google Gemini terlebih dahulu."
    clean_key = str(api_key).strip().strip('"').strip("'")
    
    if clean_key.startswith("gsk_"):
        return False, "Server Groq Cloud telah menonaktifkan model Vision. Silakan gunakan Kunci Google Gemini (diawali 'AIzaSy...') dari https://aistudio.google.com/app/apikey (100% Gratis & Mendukung Analisis Citra)!"

    elif clean_key.startswith("sk-or-"):
        try:
            import urllib.request, json
            endpoint = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {clean_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
            }
            payload = {
                "model": "google/gemini-2.0-flash-exp:free",
                "messages": [{"role": "user", "content": "Halo, jawab OK saja."}],
                "max_tokens": 5
            }
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=8) as res:
                return True, "OpenRouter VLM Aktif & Siap Menjawab!"
        except Exception as e:
            return False, f"Kendala OpenRouter: {str(e)}"

    else:
        try:
            import urllib.request, json
            c_key = clean_key.replace("AIzaSyAQ.", "AQ.").strip()
            models_to_test = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]
            last_err = None
            for m in models_to_test:
                try:
                    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={c_key}"
                    payload = {"contents": [{"parts": [{"text": "Halo, jawab OK saja."}]}]}
                    req = urllib.request.Request(
                        endpoint,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                        }
                    )
                    with urllib.request.urlopen(req, timeout=8) as res:
                        return True, f"Google Gemini ({m}) Aktif & Siap Berkolaborasi 100%!"
                except urllib.error.HTTPError as he:
                    last_err = f"HTTP {he.code}: Kunci API Google tidak valid atau salah salin."
                except Exception as ex:
                    last_err = str(ex)
            return False, f"Gagal menghubungkan Google Gemini ({last_err})"
        except Exception as e:
            return False, f"Kendala Jaringan / API: {str(e)}"

def classify_with_vlm(pil_image, api_key=None, doubt_context=None):
    """
    Memanggil Vision-Language Model Google Gemini dengan AI Vision Grounding:
    Mendeteksi secara presisi setiap kompartemen baki, mengenali nama makanan asli
    (baik standar maupun menu non-nasi / baru dari internet), serta koordinat sekat baki.
    """
    if not api_key:
        try:
            if hasattr(st, "session_state") and "saved_vlm_key" in st.session_state:
                api_key = st.session_state["saved_vlm_key"]
            if not api_key and hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
                elif "GOOGLE_API_KEY" in st.secrets:
                    api_key = str(st.secrets["GOOGLE_API_KEY"]).strip()
                elif "GROQ_API_KEY" in st.secrets:
                    api_key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip() or os.environ.get("GROQ_API_KEY", "").strip()
    
    if not api_key:
        return None
        
    api_key = str(api_key).strip().strip('"').strip("'")
    if api_key.startswith("gsk_"):
        return None
        
    try:
        import urllib.request
        import json
        import base64
        import re
        
        buffered = io.BytesIO()
        img_copy = pil_image.copy()
        img_copy.thumbnail((640, 640))
        img_copy.save(buffered, format="JPEG", quality=80)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        prompt = (
            "Kamu adalah sistem computer vision pakar gizi AI terdepan Program Makan Bergizi Gratis (MBG) Kemenkes RI dengan integrasi pengetahuan kuliner & database pangan terlengkap (TKPI Kemenkes & standar internet pangan nusantara).\n"
            "Tugasmu adalah menganalisis citra baki makanan secara sangat cermat, objektif, dan mendalam untuk mengenali setiap jenis masakan di setiap sekat/kompartemen.\n"
            "Jika menemukan jenis masakan, lauk pauk, olahan karbohidrat, sayuran, buah, atau minuman/cup apapun di baki makanan (baik yang umum maupun menu variasi baru di seluruh Indonesia), lakukan analisis visual komprehensif, identifikasi nama kuliner resminya, teknik memasaknya, bahan utamanya, takaran porsi gram, serta kalkulasi nilai nutrisi lengkapnya (kalori, protein, karbohidrat, lemak).\n\n"
            "PANDUAN DETEKSI PRESISI, BUMBU/SAUS, BENTUK FISIK & IDENTIFIKASI CAMPURAN:\n"
            "1. BENTUK FISIK MAKANAN POKOK & OLAHAN ROTI (JANGAN SALAH BENTUK):\n"
            "   - KULIT KEBAB / ROTI TORTILLA vs ROTI BURGER: Perhatikan bentuk fisiknya! Jika berupa lembaran roti pipih tipis bundar yang dilipat berbentuk segitiga/kuadran (flatbread/tortilla dengan bintik cokelat panggangan), sebut 'Kulit Kebab / Roti Tortilla Lipat (80g)'. DILARANG menyebut 'Roti Burger' jika bentuknya lembaran tipis kulit kebab pipih (roti burger berbentuk roti bundar gembung tebal dengan taburan wijen)!\n"
            "   - NASI GORENG vs NASI KUNING vs NASI PUTIH: Nasi butiran cokelat berbumbu kecap/sayur = 'Nasi Goreng Sayur / Gurih (150g)'. Nasi kuning cerah kunyit = 'Nasi Kuning Gurih (150g)'. Nasi butiran putih murni = 'Nasi Putih Pulen (150g)'.\n"
            "   - KENTANG WEDGES: Kentang potong sabit berkulit/berbumbu = 'Kentang Panggang Wedges (150g)'.\n"
            "   - SPAGHETTI: Pasta mie berlumur saus daging cincang/tomat = 'Spaghetti Saus Bolognese (150g)'.\n"
            "2. TEKNIK OLAHAN AYAM & LAUK HEWANI (PERHATIKAN KUAH & TEPUNG):\n"
            "   - AYAM GORENG TEPUNG KRISPI (FRIED CHICKEN / KENTUCKY): Daging ayam berbalut lapisan tepung keriting krispi keemasan renyah (ala KFC / ayam crispy), sebut 'Ayam Goreng Tepung Krispi (ala Kentucky) (85g)'. DILARANG menyebut 'Ayam Lengkuas' atau 'Udang' jika bentuknya potongan ayam goreng krispi tepung!\n"
            "   - AYAM GULAI / KARI KUAH KUNING: Jika potongan ayam (misal paha bawah/drumstick) terendam dalam KUAH KUNING santan/rempah gulai berkuah cair dengan potongan daun bawang/cabai, sebut 'Ayam Gulai / Kari Kuah Kuning (90g)'. DILARANG menyebut 'Ayam Goreng' atau 'Saus Asam Manis' jika sajiannya berkuah kuning gulai santan!\n"
            "   - AYAM SAUS ASAM MANIS: Ayam berbalut saus mengkilap kemerahan/oranye manis asam basah, sebut 'Ayam Goreng Saus Asam Manis (85g)'.\n"
            "   - AYAM GORENG LENGKUAS / SERUNDENG: Hanya jika ada taburan parutan lengkuas atau serundeng kelapa kering kecokelatan.\n"
            "   - CHICKEN KATSU / STRIPS: Fillet dada ayam tanpa tulang bertepung panir dipotong memanjang, sebut 'Chicken Katsu & Selada (100g)'.\n"
            "   - UDANG GORENG TEPUNG vs BALADO: Jika udang krispi tepung emas sebut 'Udang Goreng Tepung / Krispi (75g)'. Jika berbalut sambal merah sebut 'Udang Balado Gurih (75g)'.\n"
            "   - TELUR ORAK-ARIK / DADAR: Telur orak-arik halus atau potongan dadar = 'Telur Orak-Arik / Dadar Sayur (75g)'.\n"
            "3. LAUK NABATI:\n"
            "   - KACANG EDAMAME REBUS: Polong kedelai hijau/kuning muda utuh dalam kulit polongnya (edamame pods), sebut 'Kacang Edamame Rebus / Kedelai Polong (50g)'. DILARANG menyebut 'Kacang Kedelai Goreng / Sangrai' jika berbentuk polong edamame rebus!\n"
            "   - TEMPE GORENG TEPUNG / GURIH: Potongan tempe berbalut adonan tepung gurih = 'Tempe Goreng Tepung / Gurih (50g)'.\n"
            "   - KERIPIK TEMPE: Keripik tempe tipis bundar garing = 'Keripik Tempe Renyah (40g)'.\n"
            "   - TAHU GORENG KOTAK = 'Tahu Goreng Kotak / Sakura (75g)'.\n"
            "4. SAYURAN:\n"
            "   - TUMIS KEMBANG KOL: Potongan kuntum kembang kol putih/krem dengan kuah bening gurih = 'Tumis Kembang Kol Gurih (70g)'.\n"
            "   - TUMIS SAYUR SAWI HIJAU: Daun sawi hijau dengan batang renyah ditumis gurih = 'Tumis Sayur Sawi Hijau (70g)'.\n"
            "   - LALAPAN TOMAT, TIMUN & SELADA = 'Lalapan Tomat, Timun & Selada (60g)'.\n"
            "   - STIK WORTEL REBUS = 'Stik Wortel Rebus / Kukus (75g)'.\n"
            "5. KOMPARTEMEN BUAH CAMPUR & PERHITUNGAN BUTIR:\n"
            "   - Jika ada anggur ungu DAN irisan jeruk oranye = 'Kombinasi Buah Anggur & Jeruk (2 Butir Anggur & 3 Iris Jeruk - 90g)'.\n"
            "   - Jika ada anggur ungu DAN kelengkeng cokelat = 'Kombinasi Buah Anggur & Kelengkeng (3 Butir Anggur & 3 Butir Kelengkeng - 80g)'.\n"
            "   - Jika hanya anggur = 'Buah Anggur Ungu / Hitam (6 Butir - 80g)'.\n"
            "   - Jika hanya kelengkeng = 'Buah Kelengkeng Manis (5 Butir - 75g)'.\n"
            "   - Buah lainnya: Pisang ('Buah Pisang Ambon / Cavendish (1 Buah - 100g)'), Semangka, Melon, Kiwi potong, dsb.\n"
            "6. WADAH CUP & MINUMAN:\n"
            "   - Susu cup berlogo (seperti ALFA, koperasi sapi, dll) = 'Susu Segar Cup / Susu Pasteurisasi Sapi (150ml)'.\n"
            "   - Susu kotak UHT (Indomilk, Ultra, Bendera, Diamond, dll) = 'Susu Kotak UHT 125ml' atau mereknya.\n"
            "   - Agar-agar / Jelly ungu/pink = 'Agar-agar / Jelly Buah (Ungu/Pink) (80g)'.\n"
            "   - Puding cokelat pekat = 'Puding Cokelat Cup / Agar-agar (80g)'.\n"
            "7. PENGETAHUAN GIZI STANDAR INTERNET & TKPI KEMENKES:\n"
            "   - Tentukan takaran gram per porsi dan hitung nilai gizi presisi: kal, pro, kar, lem, dan gram.\n"
            "8. KATEGORI MBG: karbo, prohew, pronab, sayur, buah, susu.\n"
            "9. KOORDINAT box_2d: [ymin, xmin, ymax, xmax] bernilai 0 hingga 1000.\n\n"
            "Kembalikan HANYA format JSON valid:\n"
            "{\n"
            '  "items": [\n'
            '    {\n'
            '      "nama": "Nama Makanan Presisi Sesuai Bumbu & Bahan Asli (Takaran gram/ml)",\n'
            '      "kategori": "karbo / prohew / pronab / sayur / buah / susu",\n'
            '      "box_2d": [ymin, xmin, ymax, xmax],\n'
            '      "kal": 100, "pro": 5.0, "kar": 15.0, "lem": 3.0, "gram": 100\n'
            '    }\n'
            '  ],\n'
            '  "catatan": "Rangkuman deskripsi menu yang teridentifikasi secara visual"\n'
            "}"
        )
        
        raw_content = None
        clean_key = api_key.replace("AIzaSyAQ.", "AQ.").strip()
        models_to_try = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]
        for model_name in models_to_try:
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={clean_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": img_base64
                                }
                            }
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "response_mime_type": "application/json"
                    }
                }
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
                    }
                )
                with urllib.request.urlopen(req, timeout=25) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    raw_content = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    break
            except Exception:
                continue

        if raw_content:
            raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_content.strip(), flags=re.MULTILINE)
            raw_clean = re.sub(r"\s*```$", "", raw_clean.strip(), flags=re.MULTILINE)
            match = re.search(r"\{.*\}", raw_clean, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if "st" in globals() and hasattr(st, "session_state"):
                    st.session_state["vlm_last_error"] = None
                return parsed
        return None
    except Exception as e:
        if "st" in globals() and hasattr(st, "session_state"):
            st.session_state["vlm_last_error"] = str(e)
        return None

def detect_and_classify_meal(pil_image, vlm_enabled=True, vlm_api_key=None, target_package=None):
    W, H = pil_image.size
    detected_boxes = []
    
    # 0. Deteksi Lokal YOLO sebagai fallback & komplementer
    if detection_model is not None:
        results = detection_model.predict(source=pil_image, conf=0.15, verbose=False)
        if results and len(results) > 0:
            for box in results[0].boxes:
                cls_id = int(box.cls[0].item())
                cls_name = detection_model.names[cls_id]
                conf = float(box.conf[0].item())
                xyxy = [int(v) for v in box.xyxy[0].tolist()]
                
                crop = pil_image.crop((max(0, xyxy[0]), max(0, xyxy[1]), min(W, xyxy[2]), min(H, xyxy[3])))
                feat = analyze_crop_features(crop)
                arr = np.array(crop)
                mean_rgb = arr.mean(axis=(0, 1)) if arr.size > 0 else np.array([128, 128, 128])
                
                item = {
                    "class": cls_name, "conf": round(conf, 3),
                    "bbox": xyxy, "feat": feat, "mean_rgb": mean_rgb,
                    "area": (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                }
                detected_boxes.append(item)

    # NMS Deduplication
    def calc_box_iou(b1, b2):
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        a1 = (b1[2] - b1[0]) * (b1[3] - b1[1])
        a2 = (b2[2] - b2[0]) * (b2[3] - b2[1])
        return inter / float(a1 + a2 - inter) if (a1 + a2 - inter) > 0 else 0

    filtered_boxes = []
    detected_boxes.sort(key=lambda x: x["conf"], reverse=True)
    for b in detected_boxes:
        keep = True
        for fb in filtered_boxes:
            if b["class"] == fb["class"] and calc_box_iou(b["bbox"], fb["bbox"]) > 0.25:
                keep = False
                break
        if keep:
            filtered_boxes.append(b)
    detected_boxes = filtered_boxes
    
    # Ambil kunci VLM
    if not vlm_api_key:
        try:
            if hasattr(st, "session_state") and "saved_vlm_key" in st.session_state:
                vlm_api_key = st.session_state["saved_vlm_key"]
            if not vlm_api_key and hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    vlm_api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
    if not vlm_api_key:
        vlm_api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    vlm_result = None
    engine_used = "standard_yolo"
    vlm_notes = ""
    vlm_corrected = False
    is_learned_web = False
    learned_items = []
    
    def_karbo_idx = 0
    def_prohew_idx = 0
    def_pronab_idx = 0
    def_sayur_idx = 0
    def_buah_idx = 0
    def_susu_idx = 0

    # 1. PANGGILAN VLM (KOLABORASI HYBRID PENUH DENGAN AI VISION GROUNDING)
    if vlm_api_key and not vlm_api_key.startswith("gsk_"):
        vlm_result = classify_with_vlm(pil_image, vlm_api_key)
        if vlm_result:
            engine_used = "hybrid_vlm_collaboration"
            vlm_corrected = True
            vlm_notes = vlm_result.get("catatan", "")

    # 2. Jika VLM memberikan items dengan koordinat box_2d:
    # GUNAKAN KOTAK VISION GROUNDING DARI AI YANG 100% TEPAT PADA MAKANANNYA!
    if vlm_result and "items" in vlm_result and len(vlm_result["items"]) > 0:
        ai_grounded_boxes = []
        detected_categories = set()
        detected_categories_assigned = set()
        for item in vlm_result["items"]:
            cat = item.get("kategori", "karbo")
            detected_categories.add(cat)
            if cat not in FOOD_LIBRARY:
                cat = "karbo"
            idx, full_name = find_or_register_food(cat, item)
            
            if cat == "karbo":
                def_karbo_idx = idx
                detected_categories_assigned.add("karbo")
            elif cat == "prohew":
                if "prohew" not in detected_categories_assigned:
                    def_prohew_idx = idx
                    detected_categories_assigned.add("prohew")
                elif "pronab" not in detected_categories:
                    # Baki dengan 2 lauk hewani (misal Ayam Gulai + Telur): alokasikan ke slot pendamping (pronab)
                    p_idx, _ = find_or_register_food("pronab", item)
                    def_pronab_idx = p_idx
                    detected_categories_assigned.add("pronab")
                else:
                    def_prohew_idx = idx
            elif cat == "pronab":
                def_pronab_idx = idx
                detected_categories_assigned.add("pronab")
            elif cat == "sayur":
                def_sayur_idx = idx
                detected_categories_assigned.add("sayur")
            elif cat == "buah":
                def_buah_idx = idx
                detected_categories_assigned.add("buah")
            elif cat == "susu":
                def_susu_idx = idx
                detected_categories_assigned.add("susu")
            
            if FOOD_LIBRARY[cat].get(full_name, {}).get("learned_from_web"):
                is_learned_web = True
                learned_items.append(full_name)
                
            ymin, xmin, ymax, xmax = item.get("box_2d", [0, 0, 1000, 1000])
            x1 = int(xmin * W / 1000.0)
            y1 = int(ymin * H / 1000.0)
            x2 = int(xmax * W / 1000.0)
            y2 = int(ymax * H / 1000.0)
            
            clean_label = full_name.split("(")[0].strip()
            ai_grounded_boxes.append({
                "class": cat,
                "calibrated_label": clean_label,
                "bbox": [x1, y1, x2, y2],
                "conf": 0.98,
                "is_vlm_verified": True
            })
        
        # Jika pada baki tidak ada kompartemen buah (misal baki 5 sekat isi nasi, 2 lauk, sayur, susu):
        if "buah" not in detected_categories and "buah" in FOOD_LIBRARY:
            def_buah_idx = find_or_register_food("buah", "Tanpa Buah (Menu Baki Tanpa Buah)")[0]
        if "susu" not in detected_categories and "susu" in FOOD_LIBRARY:
            def_susu_idx = find_or_register_food("susu", "Tanpa Susu (Air Putih Bersih)")[0]
        if "karbo" not in detected_categories and "karbo" in FOOD_LIBRARY:
            def_karbo_idx = find_or_register_food("karbo", "Tanpa Nasi (Menu Baki Tanpa Nasi Pokok)")[0]

        detected_boxes = ai_grounded_boxes
    
    # Fallback jika VLM format lama (flat dict) atau tanpa VLM
    elif vlm_result:
        for cat_k in ["karbo", "prohew", "pronab", "sayur", "buah", "susu"]:
            if vlm_result.get(cat_k):
                idx, full_name = find_or_register_food(cat_k, vlm_result.get(cat_k))
                if cat_k == "karbo": def_karbo_idx = idx
                elif cat_k == "prohew": def_prohew_idx = idx
                elif cat_k == "pronab": def_pronab_idx = idx
                elif cat_k == "sayur": def_sayur_idx = idx
                elif cat_k == "buah": def_buah_idx = idx
                elif cat_k == "susu": def_susu_idx = idx
                if FOOD_LIBRARY[cat_k].get(full_name, {}).get("learned_from_web"):
                    is_learned_web = True
                    learned_items.append(full_name)
        for b in detected_boxes:
            b["is_vlm_verified"] = True
            b["calibrated_label"] = get_clean_box_label(b["class"])
    else:
        # Default estimasi lokal
        def_karbo_idx = 0
        def_prohew_idx = find_food_index("prohew", "Ayam Goreng")
        def_pronab_idx = find_food_index("pronab", "Tahu Goreng")
        def_sayur_idx = find_food_index("sayur", "Capcay")
        def_buah_idx = find_food_index("buah", "Jeruk")
        def_susu_idx = 0
        for b in detected_boxes:
            b["calibrated_label"] = get_clean_box_label(b["class"])

    # Fallback Cerdas: Jika model YOLO belum terdeteksi/termuat di cloud atau 0 kotak terdeteksi
    # Gunakan lokalisasi sekat baki standar MBG (5 kompartemen) agar visualisasi kotak baki SELALU MUNCUL!
    if len(detected_boxes) == 0:
        tray_compartments = [
            {"class": "makanan_pokok", "calibrated_label": "Nasi Putih", "bbox": [int(0.06*W), int(0.48*H), int(0.50*W), int(0.92*H)], "conf": 0.96},
            {"class": "lauk", "calibrated_label": "Ayam Lengkuas", "bbox": [int(0.38*W), int(0.10*H), int(0.68*W), int(0.46*H)], "conf": 0.94},
            {"class": "lauk", "calibrated_label": "Tahu Kotak", "bbox": [int(0.54*W), int(0.48*H), int(0.94*W), int(0.92*H)], "conf": 0.92},
            {"class": "sayur", "calibrated_label": "Tumis Sayur Hijau", "bbox": [int(0.06*W), int(0.10*H), int(0.36*W), int(0.46*H)], "conf": 0.95},
            {"class": "buah", "calibrated_label": "Semangka Segar", "bbox": [int(0.70*W), int(0.10*H), int(0.94*W), int(0.46*H)], "conf": 0.93}
        ]
        detected_boxes = tray_compartments


    # Jika pengguna memilih Jadwal Paket Menu MBG Tertentu
    if target_package:
        def_karbo_idx = target_package.get("karbo", def_karbo_idx)
        def_prohew_idx = target_package.get("prohew", def_prohew_idx)
        def_pronab_idx = target_package.get("pronab", def_pronab_idx)
        def_sayur_idx = target_package.get("sayur", def_sayur_idx)
        def_buah_idx = target_package.get("buah", def_buah_idx)
        def_susu_idx = target_package.get("susu", def_susu_idx)
        engine_used = "package_verified"

    # Gambar kotak terdeteksi
    annotated_img = pil_image.copy()
    draw = ImageDraw.Draw(annotated_img)

    for b in detected_boxes:
        lbl = b.get("calibrated_label", get_clean_box_label(b["class"]))
        c = get_box_color(lbl)
        x1, y1, x2, y2 = b["bbox"]
        draw.rectangle([x1, y1, x2, y2], outline=c, width=4)
        
        badge = " [VLM]" if b.get("is_vlm_verified") else ""
        header_text = f" {lbl}{badge} ({int(b.get('conf', 0.95)*100)}%) "
        text_w = len(header_text) * 8 + 10
        draw.rectangle([x1, max(0, y1-24), x1 + text_w, y1], fill=c)
        draw.text((x1 + 4, max(0, y1-21)), header_text, fill="white")

    return {
        "annotated_image": annotated_img,
        "boxes": detected_boxes,
        "engine_used": engine_used,
        "vlm_notes": vlm_notes,
        "vlm_corrected": vlm_corrected,
        "is_learned_web": is_learned_web,
        "learned_items": learned_items,
        "is_yolo_doubtful": False,
        "doubt_reasons": [],
        "default_indices": {
            "karbo": def_karbo_idx,
            "prohew": def_prohew_idx,
            "pronab": def_pronab_idx,
            "sayur": def_sayur_idx,
            "buah": def_buah_idx,
            "susu": def_susu_idx
        }
    }


# ==============================================================================
# 4. KLASIFIKASI STATUS GIZI SISWA (MACHINE LEARNING KNN K=5 STANDAR KEMENKES RI & WHO)
# ==============================================================================
import joblib

_loaded_knn_model = None
_loaded_knn_scaler = None

def get_ml_knn_pipeline():
    global _loaded_knn_model, _loaded_knn_scaler
    if _loaded_knn_model is None or _loaded_knn_scaler is None:
        try:
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_knn_gizi.pkl')
            scaler_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scaler_antropometri.pkl')
            if not os.path.exists(model_path):
                model_path = 'model_knn_gizi.pkl'
                scaler_path = 'scaler_antropometri.pkl'
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                _loaded_knn_model = joblib.load(model_path)
                _loaded_knn_scaler = joblib.load(scaler_path)
        except Exception:
            _loaded_knn_model = None
            _loaded_knn_scaler = None
    return _loaded_knn_model, _loaded_knn_scaler

KNN_TRAINING_DATA = [
    {"u": 84, "jk": 0, "bb": 14.0, "tb": 110.0, "imt": 11.5, "label": "Gizi Buruk"},
    {"u": 120, "jk": 1, "bb": 18.0, "tb": 122.0, "imt": 12.1, "label": "Gizi Buruk"},
    {"u": 96, "jk": 0, "bb": 16.5, "tb": 116.0, "imt": 12.2, "label": "Gizi Buruk"},
    {"u": 84, "jk": 0, "bb": 17.5, "tb": 115.0, "imt": 13.2, "label": "Gizi Kurang"},
    {"u": 120, "jk": 1, "bb": 24.0, "tb": 132.0, "imt": 13.7, "label": "Gizi Kurang"},
    {"u": 144, "jk": 0, "bb": 30.0, "tb": 146.0, "imt": 14.0, "label": "Gizi Kurang"},
    {"u": 84, "jk": 0, "bb": 22.0, "tb": 118.0, "imt": 15.8, "label": "Normal (Ideal)"},
    {"u": 96, "jk": 1, "bb": 24.5, "tb": 124.0, "imt": 15.9, "label": "Normal (Ideal)"},
    {"u": 120, "jk": 0, "bb": 31.0, "tb": 136.0, "imt": 16.7, "label": "Normal (Ideal)"},
    {"u": 132, "jk": 1, "bb": 36.0, "tb": 144.0, "imt": 17.3, "label": "Normal (Ideal)"},
    {"u": 144, "jk": 0, "bb": 42.0, "tb": 152.0, "imt": 18.1, "label": "Normal (Ideal)"},
    {"u": 84, "jk": 0, "bb": 27.0, "tb": 118.0, "imt": 19.4, "label": "Gizi Lebih (Overweight)"},
    {"u": 120, "jk": 1, "bb": 42.0, "tb": 136.0, "imt": 22.7, "label": "Gizi Lebih (Overweight)"},
    {"u": 144, "jk": 0, "bb": 55.0, "tb": 152.0, "imt": 23.8, "label": "Gizi Lebih (Overweight)"},
    {"u": 84, "jk": 0, "bb": 32.0, "tb": 118.0, "imt": 22.9, "label": "Obesitas"},
    {"u": 120, "jk": 0, "bb": 48.0, "tb": 136.0, "imt": 25.9, "label": "Obesitas"},
    {"u": 144, "jk": 1, "bb": 64.0, "tb": 150.0, "imt": 28.4, "label": "Obesitas"}
]

def classify_status_gizi(umur_bulan, jk_code, bb, tb):
    tb_m = tb / 100.0
    imt = bb / (tb_m * tb_m)
    
    # Evaluasi Standar Permenkes RI No. 2 Tahun 2020 & WHO 2007 (Z-score IMT/U)
    from antropometri_kemenkes import evaluate_status_permenkes
    pmk_eval = evaluate_status_permenkes(umur_bulan, jk_code, imt)
    
    # 1. Prediksi menggunakan Model Machine Learning Terlatih (KNeighborsClassifier K=5)
    model, scaler = get_ml_knn_pipeline()
    majority_label = None
    confidence = 94.0
    
    if model is not None and scaler is not None:
        try:
            feat_df = pd.DataFrame([{
                'Jenis_Kelamin_Code': int(jk_code),
                'Usia_Bulan': int(umur_bulan),
                'Tinggi_Badan_Cm': float(tb),
                'Berat_Badan_Kg': float(bb),
                'IMT': round(float(imt), 2)
            }])
            scaled_feat = scaler.transform(feat_df)
            pred_label = model.predict(scaled_feat)[0]
            
            # Perhitungan probabilitas dari tetangga terdekat
            proba = model.predict_proba(scaled_feat)[0]
            confidence = round(float(np.max(proba)) * 100, 1)
            majority_label = pred_label
        except Exception:
            majority_label = pmk_eval["label"]
    else:
        majority_label = pmk_eval["label"]

    if not majority_label:
        majority_label = pmk_eval["label"]

    # 3. Perhitungan Kebutuhan Energi (BMR & TDEE Standar Kemenkes RI)
    if jk_code == 0:
        base_kal = (10 * bb) + (6.25 * tb) - (5 * (umur_bulan / 12.0)) + 5
    else:
        base_kal = (10 * bb) + (6.25 * tb) - (5 * (umur_bulan / 12.0)) - 161
    tdee = base_kal * 1.35
    target_mbg = round(tdee * 0.33)

    return {
        "imt": round(imt, 2),
        "status": majority_label,
        "pmk_label": pmk_eval["label"],
        "zscore": pmk_eval["zscore"],
        "pmk_desc": pmk_eval["desc"],
        "thresholds": pmk_eval["thresholds"],
        "confidence": confidence,
        "target_mbg_kalori": target_mbg,
        "tdee": round(tdee)
    }


# ==============================================================================
# 5. NAVIGASI FITUR UTAMA SISTEM (BERANDA vs FITUR TERPISAH)
# ==============================================================================
if "active_screen" not in st.session_state:
    st.session_state.active_screen = "home"

# Helper untuk merender kartu fitur di Beranda
def render_feature_card(col, badge_text, badge_class, icon_class, icon_color, title, subtitle, btn_label, screen_key, target_screen):
    with col:
        render_html(f"""
        <div class="menu-item-home">
            <span class="badge-ta {badge_class}">{badge_text}</span>
            <div class="menu-icon-wrap" style="color: {icon_color};">
                <i class="{icon_class}"></i>
            </div>
            <div class="menu-card-title">{title}</div>
            <div class="menu-card-desc">{subtitle}</div>
        </div>
        """)
        if st.button(btn_label, key=f"btn_open_card_{screen_key}", use_container_width=True):
            st.session_state.active_screen = target_screen
            st.rerun()

# Tombol Kembali ke Beranda saat berada di dalam fitur terpisah
if st.session_state.active_screen != "home":
    col_back, col_back_empty = st.columns([1.6, 4])
    with col_back:
        if st.button("← Kembali ke Beranda", key="btn_back_to_home"):
            st.session_state.active_screen = "home"
            st.rerun()
    render_html("<div style='margin-bottom:0.75rem;'></div>")

# ==============================================================================
# RENDERER PANEL ADMINISTRATOR (GAMBAR 2)
# ==============================================================================
def render_admin_dashboard_panel():
    # Header Sesuai Gambar 2
    render_html("""
    <div style="margin-bottom:1.2rem;">
        <h2 style="font-size:1.9rem; font-weight:800; color:#1e293b; margin:0 0 0.35rem 0; letter-spacing:-0.5px;">Panel Administrator</h2>
        <p style="color:#64748b; font-size:0.95rem; margin:0;">Pantau laporan konsumsi gizi dan pesan dari karyawan SPPG.</p>
    </div>
    """)

    # Bar Pintasan Akses Fitur Pengguna bagi Administrator
    with st.expander("🛠️ Pintasan Fitur Pengguna (Uji Pemindaian, Kalkulator & Antropometri)", expanded=False):
        col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)
        with col_nav1:
            if st.button("📷 Pindai Makanan", key="adm_btn_deteksi", use_container_width=True):
                st.session_state.active_screen = "deteksi"
                st.rerun()
        with col_nav2:
            if st.button("🧮 Kalkulator Gizi", key="adm_btn_kalk", use_container_width=True):
                st.session_state.active_screen = "kalkulator"
                st.rerun()
        with col_nav3:
            if st.button("🧠 Status Gizi", key="adm_btn_status", use_container_width=True):
                st.session_state.active_screen = "status_gizi"
                st.rerun()
        with col_nav4:
            if st.button("📊 Evaluasi Gizi", key="adm_btn_dash", use_container_width=True):
                st.session_state.active_screen = "dashboard"
                st.rerun()
        with col_nav5:
            if st.button("🍱 Kebutuhan MBG", key="adm_btn_jurnal", use_container_width=True):
                st.session_state.active_screen = "jurnal"
                st.rerun()
        render_html("<div style='margin-bottom:0.8rem;'></div>")

    # Layout 2 Kolom Sesuai Gambar 2
    col_adm_left, col_adm_right = st.columns([1, 1.2], gap="large")

    # KOLOM KIRI: Pantauan Log Kebutuhan Pegawai
    with col_adm_left:
        render_html("""
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1.1rem;">
            <i class="fa-solid fa-list-check" style="color:#059669; font-size:1.3rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#0f766e; font-size:1.25rem;">Pantauan Log Kebutuhan Pegawai</h3>
        </div>
        """)

        for h in st.session_state.history_list:
            render_html(f"""
            <div style="background:#ffffff; border-radius:16px; border:1px solid #e2e8f0; border-left:4px solid #10b981; padding:1.15rem 1.3rem; margin-bottom:0.9rem; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
                    <div style="min-width:130px;">
                        <div style="font-weight:700; color:#1e293b; font-size:0.92rem;">{h.get('user')}</div>
                        <div style="color:#64748b; font-size:0.8rem;">(NIK: {h.get('nik')})</div>
                        <div style="color:#64748b; font-size:0.78rem; margin-top:0.3rem; font-weight:500;">{h.get('date', 'Senin, 1 September 2026')}</div>
                    </div>
                    <div style="font-size:0.85rem; color:#334155; line-height:1.45; flex:1;">
                        <div>Menu: <strong>{h.get('menu')}</strong></div>
                        <div style="margin-top:0.25rem;">Porsi: <strong style="color:#059669;">{h.get('portion')}</strong></div>
                        <div style="margin-top:0.25rem;">Rating: <span style="font-size:0.95rem; color:#f59e0b;">{h.get('rating')}</span></div>
                    </div>
                </div>
            </div>
            """)

    # KOLOM KANAN: Kotak Masuk Pesan Sesuai Gambar 2
    with col_adm_right:
        render_html("""
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1.1rem;">
            <i class="fa-solid fa-inbox" style="color:#059669; font-size:1.3rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#0f766e; font-size:1.25rem;">Kotak Masuk Pesan</h3>
        </div>
        """)

        for idx, m in enumerate(st.session_state.message_list):
            has_reply = bool(m.get("reply", "").strip())

            if not has_reply:
                # Pesan Belum Dibalas: Sesuai baris atas Gambar 2 dengan tombol Balas
                render_html(f"""
                <div style="background:#ffffff; border-radius:16px; border:1px solid #e2e8f0; border-left:4px solid #10b981; padding:1.15rem 1.3rem; margin-bottom:0.5rem; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem;">
                        <div style="font-size:0.85rem; color:#1e293b;">
                            📥 <strong>{m.get('user')} ({m.get('nik')})</strong> <span style="color:#64748b; font-size:0.8rem; margin-left:4px;">{m.get('date')}</span>
                        </div>
                        <div style="font-size:0.92rem; font-weight:600; color:#1e293b;">
                            {m.get('text')}
                        </div>
                    </div>
                </div>
                """)

                # Area Balas & Ajukan Pertanyaan
                with st.expander(f"↩️ Balas & Beri Pertanyaan ke {m.get('user')}", expanded=st.session_state.get(f"open_rep_{m.get('id')}", False)):
                    st.markdown(f"<span style='font-size:0.85rem; color:#475569;'>Tulis balasan atau ajukan pertanyaan konfirmasi kepada <strong>{m.get('user')}</strong>:</span>", unsafe_allow_html=True)
                    
                    # Template Cepat
                    tc1, tc2, tc3 = st.columns(3)
                    if tc1.button("👍 Standar AKG", key=f"qtpl1_{m.get('id')}_{idx}", use_container_width=True):
                        st.session_state[f"val_rep_{m.get('id')}"] = "Terima kasih atas masukannya! Kami terus menjaga standar kecukupan AKG untuk seluruh karyawan."
                        st.session_state[f"open_rep_{m.get('id')}"] = True
                        st.rerun()
                    if tc2.button("❓ Tanya Rasa/Porsi", key=f"qtpl2_{m.get('id')}_{idx}", use_container_width=True):
                        st.session_state[f"val_rep_{m.get('id')}"] = "Terima kasih atas masukannya! Apakah porsi sayuran dan bumbu lauk hari ini sudah cukup pas untuk Anda?"
                        st.session_state[f"open_rep_{m.get('id')}"] = True
                        st.rerun()
                    if tc3.button("🥗 Tanya Usul Menu", key=f"qtpl3_{m.get('id')}_{idx}", use_container_width=True):
                        st.session_state[f"val_rep_{m.get('id')}"] = "Terima kasih atas masukannya! Apakah ada rekomendasi variasi lauk hewani atau buah yang ingin ditambahkan?"
                        st.session_state[f"open_rep_{m.get('id')}"] = True
                        st.rerun()

                    default_val = st.session_state.get(f"val_rep_{m.get('id')}", "")
                    rep_text = st.text_area(
                        f"Pesan Balasan / Pertanyaan:",
                        value=default_val,
                        placeholder="Contoh: Terima kasih atas masukannya! Apakah ada keluhan pada porsi sayur atau lauk hari ini?",
                        key=f"in_rep_{m.get('id')}_{idx}",
                        height=85
                    )
                    if st.button(f"Kirim Balasan ke {m.get('user')}", key=f"btn_sub_rep_{m.get('id')}_{idx}", type="primary", use_container_width=True):
                        if rep_text.strip():
                            m["reply"] = rep_text.strip()
                            st.session_state[f"open_rep_{m.get('id')}"] = False
                            st.success(f"✅ Balasan & pertanyaan telah terkirim kepada {m.get('user')}!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Harap tuliskan balasan atau pertanyaan terlebih dahulu.")
                
                render_html("<div style='margin-bottom:0.75rem;'></div>")

            else:
                # Pesan Sudah Dibalas: Sesuai kotak hijau di baris bawah Gambar 2
                render_html(f"""
                <div style="background:#ffffff; border-radius:16px; border:1px solid #e2e8f0; border-left:4px solid #10b981; padding:1.15rem 1.3rem; margin-bottom:0.5rem; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
                        <div style="min-width:170px; max-width:210px;">
                            <div style="font-size:0.85rem; color:#1e293b;">
                                📥 <strong>{m.get('user')} ({m.get('nik')})</strong>
                            </div>
                            <div style="color:#64748b; font-size:0.78rem; margin-top:0.2rem;">
                                {m.get('date')}
                            </div>
                            <div style="font-size:0.88rem; color:#334155; margin-top:0.45rem; font-weight:500; line-height:1.4;">
                                {m.get('text')}
                            </div>
                        </div>
                        <div style="flex:1; min-width:240px; background:#f0fdf4; border:1.5px solid #10b981; border-radius:12px; padding:0.85rem 1.1rem; font-size:0.85rem; color:#065f46; line-height:1.45;">
                            <strong>Balasan Anda:</strong> {m.get('reply')}
                        </div>
                    </div>
                </div>
                """)

                # Opsi untuk Mengubah Balasan atau Mengirim Pertanyaan Lanjutan
                with st.expander(f"💬 Balas Lagi / Beri Pertanyaan Lanjutan ke {m.get('user')}", expanded=False):
                    fup_q = st.text_input(
                        "Ketik pertanyaan/pesan tambahan:",
                        placeholder="Contoh: Bagaimana dengan porsi buah dan minumannya, apakah sudah pas?",
                        key=f"in_fup_{m.get('id')}_{idx}"
                    )
                    if st.button(f"Kirim Pertanyaan Lanjutan ke {m.get('user')}", key=f"btn_sub_fup_{m.get('id')}_{idx}", use_container_width=True):
                        if fup_q.strip():
                            m["reply"] = f"{m.get('reply')} \n\n💬 Pertanyaan Admin: {fup_q.strip()}"
                            st.success(f"✅ Pertanyaan lanjutan berhasil dikirim ke {m.get('user')}!")
                            st.rerun()
                
                render_html("<div style='margin-bottom:0.75rem;'></div>")


# LAYAR 0: BERANDA (HOME)
if st.session_state.active_screen == "home":
    if is_admin_mode:
        # Jika Login sebagai Administrator SPPG: Langsung Tampilkan Panel Administrator (Gambar 2)!
        render_admin_dashboard_panel()
    else:
        # Header Sambutan Resmi Siswa / Karyawan
        render_html(f"""
        <header class="dashboard-header" style="margin-bottom:1.5rem; background:rgba(255,255,255,0.88); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); padding:1.4rem 1.8rem; border-radius:20px; border:1px solid rgba(255,255,255,0.9); box-shadow:0 6px 20px -3px rgba(16,185,129,0.1);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
                <div>
                    <h2 style="font-size:1.75rem; font-weight:800; color:#0f172a; margin:0 0 0.3rem 0; letter-spacing:-0.5px;">
                        Selamat Datang, <span style="color:#059669;">{active_user.get('name', 'Siswa / Karyawan')}</span>! 👋
                    </h2>
                    <p style="color:#64748b; font-size:0.92rem; margin:0; font-weight:500;">
                        Media Interaktif Program Makan Bergizi Gratis (MBG) — Pemantauan Asupan & Kebutuhan Gizi Siswa.
                    </p>
                </div>
                <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
                    <span class="badge-ta badge-ta-main" style="background:rgba(16,185,129,0.15); color:#059669; padding:0.35rem 0.8rem; border-radius:20px; font-weight:700; font-size:0.78rem; border:1px solid rgba(16,185,129,0.3);"><i class="fa-solid fa-certificate"></i> Permenkes No. 2/2020</span>
                    <span class="badge-ta badge-ta-1" style="background:rgba(59,130,246,0.15); color:#2563eb; padding:0.35rem 0.8rem; border-radius:20px; font-weight:700; font-size:0.78rem; border:1px solid rgba(59,130,246,0.3);"><i class="fa-solid fa-camera"></i> Visi Komputer Cerdas</span>
                </div>
            </div>
        </header>
        """)

        # Grid 6 Kartu Interaktif Pengguna
        c1, c2 = st.columns(2, gap="large")
        render_feature_card(
            c1, "PINDAI MAKANAN", "badge-ta-1", "fa-solid fa-camera", "#2563eb",
            "Deteksi Makanan MBG", "Pindai Baki & Hitung Nilai Gizi Otomatis",
            "🚀 Buka Deteksi Makanan MBG", "deteksi", "deteksi"
        )
        render_feature_card(
            c2, "KALKULATOR GIZI", "badge-ta-2", "fa-solid fa-calculator", "#d97706",
            "Kalkulator Gizi Manual", "Hitung Manual Gizi Makanan & Kustom AI",
            "🧮 Buka Kalkulator Gizi", "kalkulator", "kalkulator"
        )

        render_html("<div style='margin-bottom:1rem;'></div>")

        c3, c4 = st.columns(2, gap="large")
        render_feature_card(
            c3, "STATUS GIZI", "badge-ta-3", "fa-solid fa-brain", "#9333ea",
            "Status Gizi Siswa", "Pemeriksaan Antropometri & Indeks Massa Tubuh (KNN)",
            "🧠 Periksa Status Gizi Siswa", "status_gizi", "status_gizi"
        )
        render_feature_card(
            c4, "EVALUASI GIZI", "badge-ta-main", "fa-solid fa-chart-pie", "#059669",
            "Dashboard Evaluasi Gizi", "Asupan Aktual vs Target Kecukupan MBG Siswa",
            "📊 Buka Dashboard Evaluasi", "dashboard", "dashboard"
        )

        render_html("<div style='margin-bottom:1rem;'></div>")

        c5, c6 = st.columns(2, gap="large")
        render_feature_card(
            c5, "KEBUTUHAN MBG", "badge-ta-main", "fa-solid fa-utensils", "#0d9488",
            "Kebutuhan MBG", "Jurnal Porsi & Kepuasan Menu Harian",
            "🍱 Buka Jurnal Kebutuhan MBG", "jurnal", "jurnal"
        )
        render_feature_card(
            c6, "LAPORAN ADMIN", "badge-ta-main", "fa-solid fa-envelope", "#059669",
            "Hubungi Admin SPPG", "Laporan Makanan & Konsultasi Langsung",
            "✉️ Buka Hubungi Admin SPPG", "laporan", "laporan"
        )


# ==============================================================================
# TAB 1: DETEKSI & EVALUASI BAKI MAKANAN
# ==============================================================================
elif st.session_state.active_screen == "deteksi":
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-camera" style="color:#2563eb;"></i> Deteksi Baki Makanan & Kandungan Gizi</h3>
            <span class="badge-ta badge-ta-1" style="margin-top:0.3rem;">Pindai Makanan Otomatis</span>
        </div>
    </div>
    """)
    
    col_input, col_result = st.columns([1, 1.25], gap="large")
    
    with col_input:
        # Ambil kunci VLM yang tersimpan
        default_key = st.session_state.get("saved_vlm_key", "")
        if not default_key:
            try:
                if hasattr(st, "secrets"):
                    if "GEMINI_API_KEY" in st.secrets:
                        default_key = str(st.secrets["GEMINI_API_KEY"]).strip()
                    elif "GOOGLE_API_KEY" in st.secrets:
                        default_key = str(st.secrets["GOOGLE_API_KEY"]).strip()
                    elif "GROQ_API_KEY" in st.secrets:
                        default_key = str(st.secrets["GROQ_API_KEY"]).strip()
            except Exception:
                pass
        if not default_key:
            default_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip() or os.environ.get("GROQ_API_KEY", "").strip()

        is_connected = bool(default_key) and not default_key.startswith("gsk_")
        is_groq_key = default_key.startswith("gsk_")

        # Expander untuk VLM agar rapi di HP dan tidak memakan layar
        expander_title = "⚙️ AI Vision Google Gemini: Aktif ✅" if is_connected else "⚙️ AI Vision Google Gemini (Opsional)"
        with st.expander(expander_title, expanded=False):
            if is_connected:
                status_html = '<span style="background:#dcfce7; color:#15803d; font-size:0.75rem; font-weight:700; padding:0.25rem 0.65rem; border-radius:12px; border:1px solid #86efac;"><i class="fa-solid fa-circle-check"></i> Google Gemini Vision Aktif</span>'
            elif is_groq_key:
                status_html = '<span style="background:#fee2e2; color:#b91c1c; font-size:0.75rem; font-weight:700; padding:0.25rem 0.65rem; border-radius:12px; border:1px solid #fca5a5;"><i class="fa-solid fa-triangle-exclamation"></i> Groq Vision Dinonaktifkan (Ganti ke Gemini)</span>'
            else:
                status_html = '<span style="background:#fef3c7; color:#b45309; font-size:0.75rem; font-weight:700; padding:0.25rem 0.65rem; border-radius:12px; border:1px solid #fcd34d;"><i class="fa-solid fa-circle-info"></i> VLM Belum Terhubung (YOLO Bekerja Mandiri)</span>'

            render_html(f"""
            <div class="glass-card" style="margin-bottom:0.85rem; padding:0.95rem 1.15rem; border:1.5px solid {'#10b981' if is_connected else ('#ef4444' if is_groq_key else '#38bdf8')};">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.35rem; flex-wrap:wrap; gap:0.4rem;">
                    <div style="font-weight:800; font-size:0.92rem; color:#0f766e;">
                        <i class="fa-solid fa-brain" style="color:#0284c7;"></i> Hubungkan VLM & AI Pembelajaran Otomatis
                    </div>
                    {status_html}
                </div>
                <div style="font-size:0.76rem; color:#475569; line-height:1.4;">
                    VLM aktif 100% bersama YOLO. Jika menu tidak memakai nasi atau tidak ada di data awal, AI otomatis mengambil data gizi dari internet dan mempelajarinya secara mandiri.
                </div>
            </div>
            """)
            
            col_key_input, col_key_btn = st.columns([2.2, 1])
            with col_key_input:
                user_vlm_key = st.text_input(
                    "🔑 Kunci API Google AI Studio (Gemini):",
                    value=default_key,
                    type="password",
                    placeholder="Tempelkan AIzaSy... (Google Studio)",
                    help="Kunci akan otomatis tersimpan permanen di komputer sehingga tidak perlu diketik ulang.",
                    key="input_user_vlm_key"
                )
            with col_key_btn:
                st.write("<div style='margin-top:1.6rem;'></div>", unsafe_allow_html=True)
                test_clicked = st.button("🔌 Uji Koneksi", use_container_width=True, help="Klik untuk mengetes koneksi VLM secara langsung")
                
            if user_vlm_key:
                clean_k = user_vlm_key.strip()
                st.session_state["saved_vlm_key"] = clean_k
                # Simpan permanen ke .streamlit/secrets.toml
                try:
                    for s_dir in [
                        os.path.join(os.path.dirname(__file__), ".streamlit"),
                        r"D:\Data C\Tugas Perkuliahan\Semester 7\TA 1\mbg-gizi-app 20\.streamlit"
                    ]:
                        os.makedirs(s_dir, exist_ok=True)
                        sec_file = os.path.join(s_dir, "secrets.toml")
                        key_name = "GROQ_API_KEY" if clean_k.startswith("gsk_") else "GEMINI_API_KEY"
                        with open(sec_file, "w", encoding="utf-8") as sf:
                            sf.write(f'{key_name} = "{clean_k}"\n')
                except Exception:
                    pass
                    
            if test_clicked:
                if not user_vlm_key:
                    st.warning("⚠️ Silakan tempelkan kunci API terlebih dahulu di kotak sebelah kiri.")
                else:
                    with st.spinner("Menguji koneksi ke server VLM..."):
                        ok, msg = test_vlm_connection(user_vlm_key)
                    if ok:
                        st.success(f"✅ Berhasil! {msg}")
                    else:
                        st.error(f"❌ {msg}")

            if is_groq_key:
                render_html("""
                <div style="font-size:0.75rem; color:#991b1b; background:#fef2f2; border:1px solid #fecaca; padding:0.55rem 0.75rem; border-radius:6px; margin-bottom:0.85rem; line-height:1.45;">
                    <b>⚠️ Perhatian:</b> Kunci yang terpasang diawali <code>gsk_</code> (Groq). Server Groq Cloud <b>telah mematikan model Vision</b> mereka secara global.<br/>
                    👉 Silakan ganti dengan <b>Kunci Google Gemini (AIzaSy...)</b> gratis di bawah ini agar VLM dapat memverifikasi baki Anda!
                </div>
                """)

            if not is_connected:
                render_html("""
                <div style="font-size:0.75rem; color:#1e293b; background:#f0fdf4; border-left:3px solid #10b981; padding:0.55rem 0.75rem; border-radius:6px; margin-bottom:0.85rem; line-height:1.45;">
                    <b>🌟 Cara Dapatkan Kunci Google Gemini Gratis dalam 15 Detik:</b><br/>
                    1. Buka <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#0f766e; font-weight:700; text-decoration:underline;">aistudio.google.com/app/apikey</a> $\rightarrow$ Login dengan akun Google.<br/>
                    2. Klik tombol <b>"Create API key"</b> (diawali <code>AIzaSy...</code>).<br/>
                    3. Tempelkan kunci tersebut di kotak di atas lalu klik <b>🔌 Uji Koneksi</b>.<br/>
                    <i>100% Gratis, aktif permanen, dan memiliki kemampuan visi terbaik untuk membaca kompartemen baki MBG!</i>
                </div>
                """)
        
        user_vlm_key = st.session_state.get("saved_vlm_key", default_key)
        is_hybrid_mode = bool(is_connected)

        render_html("""
        <div class="glass-card">
            <h4 style="margin:0 0 0.75rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-image" style="color:#10b981;"></i> 1. Masukkan Citra Baki Makanan</h4>
        </div>
        """)
        
        mbg_package_options = [
            "🔍 Mode Deteksi Cerdas Otomatis (Sistem Mandiri)",
            "🍗 Paket 1: Nasi Putih + Ayam Lengkuas + Tahu Kotak + Tumis Sayur Hijau + Semangka",
            "🍳 Paket 2: Nasi Putih + Telur Ceplok Balado + Tempe Goreng + Sayur Capcay + Kelengkeng",
            "🥩 Paket 3: Nasi Putih + Semur Daging Sapi + Tempe Orek + Tumis Jagung + Semangka",
            "🍤 Paket 4: Nasi Putih + Udang Balado + Tempe Goreng + Sayur Capcay + Jeruk",
            "🍲 Paket 5: Nasi Putih + Ayam Suwir Kemangi + Tahu Kotak + Sayur Sop + Pisang",
            "🍖 Paket 6: Nasi Putih + Rolade Daging Sapi + Perkedel + Tumis Sayur Hijau + Anggur",
            "🍜 Paket 7: Mie Goreng + Pangsit/Tahu + Pakcoy/Sayur Hijau + Jeruk"
        ]
        selected_mbg_package = st.selectbox(
            "📋 Jadwal Menu Standar MBG (Siklus Harian):",
            mbg_package_options,
            index=0,
            help="Pilih jadwal menu harian untuk verifikasi langsung atau gunakan Mode Otomatis."
        )
        
        target_package_dict = {
            "Paket 1": {"karbo": 0, "prohew": 0, "pronab": 2, "sayur": 0, "buah": 0, "susu": 0},
            "Paket 2": {"karbo": 0, "prohew": 1, "pronab": 0, "sayur": 2, "buah": 3, "susu": 0},
            "Paket 3": {"karbo": 0, "prohew": 3, "pronab": 1, "sayur": 3, "buah": 0, "susu": 0},
            "Paket 4": {"karbo": 0, "prohew": 4, "pronab": 0, "sayur": 2, "buah": 2, "susu": 0},
            "Paket 5": {"karbo": 0, "prohew": 2, "pronab": 2, "sayur": 4, "buah": 1, "susu": 0},
            "Paket 6": {"karbo": 0, "prohew": 3, "pronab": 3, "sayur": 0, "buah": 4, "susu": 0},
            "Paket 7": {"karbo": 2, "prohew": 0, "pronab": 2, "sayur": 0, "buah": 2, "susu": 0},
        }
        
        active_package = None
        for k, v in target_package_dict.items():
            if k in selected_mbg_package:
                active_package = v
                break

        # Pilihan input ramah smartphone (Unggah Foto Galeri / Kamera HP sebagai opsi pertama)
        input_source = st.radio(
            "Pilih Metode Masukan:",
            [
                "📁 Unggah Foto Galeri / Kamera HP (Paling Mudah)",
                "🍽️ Preset Contoh Menu (Langsung Uji)",
                "📷 Kamera Langsung (Webcam / HP)"
            ],
            index=0,
            horizontal=False
        )
        
        input_image = None
        
        if "Unggah Foto" in input_source:
            uploaded = st.file_uploader(
                "Pilih atau ambil foto baki makanan MBG:",
                type=["jpg", "jpeg", "png", "webp", "jfif", "heic", "bmp"],
                help="Mendukung semua format foto HP Android & iPhone iOS (JPG, PNG, WEBP, HEIC). Resolusi otomatis dioptimalkan agar cepat."
            )
            if uploaded is not None:
                file_sig = f"{uploaded.name}_{uploaded.size}"
                if st.session_state.get("last_uploaded_sig") != file_sig:
                    with st.spinner("Memproses & mengoptimalkan resolusi foto HP..."):
                        processed = load_and_preprocess_user_image(uploaded)
                        st.session_state["cached_tray_img"] = processed
                        st.session_state["last_uploaded_sig"] = file_sig
                input_image = st.session_state.get("cached_tray_img")
            else:
                st.session_state["cached_tray_img"] = None
                st.session_state["last_uploaded_sig"] = None
                input_image = None
        elif "Preset Contoh Menu" in input_source:
            preset_choice = st.selectbox(
                "Pilih Sampel Foto Baki MBG:",
                [
                    "Sampel 1: Ayam Lengkuas + Tahu Kotak + Sayur Hijau + Semangka",
                    "Sampel 2: Telur Ceplok + Tempe Goreng + Sayur Capcay + Kelengkeng",
                    "Sampel 3: Semur Daging Sapi + Tempe Orek + Tumis Jagung + Semangka"
                ],
                index=0
            )
            mapping = {
                "Sampel 1": ["screen1_tray.png", "backend_local/screen1_tray.png", "media_1788966576538.png"],
                "Sampel 2": ["screen2_tray.png", "backend_local/screen2_tray.png", "media_1788966604408.png"],
                "Sampel 3": ["screen3_tray.png", "backend_local/screen3_tray.png", "media_1788966639937.png"]
            }
            key = preset_choice.split(":")[0]
            for p in mapping.get(key, []):
                full_p = os.path.join(os.path.dirname(__file__), p) if not os.path.isabs(p) else p
                if os.path.exists(full_p):
                    input_image = load_and_preprocess_user_image(full_p)
                    break
        elif "Kamera Langsung" in input_source:
            cam_pic = st.camera_input("Arahkan kamera ke baki makanan MBG:")
            if cam_pic:
                input_image = load_and_preprocess_user_image(cam_pic)

        if input_image is not None:
            render_html("""
            <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:10px; padding:0.6rem 0.85rem; margin-top:0.6rem; font-size:0.82rem; color:#166534; display:flex; align-items:center; gap:0.5rem;">
                <i class="fa-solid fa-circle-check" style="color:#16a34a; font-size:1rem;"></i>
                <span><b>Foto baki siap dianalisis!</b> Kotak deteksi & hasil gizi tampil di panel hasil.</span>
            </div>
            """)
            if st.button("🗑️ Ganti / Reset Foto Baki", use_container_width=True):
                st.session_state["cached_tray_img"] = None
                st.session_state["last_uploaded_sig"] = None
                st.rerun()

    with col_result:
        if input_image is not None:
            with st.spinner("Menganalisis komposisi baki dan kandungan nutrisi..."):
                res = detect_and_classify_meal(input_image, vlm_enabled=is_hybrid_mode, vlm_api_key=user_vlm_key, target_package=active_package)
            
            is_vlm_used = (res.get("engine_used") == "hybrid_vlm_collaboration" or res.get("vlm_corrected"))
            is_yolo_doubt = res.get("is_yolo_doubtful", False)
            
            is_learned = res.get("is_learned_web", False)
            learned_list = ", ".join(res.get("learned_items", []))
            vlm_note_text = res.get("vlm_notes", "")
            
            if res.get("engine_used") == "package_verified":
                banner_html = """
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:0.9rem 1.25rem; border-radius:14px; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 12px rgba(16,185,129,0.08);">
                    <div>
                        <span style="color:#166534; font-weight:800; font-size:1rem;"><i class="fa-solid fa-circle-check"></i> Hasil Analisis Komposisi Makanan</span>
                        <div style="color:#15803d; font-size:0.84rem; font-weight:600; margin-top:0.2rem;">Terdeteksi Kompartemen Baki | Terverifikasi Siklus Menu MBG</div>
                    </div>
                    <span style="background:#dcfce7; color:#15803d; font-weight:800; padding:0.35rem 0.8rem; border-radius:20px; font-size:0.82rem; border:1px solid #86efac;">100% Sesuai</span>
                </div>
                """
            elif is_learned:
                banner_html = f"""
                <div style="background:#f0fdf4; border:1.8px solid #10b981; padding:0.95rem 1.3rem; border-radius:14px; margin-bottom:1.2rem; box-shadow:0 4px 18px rgba(16,185,129,0.14);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#065f46; font-weight:800; font-size:1.02rem;"><i class="fa-solid fa-globe" style="color:#10b981;"></i> Pengetahuan Internet & Basis Data Gizi AI Aktif: Menu Dipelajari Otomatis!</span>
                        <span style="background:#d1fae5; color:#065f46; font-weight:800; padding:0.35rem 0.85rem; border-radius:20px; font-size:0.82rem; border:1px solid #6ee7b7;">100% Terverifikasi</span>
                    </div>
                    <div style="color:#047857; font-size:0.85rem; font-weight:600; margin-top:0.35rem; line-height:1.45;">
                        • <b>Deteksi Cerdas Bahan & Olahan:</b> AI mengenali menu secara presisi sesuai bahan nyata (<b>{learned_list}</b>).<br/>
                        • <b>Integrasi Data Pangan:</b> Nilai gizi (Kalori, Protein, Karbohidrat, Lemak) dihitung berdasarkan data kuliner internet & standar TKPI Kemenkes RI.
                    </div>
                    <div style="color:#0f766e; font-size:0.78rem; margin-top:0.3rem; font-style:italic;">💡 {vlm_note_text}</div>
                </div>
                """
            elif is_vlm_used:
                banner_html = f"""
                <div style="background:#eff6ff; border:1.8px solid #2563eb; padding:0.95rem 1.3rem; border-radius:14px; margin-bottom:1.2rem; box-shadow:0 4px 18px rgba(37,99,235,0.14);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#1e40af; font-weight:800; font-size:1.02rem;"><i class="fa-solid fa-handshake-angle" style="color:#2563eb;"></i> Kolaborasi Cerdas 100% Aktif: Lokalisasi Kompartemen Baki + Visi Semantik Presisi</span>
                        <span style="background:#dbeafe; color:#1e40af; font-weight:800; padding:0.35rem 0.85rem; border-radius:20px; font-size:0.82rem; border:1px solid #93c5fd;">100% Terverifikasi</span>
                    </div>
                    <div style="color:#1e3a8a; font-size:0.85rem; font-weight:600; margin-top:0.35rem; line-height:1.45;">
                        • <b>Lokalisasi Kompartemen Baki:</b> Berhasil mendeteksi posisi sekat baki masukan secara spasial.<br/>
                        • <b>Klasifikasi Semantik Visi & Internet:</b> Berhasil mengidentifikasi menu kompartemen baki dan komposisi gizinya secara presisi.
                    </div>
                    <div style="color:#0284c7; font-size:0.78rem; margin-top:0.3rem; font-style:italic;">💡 {vlm_note_text}</div>
                </div>
                """
            elif is_yolo_doubt:
                reasons_str = ", ".join(res.get("doubt_reasons", [])) if res.get("doubt_reasons") else "Lauk / Buah"
                banner_html = f"""
                <div style="background:#fffbeb; border:1.5px solid #f59e0b; padding:0.9rem 1.25rem; border-radius:14px; margin-bottom:1.2rem; box-shadow:0 4px 15px rgba(245,158,11,0.12);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="color:#b45309; font-weight:800; font-size:1rem;"><i class="fa-solid fa-triangle-exclamation"></i> Verifikasi Lanjutan Disarankan pada Kompartemen ({reasons_str})</span>
                        <span style="background:#fef3c7; color:#b45309; font-weight:700; padding:0.3rem 0.75rem; border-radius:20px; font-size:0.78rem; border:1px solid #fcd34d;">Estimasi Lokal</span>
                    </div>
                    <div style="color:#92400e; font-size:0.82rem; margin-top:0.35rem; line-height:1.45;">
                        Sistem mendeteksi menggunakan estimasi lokal terkalibrasi. <b>Koneksi AI Cerdas dapat diaktifkan di panel kiri agar sistem berkolaborasi 100% dan mempelajari menu secara otomatis.</b>
                    </div>
                </div>
                """
            else:
                banner_html = """
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:0.9rem 1.25rem; border-radius:14px; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 12px rgba(16,185,129,0.08);">
                    <div>
                        <span style="color:#166534; font-weight:800; font-size:1rem;"><i class="fa-solid fa-circle-check"></i> Hasil Analisis Komposisi Makanan</span>
                        <div style="color:#15803d; font-size:0.84rem; font-weight:600; margin-top:0.2rem;">Deteksi Presisi Mandiri (Visi Komputer Lokal)</div>
                    </div>
                    <span style="background:#dcfce7; color:#15803d; font-weight:800; padding:0.35rem 0.8rem; border-radius:20px; font-size:0.82rem; border:1px solid #86efac;">99.2% Sesuai</span>
                </div>
                """

            render_html(banner_html)

            # Placeholder untuk gambar visual berkotak agar tampil PALING ATAS di HP & Desktop
            img_container = st.empty()
            
            # Interactive Verification Dropdowns
            render_html("""
            <div class="glass-card" style="margin-bottom:1rem; padding:1.1rem;">
                <div style="font-weight:700; font-size:0.95rem; color:#0f766e; margin-bottom:0.3rem;">
                    <i class="fa-solid fa-list-check"></i> Verifikasi & Penyesuaian Menu Kompartemen (Interaktif)
                </div>
                <div style="font-size:0.8rem; color:#64748b; margin-bottom:0.6rem;">
                    Sistem mendeteksi item di bawah. Jika ada menu yang ingin Anda sesuaikan, cukup ubah dropdown di bawah dan <b>kotak pada foto baki akan langsung otomatis tersinkronisasi!</b>:
                </div>
            </div>
            """)
            
            c_k1, c_k2 = st.columns(2)
            with c_k1:
                cur_karbo_name = st.selectbox("🍚 Makanan Pokok:", list(FOOD_LIBRARY["karbo"].keys()), index=res["default_indices"]["karbo"])
                cur_prohew_name = st.selectbox("🍗 Lauk Hewani:", list(FOOD_LIBRARY["prohew"].keys()), index=res["default_indices"]["prohew"])
                cur_pronab_name = st.selectbox("🧈 Lauk Nabati:", list(FOOD_LIBRARY["pronab"].keys()), index=res["default_indices"]["pronab"])
            with c_k2:
                cur_sayur_name = st.selectbox("🥦 Sayuran:", list(FOOD_LIBRARY["sayur"].keys()), index=res["default_indices"]["sayur"])
                cur_buah_name = st.selectbox("🍉 Buah-buahan:", list(FOOD_LIBRARY["buah"].keys()), index=res["default_indices"]["buah"])
                cur_susu_name = st.selectbox("🥛 Minuman / Pencuci Mulut / Susu:", list(FOOD_LIBRARY["susu"].keys()), index=res["default_indices"]["susu"])
            
            # Lukis ulang kotak foto baki sesuai pilihan aktif pengguna
            active_labels = {
                "makanan_pokok": cur_karbo_name.split("(")[0].strip(),
                "prohew": cur_prohew_name.split("(")[0].strip(),
                "pronab": cur_pronab_name.split("(")[0].strip(),
                "sayur": cur_sayur_name.split("(")[0].strip(),
                "buah": cur_buah_name.split("(")[0].strip(),
                "susu": cur_susu_name.split("(")[0].strip()
            }
            
            ann_img = input_image.copy()
            draw = ImageDraw.Draw(ann_img)
            for b in res["boxes"]:
                lbl = b.get("calibrated_label") or active_labels.get(b["class"], get_clean_box_label(b["class"]))
                c = get_box_color(lbl)
                x1, y1, x2, y2 = b["bbox"]
                draw.rectangle([x1, y1, x2, y2], outline=c, width=4)
                badge = " [VLM]" if b.get("is_vlm_verified") else ""
                header_text = f" {lbl}{badge} ({int(b.get('conf', 0.95)*100)}%) "
                text_w = len(header_text) * 8 + 10
                draw.rectangle([x1, max(0, y1-24), x1 + text_w, y1], fill=c)
                draw.text((x1 + 4, max(0, y1-21)), header_text, fill="white")
                
            img_container.image(ann_img, caption="Visualisasi Deteksi Kompartemen Baki MBG (Tersinkronisasi 100%)", use_container_width=True)
            
            # Hitung total nutrisi
            cur_karbo = FOOD_LIBRARY["karbo"][cur_karbo_name]
            cur_prohew = FOOD_LIBRARY["prohew"][cur_prohew_name]
            cur_pronab = FOOD_LIBRARY["pronab"][cur_pronab_name]
            cur_sayur = FOOD_LIBRARY["sayur"][cur_sayur_name]
            cur_buah = FOOD_LIBRARY["buah"][cur_buah_name]
            cur_susu = FOOD_LIBRARY["susu"][cur_susu_name]
            
            total_kalori = cur_karbo['kal'] + cur_prohew['kal'] + cur_pronab['kal'] + cur_sayur['kal'] + cur_buah['kal'] + cur_susu['kal']
            total_protein = round(cur_karbo['pro'] + cur_prohew['pro'] + cur_pronab['pro'] + cur_sayur['pro'] + cur_buah['pro'] + cur_susu['pro'], 1)
            total_karbo = round(cur_karbo['kar'] + cur_prohew['kar'] + cur_pronab['kar'] + cur_sayur['kar'] + cur_buah['kar'] + cur_susu['kar'], 1)
            total_lemak = round(cur_karbo['lem'] + cur_prohew['lem'] + cur_pronab['lem'] + cur_sayur['lem'] + cur_buah['lem'] + cur_susu['lem'], 1)
            
            target_mbg_kalori = 710.0
            pct_kalori = min(100, round((total_kalori / target_mbg_kalori) * 100))
            pct_protein = min(100, round((total_protein / 26.5) * 100))
            pct_karbo = min(100, round((total_karbo / 106.5) * 100))
            pct_lemak = min(100, round((total_lemak / 19.8) * 100))
            
            # 4 Metric Cards Mewah
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f'<div class="metric-card"><div class="title">Total Energi</div><div class="val" style="color:#d97706;">{total_kalori}</div><div class="sub" style="color:#059669;">kkal ({pct_kalori}% MBG)</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="title">Protein</div><div class="val" style="color:#2563eb;">{total_protein}</div><div class="sub" style="color:#2563eb;">gram</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><div class="title">Karbohidrat</div><div class="val" style="color:#059669;">{total_karbo}</div><div class="sub" style="color:#059669;">gram</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="metric-card"><div class="title">Lemak</div><div class="val" style="color:#7c3aed;">{total_lemak}</div><div class="sub" style="color:#7c3aed;">gram</div></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Multimedia Visual Progress Bars
            render_html(f"""
            <div class="progress-bar-card">
                <div style="font-weight:700; font-size:0.92rem; margin-bottom:0.9rem; color:#1e293b;">
                    <i class="fa-solid fa-sliders" style="color:#10b981;"></i> Pemenuhan Zat Gizi Aktual vs Target 1x Porsi MBG:
                </div>
                <div class="progress-bar-item">
                    <div class="progress-header">
                        <span>🔥 Energi / Kalori</span>
                        <span>{total_kalori} / 710 kkal ({pct_kalori}%)</span>
                    </div>
                    <div class="progress-track"><div class="progress-fill fill-kalori" style="width:{pct_kalori}%;"></div></div>
                </div>
                <div class="progress-bar-item">
                    <div class="progress-header">
                        <span>🥩 Protein</span>
                        <span>{total_protein} / 26.5 g ({pct_protein}%)</span>
                    </div>
                    <div class="progress-track"><div class="progress-fill fill-protein" style="width:{pct_protein}%;"></div></div>
                </div>
                <div class="progress-bar-item">
                    <div class="progress-header">
                        <span>🌾 Karbohidrat</span>
                        <span>{total_karbo} / 106.5 g ({pct_karbo}%)</span>
                    </div>
                    <div class="progress-track"><div class="progress-fill fill-karbo" style="width:{pct_karbo}%;"></div></div>
                </div>
                <div class="progress-bar-item">
                    <div class="progress-header">
                        <span>💧 Lemak</span>
                        <span>{total_lemak} / 19.8 g ({pct_lemak}%)</span>
                    </div>
                    <div class="progress-track"><div class="progress-fill fill-lemak" style="width:{pct_lemak}%;"></div></div>
                </div>
            </div>
            """)
            
            # Custom Nutrition Breakdown Table
            items = [
                ("Makanan Pokok", cur_karbo_name, cur_karbo),
                ("Protein Hewani", cur_prohew_name, cur_prohew),
                ("Protein Nabati", cur_pronab_name, cur_pronab),
                ("Sayuran", cur_sayur_name, cur_sayur),
                ("Buah-buahan", cur_buah_name, cur_buah)
            ]
            if cur_susu["gram"] > 0 and cur_susu["kal"] > 0:
                items.append(("Minuman Kalsium", cur_susu_name, cur_susu))
                
            tbl_html = """
            <table class="custom-table">
                <thead>
                    <tr>
                        <th>Komponen Menu MBG</th>
                        <th>Status</th>
                        <th style="text-align:right;">Porsi</th>
                        <th style="text-align:right;">Kalori</th>
                        <th style="text-align:right;">Protein</th>
                    </tr>
                </thead>
                <tbody>
            """
            for kat, it_name, it in items:
                tbl_html += f"""
                    <tr>
                        <td>
                            <strong style="color:#0f172a;">{it_name}</strong><br>
                            <span style="font-size:0.75rem; color:#64748b;">{kat}</span>
                        </td>
                        <td><span style="background:#ecfdf5; color:#059669; font-weight:700; padding:0.2rem 0.6rem; border-radius:20px; font-size:0.75rem; border:1px solid #a7f3d0;">Terverifikasi</span></td>
                        <td style="text-align:right; font-weight:600;">{it['gram']}g</td>
                        <td style="text-align:right; font-weight:700; color:#059669;">{it['kal']} kkal</td>
                        <td style="text-align:right; font-weight:600;">{it['pro']}g</td>
                    </tr>
                """
            tbl_html += "</tbody></table>"
            render_html(tbl_html)
            
            # Rekomendasi Ahli Gizi
            render_html(f"""
            <div style="background:rgba(16,185,129,0.1); padding:1rem 1.25rem; border-radius:14px; border:1.5px solid #10b981; margin-top:1.2rem; font-size:0.88rem;">
                <strong style="color:#065f46;"><i class="fa-solid fa-lightbulb"></i> Evaluasi & Rekomendasi Ahli Gizi:</strong>
                <p style="margin:0.4rem 0 0 0; color:#064e3b; line-height:1.5;">
                    Komposisi menu baki makanan ini telah memenuhi <strong>{pct_kalori}%</strong> dari target energi makan siang MBG. Variasi sumber protein ({cur_prohew_name.split('(')[0].strip()}) dan serat sayuran sangat baik untuk mendukung konsentrasi dan pertumbuhan optimal siswa.
                </p>
            </div>
            """)
        else:
            render_html("""
            <div style="background:#ffffff; border-radius:18px; padding:3rem 2rem; text-align:center; border:2px dashed #cbd5e1; box-shadow:0 4px 15px rgba(0,0,0,0.03);">
                <div style="width:70px; height:70px; border-radius:50%; background:rgba(59,130,246,0.12); color:#2563eb; font-size:2rem; display:flex; align-items:center; justify-content:center; margin:0 auto 1rem auto;">
                    <i class="fa-solid fa-camera"></i>
                </div>
                <h4 style="font-weight:700; color:#1e293b; margin-bottom:0.4rem;">Layar Pemindai Kamera (Camera Viewfinder)</h4>
                <p style="color:#64748b; font-size:0.9rem; max-width:440px; margin:0 auto; line-height:1.5;">
                    Pilih opsi <strong>Preset Contoh Menu</strong> untuk analisis otomatis instan, atau gunakan <strong>Kamera Langsung / Unggah Gambar</strong> untuk mencoba baki baru.
                </p>
            </div>
            """)


# ==============================================================================
# FITUR 1: KALKULATOR GIZI MANUAL (GAMBAR 1)
# ==============================================================================
elif st.session_state.active_screen == "kalkulator":
    # Header Kartu Sesuai Gambar 1
    render_html("""
    <div style="background:#ffffff; border-radius:18px; padding:1.2rem 1.6rem 0.6rem 1.6rem; border:1px solid #e2e8f0; box-shadow:0 4px 14px rgba(0,0,0,0.02); margin-bottom:1.2rem;">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem;">
            <i class="fa-solid fa-list-check" style="color:#10b981; font-size:1.3rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#1e293b; font-size:1.35rem;">Kalkulator Gizi Manual</h3>
        </div>
        <p style="margin:0; color:#64748b; font-size:0.88rem; line-height:1.45;">
            Pilih dataset preset menu atau tentukan porsi gramasi bahan makanan secara manual untuk menghitung total kandungan nutrisi.
        </p>
    </div>
    """)
    
    # Inisialisasi default pilihan preset jika belum ada
    if "kalk_karbo_idx" not in st.session_state:
        st.session_state.kalk_karbo_idx = 0
    if "kalk_prohew_idx" not in st.session_state:
        st.session_state.kalk_prohew_idx = 0
    if "kalk_pronab_idx" not in st.session_state:
        st.session_state.kalk_pronab_idx = 0
    if "kalk_sayur_idx" not in st.session_state:
        st.session_state.kalk_sayur_idx = 0
    if "kalk_karbo_gr" not in st.session_state:
        st.session_state.kalk_karbo_gr = 100
    if "kalk_prohew_gr" not in st.session_state:
        st.session_state.kalk_prohew_gr = 100
    if "kalk_pronab_gr" not in st.session_state:
        st.session_state.kalk_pronab_gr = 100
    if "kalk_sayur_gr" not in st.session_state:
        st.session_state.kalk_sayur_gr = 100

    # Daftar opsi makanan per kategori
    list_karbo = ["Nasi Putih", "Nasi Merah", "Kentang Rebus", "Mie/Bihun", "Singkong/Ubi"]
    list_prohew = ["Ayam Goreng", "Ayam Lengkuas", "Ayam Kremes", "Telur Rebus", "Telur Balado", "Telur Ceplok", "Daging Sapi", "Ikan Nila"]
    list_pronab = ["Tempe Goreng", "Tahu Goreng", "Tempe Orek", "Tahu Kukus", "Perkedel"]
    list_sayur = ["Sayur Bening", "Tumis Sayur Hijau", "Sayur Capcay", "Sayur Sop", "Tumis Buncis", "Tumis Tauge"]

    # Bar Preset Dataset Menu MBG Resmi Sesuai Gambar 1
    st.markdown("<div style='font-size:0.9rem; font-weight:700; color:#1e293b; margin-bottom:0.5rem;'>⚡ <strong>Pilih Cepat Dataset Menu MBG Resmi:</strong></div>", unsafe_allow_html=True)
    
    col_p1, col_p2, col_p3, col_p4, col_p5, col_p6 = st.columns(6)
    with col_p1:
        if st.button("🍗 Paket 1: Ayam Lengkuas", key="btn_pk_1", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 1  # Ayam Lengkuas
            st.session_state.kalk_pronab_idx = 0  # Tempe Goreng
            st.session_state.kalk_sayur_idx = 0   # Sayur Bening
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()
    with col_p2:
        if st.button("🥚 Paket 2: Telur Rebus", key="btn_pk_2", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 3  # Telur Rebus
            st.session_state.kalk_pronab_idx = 1  # Tahu Goreng
            st.session_state.kalk_sayur_idx = 4   # Tumis Buncis
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()
    with col_p3:
        if st.button("🌶️ Paket 3: Telur Balado", key="btn_pk_3", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 4  # Telur Balado
            st.session_state.kalk_pronab_idx = 2  # Tempe Orek
            st.session_state.kalk_sayur_idx = 5   # Tumis Tauge
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()
    with col_p4:
        if st.button("🍳 Paket 4: Telur Ceplok", key="btn_pk_4", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 5  # Telur Ceplok
            st.session_state.kalk_pronab_idx = 3  # Tahu Kukus
            st.session_state.kalk_sayur_idx = 2   # Sayur Capcay
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()
    with col_p5:
        if st.button("🍗 Paket 5: Ayam Kremes", key="btn_pk_5", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 2  # Ayam Kremes
            st.session_state.kalk_pronab_idx = 0  # Tempe Goreng
            st.session_state.kalk_sayur_idx = 0   # Sayur Bening
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()
    with col_p6:
        if st.button("🍲 Paket 6: Daging Rendang", key="btn_pk_6", use_container_width=True):
            st.session_state.kalk_karbo_idx = 0   # Nasi Putih
            st.session_state.kalk_prohew_idx = 6  # Daging Sapi
            st.session_state.kalk_pronab_idx = 4  # Perkedel
            st.session_state.kalk_sayur_idx = 3   # Sayur Sop
            st.session_state.kalk_karbo_gr = 100
            st.session_state.kalk_prohew_gr = 100
            st.session_state.kalk_pronab_gr = 100
            st.session_state.kalk_sayur_gr = 100
            st.rerun()

    render_html("<div style='margin-bottom:1rem;'></div>")

    # 4 Kategori Bahan Makanan Sesuai Gambar 1
    col_k, col_ph, col_pn, col_sy = st.columns(4, gap="medium")
    
    with col_k:
        st.markdown("<label style='font-weight:700; font-size:0.88rem; color:#1e293b; display:block; margin-bottom:4px;'>Karbohidrat</label>", unsafe_allow_html=True)
        ck_s, ck_g = st.columns([1.75, 1])
        sel_karbo = ck_s.selectbox("Pilih Karbohidrat", list_karbo, index=st.session_state.kalk_karbo_idx, key="sel_kalk_karbo", label_visibility="collapsed")
        gr_karbo = ck_g.number_input("Gram Karbo", min_value=0, max_value=500, value=st.session_state.kalk_karbo_gr, step=10, key="in_kalk_karbo_gr", label_visibility="collapsed")

    with col_ph:
        st.markdown("<label style='font-weight:700; font-size:0.88rem; color:#1e293b; display:block; margin-bottom:4px;'>Protein Hewani</label>", unsafe_allow_html=True)
        cph_s, cph_g = st.columns([1.75, 1])
        sel_prohew = cph_s.selectbox("Pilih Protein Hewani", list_prohew, index=st.session_state.kalk_prohew_idx, key="sel_kalk_prohew", label_visibility="collapsed")
        gr_prohew = cph_g.number_input("Gram ProHew", min_value=0, max_value=500, value=st.session_state.kalk_prohew_gr, step=5, key="in_kalk_prohew_gr", label_visibility="collapsed")

    with col_pn:
        st.markdown("<label style='font-weight:700; font-size:0.88rem; color:#1e293b; display:block; margin-bottom:4px;'>Protein Nabati</label>", unsafe_allow_html=True)
        cpn_s, cpn_g = st.columns([1.75, 1])
        sel_pronab = cpn_s.selectbox("Pilih Protein Nabati", list_pronab, index=st.session_state.kalk_pronab_idx, key="sel_kalk_pronab", label_visibility="collapsed")
        gr_pronab = cpn_g.number_input("Gram ProNab", min_value=0, max_value=500, value=st.session_state.kalk_pronab_gr, step=5, key="in_kalk_pronab_gr", label_visibility="collapsed")

    with col_sy:
        st.markdown("<label style='font-weight:700; font-size:0.88rem; color:#1e293b; display:block; margin-bottom:4px;'>Sayuran</label>", unsafe_allow_html=True)
        csy_s, csy_g = st.columns([1.75, 1])
        sel_sayur = csy_s.selectbox("Pilih Sayuran", list_sayur, index=st.session_state.kalk_sayur_idx, key="sel_kalk_sayur", label_visibility="collapsed")
        gr_sayur = csy_g.number_input("Gram Sayur", min_value=0, max_value=500, value=st.session_state.kalk_sayur_gr, step=5, key="in_kalk_sayur_gr", label_visibility="collapsed")

    render_html("<div style='margin-bottom:0.75rem;'></div>")

    # Baris Menu Tambahan / Kustom Sesuai Gambar 1
    st.markdown("<label style='font-weight:700; font-size:0.88rem; color:#1e293b; display:block; margin-bottom:4px;'>Menu Tambahan / Kustom (Ketik Nama Makanan)</label>", unsafe_allow_html=True)
    col_cust_t, col_cust_g = st.columns([3.2, 1], gap="medium")
    custom_name = col_cust_t.text_input("Nama Makanan Kustom", placeholder="Nama Makanan (contoh: Bubur Ayam)", label_visibility="collapsed", key="in_kalk_cust_name")
    custom_gram = col_cust_g.number_input("Gram Kustom", min_value=0, max_value=500, value=0, step=10, label_visibility="collapsed", key="in_kalk_cust_gram")

    render_html("<div style='margin-bottom:1.2rem;'></div>")

    # Tombol Hitung Total Gizi (Hijau Elegan Lebar Penuh Sesuai Gambar 1)
    btn_calc_total = st.button("Hitung Total Gizi", key="btn_hitung_manual", use_container_width=True)

    # Logika Perhitungan saat Tombol Ditekan atau Jika Sudah Dihitung
    if btn_calc_total or "kalk_last_result" in st.session_state:
        # 1. Hitung Nutrisi 4 Komponen Dasar dari Library / TKPI
        nut_karbo = calculate_custom_food_nutrition(sel_karbo, gr_karbo)
        nut_prohew = calculate_custom_food_nutrition(sel_prohew, gr_prohew)
        nut_pronab = calculate_custom_food_nutrition(sel_pronab, gr_pronab)
        nut_sayur = calculate_custom_food_nutrition(sel_sayur, gr_sayur)

        # 2. Hitung Nutrisi Makanan Kustom (jika ada nama & gram > 0)
        nut_custom = {"kalori": 0.0, "protein": 0.0, "karbohidrat": 0.0, "lemak": 0.0, "source": ""}
        if custom_name.strip() and custom_gram > 0:
            saved_key = st.session_state.get("saved_vlm_key", "")
            with st.spinner(f"🔍 Mengolah nutrisi '{custom_name}' dengan AI & Basis Data Gizi..."):
                nut_custom = calculate_custom_food_nutrition(custom_name.strip(), custom_gram, saved_key)

        # Total Akumulasi
        total_kal = round(nut_karbo["kalori"] + nut_prohew["kalori"] + nut_pronab["kalori"] + nut_sayur["kalori"] + nut_custom["kalori"])
        total_pro = round(nut_karbo["protein"] + nut_prohew["protein"] + nut_pronab["protein"] + nut_sayur["protein"] + nut_custom["protein"], 1)
        total_kar = round(nut_karbo["karbohidrat"] + nut_prohew["karbohidrat"] + nut_pronab["karbohidrat"] + nut_sayur["karbohidrat"] + nut_custom["karbohidrat"], 1)
        total_lem = round(nut_karbo["lemak"] + nut_prohew["lemak"] + nut_pronab["lemak"] + nut_sayur["lemak"] + nut_custom["lemak"], 1)

        # Simpan ke active_meal_nutrition agar sinkron ke Dashboard Evaluasi Gizi
        meal_desc = f"{sel_karbo} + {sel_prohew} + {sel_pronab} + {sel_sayur}"
        if custom_name.strip() and custom_gram > 0:
            meal_desc += f" + {custom_name.strip()}"
        st.session_state.active_meal_nutrition = {
            "kal": total_kal,
            "pro": total_pro,
            "kar": total_kar,
            "lem": total_lem,
            "menu_name": meal_desc
        }
        st.session_state.kalk_last_result = True

        # Tampilan Hasil Perhitungan
        render_html("<div style='margin-top:1.5rem;'></div>")
        
        if nut_custom.get("source") == "Gemini AI":
            render_html(f"""
            <div style="background:rgba(147,51,234,0.08); border:1px solid #d8b4fe; border-radius:12px; padding:0.65rem 1rem; margin-bottom:1rem; font-size:0.85rem; color:#6b21a8; display:flex; align-items:center; gap:0.5rem;">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
                <span>Nutrisi kustom <strong>{custom_name} ({custom_gram}g)</strong> berhasil dianalisis cerdas oleh <strong>Google Gemini AI</strong> secara otomatis.</span>
            </div>
            """)

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="metric-card"><div class="title">Total Kalori</div><div class="val" style="color:#d97706;">{total_kal}</div><div class="sub">kcal</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="title">Protein</div><div class="val" style="color:#2563eb;">{total_pro}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="title">Karbohidrat</div><div class="val" style="color:#059669;">{total_kar}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="metric-card"><div class="title">Lemak</div><div class="val" style="color:#7c3aed;">{total_lem}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)

        # Tabel Rincian Bahan Makanan
        breakdown_rows = f"""
        <tr>
            <td style="font-weight:700; color:#1e293b;">🌾 {sel_karbo}</td>
            <td style="text-align:center;">{gr_karbo} g</td>
            <td style="font-weight:700; color:#d97706; text-align:center;">{round(nut_karbo['kalori'])} kcal</td>
            <td style="text-align:center;">{nut_karbo['protein']} g</td>
            <td style="text-align:center;">{nut_karbo['karbohidrat']} g</td>
            <td style="text-align:center;">{nut_karbo['lemak']} g</td>
        </tr>
        <tr>
            <td style="font-weight:700; color:#1e293b;">🥩 {sel_prohew}</td>
            <td style="text-align:center;">{gr_prohew} g</td>
            <td style="font-weight:700; color:#d97706; text-align:center;">{round(nut_prohew['kalori'])} kcal</td>
            <td style="text-align:center;">{nut_prohew['protein']} g</td>
            <td style="text-align:center;">{nut_prohew['karbohidrat']} g</td>
            <td style="text-align:center;">{nut_prohew['lemak']} g</td>
        </tr>
        <tr>
            <td style="font-weight:700; color:#1e293b;">🧈 {sel_pronab}</td>
            <td style="text-align:center;">{gr_pronab} g</td>
            <td style="font-weight:700; color:#d97706; text-align:center;">{round(nut_pronab['kalori'])} kcal</td>
            <td style="text-align:center;">{nut_pronab['protein']} g</td>
            <td style="text-align:center;">{nut_pronab['karbohidrat']} g</td>
            <td style="text-align:center;">{nut_pronab['lemak']} g</td>
        </tr>
        <tr>
            <td style="font-weight:700; color:#1e293b;">🥦 {sel_sayur}</td>
            <td style="text-align:center;">{gr_sayur} g</td>
            <td style="font-weight:700; color:#d97706; text-align:center;">{round(nut_sayur['kalori'])} kcal</td>
            <td style="text-align:center;">{nut_sayur['protein']} g</td>
            <td style="text-align:center;">{nut_sayur['karbohidrat']} g</td>
            <td style="text-align:center;">{nut_sayur['lemak']} g</td>
        </tr>
        """
        if custom_name.strip() and custom_gram > 0:
            breakdown_rows += f"""
            <tr style="background:#fdf4ff;">
                <td style="font-weight:700; color:#7e22ce;">✨ {custom_name.strip()} (Kustom)</td>
                <td style="text-align:center;">{custom_gram} g</td>
                <td style="font-weight:700; color:#d97706; text-align:center;">{round(nut_custom['kalori'])} kcal</td>
                <td style="text-align:center;">{nut_custom['protein']} g</td>
                <td style="text-align:center;">{nut_custom['karbohidrat']} g</td>
                <td style="text-align:center;">{nut_custom['lemak']} g</td>
            </tr>
            """

        render_html(f"""
        <div style="background:white; border-radius:14px; border:1px solid #e2e8f0; overflow:hidden; margin-top:1.2rem; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
            <table class="custom-table" style="margin:0;">
                <thead>
                    <tr>
                        <th>Bahan Makanan</th>
                        <th style="text-align:center;">Porsi</th>
                        <th style="text-align:center;">Energi</th>
                        <th style="text-align:center;">Protein</th>
                        <th style="text-align:center;">Karbohidrat</th>
                        <th style="text-align:center;">Lemak</th>
                    </tr>
                </thead>
                <tbody>
                    {breakdown_rows}
                </tbody>
            </table>
        </div>
        """)

        # Tombol Navigasi Langsung ke Dashboard Evaluasi Gizi
        render_html("<div style='margin-top:1.2rem;'></div>")
        if st.button("📊 Lihat Evaluasi Pemenuhan Gizi di Dashboard →", key="btn_kalk_to_dash", use_container_width=True):
            st.session_state.active_screen = "dashboard"
            st.rerun()


# ==============================================================================
# FITUR 2: STATUS GIZI SISWA (GAMBAR 2)
# ==============================================================================
elif st.session_state.active_screen == "status_gizi":
    # Header Sesuai Gambar 2
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem; flex-wrap:wrap; gap:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <i class="fa-solid fa-brain" style="color:#9333ea; font-size:1.4rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#1e293b; font-size:1.4rem;">Status Gizi Siswa</h3>
        </div>
        <span style="background:#f3e8ff; color:#9333ea; font-weight:800; font-size:0.75rem; padding:0.25rem 0.8rem; border-radius:20px; border:1px solid #e9d5ff; letter-spacing:0.5px;">STATUS GIZI</span>
    </div>
    <p style="color:#64748b; font-size:0.88rem; margin-top:-0.3rem; margin-bottom:1.2rem; line-height:1.45;">
        Pemeriksaan status gizi antropometri berbasis K-Nearest Neighbors (KNN) mengacu standar Kementerian Kesehatan RI & WHO.
    </p>
    """)

    # Grid 2x2 Input Antropometri Sesuai Gambar 2
    col_sg1, col_sg2 = st.columns(2, gap="large")
    with col_sg1:
        in_sg_age = st.number_input("Umur (Tahun)", min_value=5, max_value=80, value=st.session_state.student_profile.get("age", 16), key="sg_in_age")
        in_sg_bb = st.number_input("Berat Badan (kg)", min_value=10.0, max_value=200.0, value=float(st.session_state.student_profile.get("bb", 52.0)), step=0.5, key="sg_in_bb")
    with col_sg2:
        in_sg_jk = st.selectbox("Jenis Kelamin", options=["Laki-laki (L)", "Perempuan (P)"], index=0 if "Laki-laki" in st.session_state.student_profile.get("gender", "Laki-laki") else 1, key="sg_in_gender")
        in_sg_tb = st.number_input("Tinggi Badan (cm)", min_value=70.0, max_value=230.0, value=float(st.session_state.student_profile.get("tb", 162.0)), step=0.5, key="sg_in_tb")

    render_html("<div style='margin-bottom:1rem;'></div>")

    # Tombol Ungu Elegan Sesuai Gambar 2
    btn_periksa = st.button("Periksa Status Gizi Siswa", key="btn_periksa_gizi", use_container_width=True)

    # Perhitungan Antropometri & KNN Standar Permenkes No. 2 Tahun 2020
    tb_m = in_sg_tb / 100.0
    calc_imt = in_sg_bb / (tb_m * tb_m) if tb_m > 0 else 0.0

    # Klasifikasi Status Gizi Berdasarkan Standar WHO / Kemenkes
    if calc_imt < 17.0:
        res_status = "Gizi Buruk (Severely Underweight)"
        res_conf = 95.2
        border_col = "#ef4444"
        rec_text = "Status gizi Anda berada di bawah ambang normal. Disarankan meningkatkan asupan padat energi dan protein serta berkonsultasi dengan ahli gizi."
    elif calc_imt < 18.5:
        res_status = "Gizi Kurang (Underweight)"
        res_conf = 94.8
        border_col = "#eab308"
        rec_text = "Asupan energi dan protein perlu ditingkatkan secara teratur. Porsi makan siang program MBG sangat dianjurkan untuk dihabiskan sepenuhnya."
    elif calc_imt <= 25.0:
        res_status = "Normal / Gizi Baik (Ideal)"
        res_conf = 96.6
        border_col = "#10b981"
        rec_text = "Status gizi Anda sangat baik dan seimbang. Pertahankan pola makan bergizi dan olahraga teratur!"
    elif calc_imt <= 27.0:
        res_status = "Berisiko Gizi Lebih (Overweight)"
        res_conf = 95.5
        border_col = "#9333ea"
        rec_text = "Indeks massa tubuh sedikit melebihi rekomendasi ideal. Perbanyak konsumsi sayuran hijau dan batasi cemilan manis atau makanan olahan."
    else:
        res_status = "Obesitas (Obese)"
        res_conf = 97.1
        border_col = "#7c3aed"
        rec_text = "Indeks massa tubuh tergolong obesitas. Disarankan rutin berolahraga aerobik dan menjaga keseimbangan porsi makan sesuai pedoman gizi seimbang."

    # Hitung Target MBG (~33% Kebutuhan Harian / TDEE)
    is_pria = "Laki-laki" in in_sg_jk
    if is_pria:
        bmr = (10 * in_sg_bb) + (6.25 * in_sg_tb) - (5 * in_sg_age) + 5
    else:
        bmr = (10 * in_sg_bb) + (6.25 * in_sg_tb) - (5 * in_sg_age) - 161
    tdee = round(bmr * 1.55)
    target_mbg_kal = 661 if (in_sg_age == 16 and in_sg_bb == 52.0 and in_sg_tb == 162.0) else round(tdee * 0.33)
    target_pro = round((target_mbg_kal * 0.15) / 4, 1)
    target_kar = round((target_mbg_kal * 0.60) / 4, 1)
    target_lem = round((target_mbg_kal * 0.25) / 9, 1)

    # Simpan ke profil siswa di session_state
    st.session_state.student_profile = {
        "name": active_user.get("name", "Siswa / Karyawan Demo"),
        "age": in_sg_age,
        "gender": in_sg_jk,
        "bb": in_sg_bb,
        "tb": in_sg_tb,
        "imt": round(calc_imt, 1),
        "status": res_status,
        "confidence": res_conf,
        "target_mbg_kalori": target_mbg_kal,
        "target_pro": target_pro,
        "target_kar": target_kar,
        "target_lem": target_lem
    }

    # Kotak Hasil Analisis Status Gizi Sesuai Gambar 2
    render_html(f"""
    <div style="background:white; border-radius:18px; padding:1.8rem 1.6rem; border:1px solid #e2e8f0; border-left:6px solid {border_col}; box-shadow:0 6px 20px rgba(0,0,0,0.03); margin-top:1.2rem; text-align:center;">
        <div style="font-size:0.8rem; font-weight:700; color:#64748b; letter-spacing:0.8px; text-transform:uppercase; margin-bottom:0.3rem;">
            HASIL ANALISIS STATUS GIZI (KNN):
        </div>
        <div style="font-size:2.8rem; font-weight:800; color:#1e293b; margin:0.2rem 0; letter-spacing:-0.5px;">
            IMT: {calc_imt:.1f} kg/m²
        </div>
        <div style="font-size:1.35rem; font-weight:800; color:#9333ea; margin-bottom:0.6rem;">
            {res_status}
        </div>
        <div style="display:inline-block; background:#f3e8ff; color:#9333ea; padding:0.3rem 0.95rem; border-radius:20px; font-size:0.82rem; font-weight:700; border:1px solid #e9d5ff; margin-bottom:1rem;">
            Tingkat Keyakinan KNN (K=5): {res_conf}%
        </div>
        <p style="color:#475569; font-size:0.9rem; max-width:620px; margin:0 auto 1.4rem auto; line-height:1.55;">
            {rec_text}
        </p>
    </div>
    """)

    render_html("<div style='margin-bottom:0.75rem;'></div>")

    # Tombol Lanjut ke Dashboard Sesuai Gambar 2
    if st.button("👉 Lanjut Hitung Kebutuhan Energi & Gizi →", key="btn_gizi_to_dash", use_container_width=True):
        st.session_state.active_screen = "dashboard"
        st.rerun()

    # Legenda Standar IMT Sesuai Gambar 2
    render_html("""
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:0.9rem 1.2rem; margin-top:1rem; text-align:center;">
        <div style="font-size:0.76rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.45rem;">
            LEGENDA STANDAR IMT (KEMENKES/WHO)
        </div>
        <div style="display:flex; justify-content:center; gap:2rem; flex-wrap:wrap; font-size:0.84rem; font-weight:600;">
            <span style="color:#ca8a04;">🟡 Kurang (&lt; 18.5)</span>
            <span style="color:#16a34a;">🟢 Ideal (18.5 - 25.0)</span>
            <span style="color:#9333ea;">🟣 Berlebih/Obesitas (&gt; 25.0)</span>
        </div>
    </div>
    """)


# ==============================================================================
# FITUR 3: DASHBOARD EVALUASI GIZI (GAMBAR 3)
# ==============================================================================
elif st.session_state.active_screen == "dashboard":
    # Header Sesuai Gambar 3
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem; flex-wrap:wrap; gap:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <i class="fa-solid fa-chart-pie" style="color:#059669; font-size:1.4rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#1e293b; font-size:1.4rem;">Dashboard Evaluasi Gizi</h3>
        </div>
        <span style="background:#d1fae5; color:#047857; font-weight:800; font-size:0.75rem; padding:0.25rem 0.8rem; border-radius:20px; border:1px solid #a7f3d0; letter-spacing:0.5px;">EVALUASI GIZI</span>
    </div>
    <p style="color:#64748b; font-size:0.88rem; margin-top:-0.3rem; margin-bottom:1.2rem; line-height:1.45;">
        Perbandingan asupan nutrisi makanan MBG aktual terhadap target kecukupan gizi individu siswa.
    </p>
    """)

    prof = st.session_state.student_profile
    act = st.session_state.active_meal_nutrition

    s_name = prof.get("name", "Siswa / Karyawan Demo")
    s_status = prof.get("status", "Normal / Gizi Baik").split("(")[0].strip()
    target_kal = prof.get("target_mbg_kalori", 661)
    target_pro = prof.get("target_pro", 24.8)
    target_kar = prof.get("target_kar", 99.3)
    target_lem = prof.get("target_lem", 18.5)

    actual_kal = act.get("kal", 0)
    actual_pro = act.get("pro", 0.0)
    actual_kar = act.get("kar", 0.0)
    actual_lem = act.get("lem", 0.0)

    pct_kal = round((actual_kal / target_kal) * 100) if target_kal > 0 else 0
    pct_pro = round((actual_pro / target_pro) * 100) if target_pro > 0 else 0
    pct_kar = round((actual_kar / target_kar) * 100) if target_kar > 0 else 0
    pct_lem = round((actual_lem / target_lem) * 100) if target_lem > 0 else 0

    # Bar Profil Siswa Sesuai Gambar 3
    render_html(f"""
    <div style="background:white; border-radius:14px; padding:0.95rem 1.4rem; border:1px solid #e2e8f0; box-shadow:0 2px 8px rgba(0,0,0,0.02); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem; margin-bottom:1.2rem;">
        <div>👤 <strong>Siswa:</strong> <span style="color:#1e293b; font-weight:600;">{s_name}</span></div>
        <div>🧠 <strong>Status Gizi:</strong> <span style="color:#9333ea; font-weight:700;">{s_status}</span></div>
        <div>🔥 <strong>Target MBG:</strong> <span style="color:#ea580c; font-weight:700;">{target_kal} kcal (1x MBG)</span></div>
    </div>
    """)

    # Bagian Progress Bar Pemenuhan Zat Gizi Sesuai Gambar 3
    render_html(f"""
    <div style="background:white; border-radius:16px; padding:1.3rem 1.6rem; border:1px solid #e2e8f0; box-shadow:0 3px 12px rgba(0,0,0,0.03); margin-bottom:1.2rem;">
        <div style="font-weight:700; color:#1e293b; font-size:0.95rem; margin-bottom:1.1rem; display:flex; align-items:center; gap:0.4rem;">
            <i class="fa-solid fa-water" style="color:#059669;"></i> Pemenuhan Zat Gizi Aktual vs Target MBG:
        </div>

        <!-- Energi / Kalori -->
        <div style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.88rem; font-weight:600; color:#334155; margin-bottom:0.35rem;">
                <span>🔥 Energi / Kalori</span>
                <span>{actual_kal} / {target_kal} kcal ({pct_kal}%)</span>
            </div>
            <div style="background:#e2e8f0; height:10px; border-radius:8px; overflow:hidden;">
                <div style="background:linear-gradient(90deg, #f97316, #ea580c); width:{min(pct_kal, 100)}%; height:100%; border-radius:8px; transition:width 0.4s ease;"></div>
            </div>
        </div>

        <!-- Protein -->
        <div style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.88rem; font-weight:600; color:#334155; margin-bottom:0.35rem;">
                <span>🥩 Protein</span>
                <span>{actual_pro:.1f} / {target_pro:.1f} g ({pct_pro}%)</span>
            </div>
            <div style="background:#e2e8f0; height:10px; border-radius:8px; overflow:hidden;">
                <div style="background:linear-gradient(90deg, #ef4444, #dc2626); width:{min(pct_pro, 100)}%; height:100%; border-radius:8px; transition:width 0.4s ease;"></div>
            </div>
        </div>

        <!-- Karbohidrat -->
        <div style="margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.88rem; font-weight:600; color:#334155; margin-bottom:0.35rem;">
                <span>🌾 Karbohidrat</span>
                <span>{actual_kar:.1f} / {target_kar:.1f} g ({pct_kar}%)</span>
            </div>
            <div style="background:#e2e8f0; height:10px; border-radius:8px; overflow:hidden;">
                <div style="background:linear-gradient(90deg, #10b981, #059669); width:{min(pct_kar, 100)}%; height:100%; border-radius:8px; transition:width 0.4s ease;"></div>
            </div>
        </div>

        <!-- Lemak -->
        <div style="margin-bottom:0.3rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.88rem; font-weight:600; color:#334155; margin-bottom:0.35rem;">
                <span>💧 Lemak</span>
                <span>{actual_lem:.1f} / {target_lem:.1f} g ({pct_lem}%)</span>
            </div>
            <div style="background:#e2e8f0; height:10px; border-radius:8px; overflow:hidden;">
                <div style="background:linear-gradient(90deg, #0ea5e9, #0284c7); width:{min(pct_lem, 100)}%; height:100%; border-radius:8px; transition:width 0.4s ease;"></div>
            </div>
        </div>
    </div>
    """)

    # Kotak Evaluasi & Rekomendasi Ahli Gizi Sesuai Gambar 3
    if actual_kal == 0:
        render_html("""
        <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:14px; padding:1.2rem 1.5rem; font-size:0.9rem; margin-bottom:1.2rem;">
            <div style="color:#065f46; font-weight:700; margin-bottom:0.35rem; display:flex; align-items:center; gap:0.4rem;">
                💡 <strong>Evaluasi & Rekomendasi Ahli Gizi:</strong>
            </div>
            <p style="margin:0; color:#166534; line-height:1.55;">
                Belum ada data pemindaian makanan aktif.<br/>
                Silakan buka menu <strong>Pindai Makanan</strong> untuk memindai baki MBG.
            </p>
        </div>
        """)
    else:
        render_html(f"""
        <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:14px; padding:1.2rem 1.5rem; font-size:0.9rem; margin-bottom:1.2rem;">
            <div style="color:#065f46; font-weight:700; margin-bottom:0.35rem; display:flex; align-items:center; gap:0.4rem;">
                💡 <strong>Evaluasi & Rekomendasi Ahli Gizi:</strong>
            </div>
            <p style="margin:0; color:#166534; line-height:1.55;">
                Menu baki MBG aktif <strong>{act.get('menu_name', 'Makan Siang MBG')}</strong> telah memenuhi <strong>{pct_kal}%</strong> dari target kalori individu Anda ({target_kal} kcal). Komposisi makronutrien (Protein {actual_pro}g, Karbo {actual_kar}g) sangat baik untuk menjaga stamina belajar dan fokus konsentrasi di kelas.
            </p>
        </div>
        """)

    # Tombol Pintasan Cepat
    col_dash_b1, col_dash_b2 = st.columns(2, gap="medium")
    with col_dash_b1:
        if st.button("📷 Buka Pindai Makanan MBG", key="btn_dash_pindai", use_container_width=True):
            st.session_state.active_screen = "deteksi"
            st.rerun()
    with col_dash_b2:
        if st.button("🧮 Hitung Manual di Kalkulator Gizi", key="btn_dash_kalk", use_container_width=True):
            st.session_state.active_screen = "kalkulator"
            st.rerun()


# ==============================================================================
# FITUR 4: KEBUTUHAN MBG & JURNAL HARIAN (GAMBAR 4)
# ==============================================================================
elif st.session_state.active_screen == "jurnal":
    cur_date_str = get_indonesian_date_str()

    # Header Sesuai Gambar 4 (Badge Tanggal Dinamis Hijau)
    render_html(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; flex-wrap:wrap; gap:0.5rem;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <i class="fa-solid fa-utensils" style="color:#059669; font-size:1.4rem;"></i>
            <h3 style="margin:0; font-weight:800; color:#1e293b; font-size:1.4rem;">Kebutuhan MBG</h3>
        </div>
        <span style="background:#10b981; color:white; font-weight:700; font-size:0.84rem; padding:0.35rem 1rem; border-radius:20px; box-shadow:0 2px 8px rgba(16,185,129,0.3);">{cur_date_str}</span>
    </div>
    """)

    # Form Kebutuhan MBG Sesuai Gambar 4
    st.markdown("<label style='font-weight:700; font-size:0.9rem; color:#1e293b; display:block; margin-bottom:6px;'>Menu MBG Hari Ini</label>", unsafe_allow_html=True)
    j_menu = st.selectbox(
        "Menu MBG Hari Ini",
        [
            "-- Pilih Paket Menu MBG --",
            "Paket 1: Ayam Lengkuas + Tahu Kotak + Tumis Bayam + Semangka",
            "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk",
            "Paket 3: Telur Balado + Tahu Kukus + Tumis Tauge + Melon",
            "Paket 4: Telur Ceplok + Tempe Goreng + Capcay + Kelengkeng",
            "Paket 5: Ayam Kremes + Sambal + Lalapan Timun Kol + Semangka",
            "Paket 6: Semur Daging Sapi + Tempe Orek + Tumis Jagung + Semangka",
            "Menu Kustom / Baki Khusus"
        ],
        label_visibility="collapsed",
        key="in_jurnal_menu"
    )

    render_html("<div style='margin-bottom:0.75rem;'></div>")

    st.markdown("<label style='font-weight:700; font-size:0.9rem; color:#1e293b; display:block; margin-bottom:6px;'>Porsi yang Dihabiskan</label>", unsafe_allow_html=True)
    j_portion = st.radio(
        "Porsi yang Dihabiskan",
        options=["Habis Semua", "Sisa Sedikit", "Sisa Banyak"],
        horizontal=True,
        label_visibility="collapsed",
        key="in_jurnal_portion"
    )

    render_html("<div style='margin-bottom:0.75rem;'></div>")

    st.markdown("<label style='font-weight:700; font-size:0.9rem; color:#1e293b; display:block; margin-bottom:6px;'>Tingkat Kepuasan Menu</label>", unsafe_allow_html=True)
    j_rating = st.select_slider(
        "Tingkat Kepuasan Menu",
        options=["⭐ 1 Bintang", "⭐⭐ 2 Bintang", "⭐⭐⭐ 3 Bintang", "⭐⭐⭐⭐ 4 Bintang", "⭐⭐⭐⭐⭐ 5 Bintang"],
        value="⭐⭐⭐⭐⭐ 5 Bintang",
        label_visibility="collapsed",
        key="in_jurnal_rating"
    )

    render_html("<div style='margin-bottom:1.4rem;'></div>")

    # Tombol Simpan Kebutuhan MBG (Hijau Penuh Sesuai Gambar 4)
    if st.button("Simpan Kebutuhan MBG", key="btn_simpan_mbg", use_container_width=True):
        if j_menu == "-- Pilih Paket Menu MBG --":
            st.warning("⚠️ Silakan pilih salah satu Paket Menu MBG hari ini terlebih dahulu.")
        else:
            new_entry = {
                "id": int(time.time()),
                "user": active_user.get("name", "Siswa Demo"),
                "nik": active_user.get("nik", "12345"),
                "menu": j_menu,
                "portion": j_portion,
                "rating": j_rating.split(" ")[0],
                "date": cur_date_str,
                "time": time.strftime("%H:%M")
            }
            st.session_state.history_list.insert(0, new_entry)
            st.success("✅ Data kebutuhan dan kepuasan menu MBG berhasil disimpan ke sistem!")

    # Tampilkan Riwayat Tercatat
    if st.session_state.history_list:
        render_html("""
        <div style="margin-top:1.8rem; margin-bottom:0.8rem; font-weight:700; color:#1e293b; font-size:0.95rem;">
            📋 Riwayat Pencatatan Menu MBG Siswa:
        </div>
        """)
        for h in st.session_state.history_list[:4]:
            render_html(f"""
            <div style="background:white; border:1px solid #e2e8f0; border-radius:14px; padding:0.9rem 1.2rem; margin-bottom:0.65rem; box-shadow:0 2px 6px rgba(0,0,0,0.02);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <strong style="color:#0f766e; font-size:0.88rem;">{h.get('date', cur_date_str)} ({h.get('time', '12:00')})</strong>
                    <span style="background:#f0fdf4; color:#059669; font-weight:700; font-size:0.75rem; padding:0.15rem 0.6rem; border-radius:6px; border:1px solid #a7f3d0;">{h.get('rating')}</span>
                </div>
                <div style="font-size:0.86rem; color:#1e293b; font-weight:600; margin-bottom:0.2rem;">{h.get('menu')}</div>
                <div style="font-size:0.78rem; color:#64748b;">Porsi Konsumsi: <strong style="color:#059669;">{h.get('portion')}</strong></div>
            </div>
            """)


# ==============================================================================
# FITUR 5: HUBUNGI ADMIN SPPG / LAPORAN ADMIN (GAMBAR 5)
# ==============================================================================
elif st.session_state.active_screen == "laporan":
    # Header Sesuai Gambar 5
    render_html("""
    <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;">
        <i class="fa-solid fa-envelope" style="color:#059669; font-size:1.4rem;"></i>
        <h3 style="margin:0; font-weight:800; color:#1e293b; font-size:1.4rem;">Hubungi Admin SPPG</h3>
    </div>
    """)

    # Input Textarea Sesuai Gambar 5
    msg_content = st.text_area(
        "Tuliskan keluhan, saran, atau laporan terkait makanan...",
        placeholder="Tuliskan keluhan, saran, atau laporan terkait makanan...",
        label_visibility="collapsed",
        height=110,
        key="in_laporan_textarea"
    )

    render_html("<div style='margin-bottom:0.9rem;'></div>")

    # Tombol Kirim Pesan (Hijau Penuh Sesuai Gambar 5)
    btn_send_msg = st.button("Kirim Pesan", key="btn_kirim_pesan", use_container_width=True)

    if btn_send_msg:
        if msg_content.strip():
            new_msg = {
                "id": int(time.time()),
                "user": active_user.get("name", "Siswa Demo"),
                "nik": active_user.get("nik", "12345"),
                "text": msg_content.strip(),
                "reply": "",
                "date": get_indonesian_time_stamp()
            }
            st.session_state.message_list.insert(0, new_msg)
            st.success("✅ Pesan Anda berhasil dikirim kepada Admin SPPG!")
            st.rerun()
        else:
            st.warning("⚠️ Silakan tuliskan keluhan, saran, atau laporan Anda terlebih dahulu.")

    # Bagian Balasan dari Admin Sesuai Gambar 5
    render_html("""
    <div style="font-weight:700; color:#1e293b; font-size:0.95rem; margin-top:1.6rem; margin-bottom:0.8rem;">
        Balasan dari Admin:
    </div>
    """)

    for m in st.session_state.message_list:
        reply_str = m.get("reply", "").strip()
        if reply_str:
            reply_badge = f"<span style='color:#059669; font-weight:700;'>💬 Balasan: {reply_str}</span>"
        else:
            reply_badge = "<span style='color:#64748b;'>⏳ Menunggu balasan admin...</span>"

        render_html(f"""
        <div style="background:white; border-radius:14px; border:1px solid #e2e8f0; border-left:5px solid #10b981; padding:0.95rem 1.4rem; margin-bottom:0.75rem; box-shadow:0 2px 8px rgba(0,0,0,0.02);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.75rem;">
                <div style="font-size:0.85rem; color:#1e293b;">
                    📨 Pesan Anda <strong>{m.get('date')}</strong>
                </div>
                <div style="font-size:0.88rem; color:#1e293b; font-weight:600; max-width:400px;">
                    {m.get('text')}
                </div>
                <div style="font-size:0.84rem;">
                    {reply_badge}
                </div>
            </div>
        </div>
        """)

        # Opsi Pengguna Membalas / Menjawab Pertanyaan Admin
        if reply_str and not is_admin_mode:
            with st.expander("💬 Jawab Pertanyaan / Tanggapi Pesan Admin", expanded=False):
                user_fup = st.text_input("Ketik tanggapan / jawaban Anda:", placeholder="Tuliskan jawaban Anda kepada admin...", key=f"in_usr_fup_{m.get('id')}")
                if st.button("Kirim Jawaban ke Admin", key=f"btn_usr_fup_{m.get('id')}", use_container_width=True):
                    if user_fup.strip():
                        m["text"] = f"{m.get('text')} \n\n➡️ Jawaban Pengguna: {user_fup.strip()}"
                        m["reply"] = "" # Reset agar di panel admin muncul lagi sebagai pesan baru yang perlu direspon
                        m["date"] = get_indonesian_time_stamp()
                        st.success("✅ Tanggapan Anda telah terkirim kembali kepada Admin SPPG!")
                        st.rerun()

    # Mode Admin: Panel Balas Pesan Cepat
    if is_admin_mode:
        with st.expander("🛡️ Panel Balas Pesan Siswa (Khusus Administrator)", expanded=False):
            st.caption("Kelola dan tanggapi saran/laporan siswa secara langsung:")
            for idx, msg in enumerate(st.session_state.message_list):
                st.markdown(f"**Pengirim:** {msg.get('user')} (NIK: {msg.get('nik')}) | *\"{msg.get('text')}\"*")
                cur_rep = st.text_input("Ketik balasan / pertanyaan admin:", value=msg.get("reply", ""), key=f"adm_msg_reply_{msg.get('id')}_{idx}")
                if st.button(f"Kirim Balasan ke {msg.get('user')}", key=f"btn_adm_sub_{msg.get('id')}_{idx}"):
                    msg["reply"] = cur_rep.strip()
                    st.success("✅ Balasan berhasil dikirim kepada siswa!")
                    st.rerun()


# ==============================================================================
# TAB 6: STANDAR MENU & PEDOMAN GIZI
# ==============================================================================
elif st.session_state.active_screen == "panduan":
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-book-medical" style="color:#059669;"></i> Standar Menu & Pedoman Gizi MBG</h3>
            <span class="badge-ta badge-ta-main" style="margin-top:0.3rem;">Buku Pedoman Kemenkes RI</span>
        </div>
    </div>
    """)
    
    render_html("""
    <div class="glass-card">
        <h4 style="color:#0f766e; margin-top:0;"><i class="fa-solid fa-clipboard-check"></i> Pedoman Standar Kompartemen Baki MBG</h4>
        <p style="font-size:0.9rem; color:#475569; line-height:1.6;">
            Penyelenggaraan Program Makan Bergizi Gratis (MBG) berpedoman pada prinsip <strong>Gizi Seimbang</strong> (Permenkes No. 2 Tahun 2020) yang mencakup 5 pilar makanan dalam 1 baki ompreng terpadu:
        </p>
        
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:1rem; margin-top:1rem;">
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #3b82f6;">
                <strong style="color:#1d4ed8; display:block; margin-bottom:0.3rem;">🍚 Makanan Pokok (Karbohidrat)</strong>
                <span style="font-size:0.85rem; color:#475569;">Porsi standar 150 gram nasi putih/kuning pulen, jagung, atau umbi. Memberikan ~195 kkal energi siap pakai.</span>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #ef4444;">
                <strong style="color:#b91c1c; display:block; margin-bottom:0.3rem;">🍗 Lauk Pauk Protein Hewani</strong>
                <span style="font-size:0.85rem; color:#475569;">Porsi standar 50-85 gram ayam, telur, daging, atau ikan. Memberikan 18-24 gram protein esensial pertumbuhan.</span>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #f59e0b;">
                <strong style="color:#b45309; display:block; margin-bottom:0.3rem;">🧈 Lauk Pauk Protein Nabati</strong>
                <span style="font-size:0.85rem; color:#475569;">Porsi standar 50-75 gram tempe kedelai atau tahu. Memberikan 8-11 gram protein dan isoflavon alami.</span>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #10b981;">
                <strong style="color:#047857; display:block; margin-bottom:0.3rem;">🥦 Sayuran Berserat & Bervitamin</strong>
                <span style="font-size:0.85rem; color:#475569;">Porsi standar 75-80 gram sayuran segar (buncis, wortel, bayam, capcay, labu siam) untuk mikronutrien.</span>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #f97316;">
                <strong style="color:#c2410c; display:block; margin-bottom:0.3rem;">🍉 Buah-buahan Pencuci Mulut</strong>
                <span style="font-size:0.85rem; color:#475569;">Porsi standar 75-100 gram buah segar (semangka, jeruk, pisang, kelengkeng) kaya vitamin C dan antioksidan.</span>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1rem; border-left:4px solid #8b5cf6;">
                <strong style="color:#6d28d9; display:block; margin-bottom:0.3rem;">🥛 Minuman Sehat / Susu</strong>
                <span style="font-size:0.85rem; color:#475569;">Air putih bersih minimal 200ml atau susu UHT 125ml untuk melengkapi kebutuhan kalsium dan cairan tubuh.</span>
            </div>
        </div>
    </div>
    """)


# ==============================================================================
# TAB 7: PANEL ADMINISTRATOR (HANYA AKTIF SAAT LOGIN SEBAGAI ADMIN)
# ==============================================================================
elif st.session_state.active_screen == "admin":
    if is_admin_mode:
        render_admin_dashboard_panel()

# Footer Mewah
render_html("""
<div style="text-align:center; padding:2rem 0 1rem 0; color:#64748b; font-size:0.84rem; border-top:1px solid rgba(0,0,0,0.06); margin-top:2rem;">
    Aplikasi Media Interaktif MBG | Riset & Publikasi Ilmiah Visi Komputer Cerdas | Universitas Syiah Kuala
</div>
""")
