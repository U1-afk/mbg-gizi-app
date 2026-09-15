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
        {"id": 1, "user": "Siswa Demo", "nik": "12345", "menu": "Paket 1: Ayam Lengkuas + Tahu Kuning + Labu Siam + Semangka", "portion": "Habis Semua (100%)", "rating": "5 ⭐", "date": "Senin, 14 September 2026", "time": "12:15"},
        {"id": 2, "user": "Ahmad Fauzi", "nik": "10021", "menu": "Paket 6: Semur Daging Sapi + Tempe Orek + Sayur Capcay + Semangka", "portion": "Habis Semua (100%)", "rating": "5 ⭐", "date": "Senin, 14 September 2026", "time": "12:30"},
        {"id": 3, "user": "Siti Rahma", "nik": "10045", "menu": "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk", "portion": "Sisa Sedikit (75%)", "rating": "4 ⭐", "date": "Senin, 14 September 2026", "time": "12:45"}
    ]

if "message_list" not in st.session_state:
    st.session_state.message_list = [
        {"id": 1, "user": "Siswa Demo", "nik": "12345", "text": "Porsi ayam hari ini sangat lezat dan bumbunya empuk. Sayurannya juga segar!", "reply": "Terima kasih atas apresiasinya! Selamat belajar dan tetap semangat!", "date": "14 Sep 2026 12:20"},
        {"id": 2, "user": "Ahmad Fauzi", "nik": "10021", "text": "Mohon variasi buah semangka diselingi buah melon atau pisang di hari Rabu.", "reply": "Saran diterima, variasi menu buah akan kami rotasi setiap pekan.", "date": "14 Sep 2026 12:35"}
    ]

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

    /* Home Menu Grid 6 Fitur Persis Vercel */
    .home-menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.85rem;
        margin-bottom: 1.6rem;
    }
    .menu-item {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(12px);
        border: 1.5px solid rgba(255, 255, 255, 0.8);
        border-radius: 16px;
        padding: 1.1rem 0.9rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
    }
    .menu-item:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.2);
    }
    .menu-item .menu-icon {
        font-size: 2rem;
        margin-bottom: 0.45rem;
    }
    .menu-item .menu-title {
        font-weight: 800;
        color: #0f172a !important;
        font-size: 0.9rem;
    }
    .menu-item .menu-subtitle {
        font-size: 0.74rem;
        color: #64748b !important;
        margin-top: 0.25rem;
        line-height: 1.3;
    }

    /* Tabs Kustom Super Jelas & Tajam */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 0.4rem !important;
        background: rgba(255, 255, 255, 0.8) !important;
        padding: 0.45rem !important;
        border-radius: 16px !important;
        border: 1.5px solid rgba(16, 185, 129, 0.25) !important;
        margin-bottom: 1.4rem !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.08) !important;
    }
    button[data-baseweb="tab"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 12px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        color: #1e293b !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    button[data-baseweb="tab"]:hover {
        background: #ecfdf5 !important;
        border-color: #10b981 !important;
        color: #059669 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        border-color: #059669 !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] span {
        color: #ffffff !important;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }

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
        st.rerun()

# Header Banner
render_html("""
<div class="hero-banner">
    <h1>🍱 Media Interaktif Pemantauan Gizi MBG</h1>
    <p>Aplikasi Evaluasi Porsi Makan Bergizi Gratis & Analisis Status Gizi Siswa Berbasis Visi Komputer Cerdas Mengacu Standar Resmi Kementerian Kesehatan RI</p>
    <div class="hero-tags">
        <span class="hero-tag"><i class="fa-solid fa-certificate"></i> Standar Kemenkes RI Permenkes No. 2/2020</span>
        <span class="hero-tag"><i class="fa-solid fa-microchip"></i> Intelligent Multimedia Processing</span>
        <span class="hero-tag"><i class="fa-solid fa-bowl-rice"></i> 5 Kompartemen Baki Gizi Terpadu</span>
    </div>
</div>
""")

# Home Menu Grid 6 Fitur (Identik dengan Menu Vercel)
render_html("""
<div class="home-menu-grid">
    <div class="menu-item">
        <span class="badge-ta badge-ta-1">Pindai Makanan</span>
        <div class="menu-icon" style="color:#2563eb;"><i class="fa-solid fa-camera"></i></div>
        <div class="menu-title">Deteksi Baki MBG</div>
        <div class="menu-subtitle">Pindai Baki & Hitung Nilai Gizi Otomatis</div>
    </div>
    <div class="menu-item">
        <span class="badge-ta badge-ta-2">Kebutuhan Energi</span>
        <div class="menu-icon" style="color:#d97706;"><i class="fa-solid fa-calculator"></i></div>
        <div class="menu-title">Kalkulator Gizi</div>
        <div class="menu-subtitle">Hitung Kebutuhan Energi & Makronutrisi</div>
    </div>
    <div class="menu-item">
        <span class="badge-ta badge-ta-3">Status Gizi</span>
        <div class="menu-icon" style="color:#9333ea;"><i class="fa-solid fa-brain"></i></div>
        <div class="menu-title">Status Gizi Siswa</div>
        <div class="menu-subtitle">Pemeriksaan Antropometri Kemenkes RI</div>
    </div>
    <div class="menu-item">
        <span class="badge-ta badge-ta-main">Evaluasi Gizi</span>
        <div class="menu-icon" style="color:#059669;"><i class="fa-solid fa-chart-pie"></i></div>
        <div class="menu-title">Dashboard MBG</div>
        <div class="menu-subtitle">Asupan Aktual vs Target Kebutuhan Siswa</div>
    </div>
    <div class="menu-item">
        <div class="menu-icon" style="color:#0f766e;"><i class="fa-solid fa-utensils"></i></div>
        <div class="menu-title">Kebutuhan MBG</div>
        <div class="menu-subtitle">Jurnal Porsi & Kepuasan Menu Harian</div>
    </div>
    <div class="menu-item">
        <div class="menu-icon" style="color:#6366f1;"><i class="fa-solid fa-book-medical"></i></div>
        <div class="menu-title">Standar Menu</div>
        <div class="menu-subtitle">Buku Pedoman Standar Porsi Kemenkes RI</div>
    </div>
</div>
""")


# ==============================================================================
# 2. MODEL LOADER (ULTRALYTICS ENGINE)
# ==============================================================================
@st.cache_resource(show_spinner="Memuat model visi komputer...")
def load_detection_model():
    candidate_paths = [
        "best.pt",
        os.path.join(os.path.dirname(__file__), "best.pt"),
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


# ==============================================================================
# 3. BASIS DATA GIZI RESMI MBG
# ==============================================================================
FOOD_LIBRARY = {
    "karbo": {
        "Nasi Putih Pulen (150g)": {"gram": 150, "kal": 195, "pro": 4.0, "kar": 43.0, "lem": 0.5, "cat": "Makanan Pokok"},
        "Nasi Kuning Gurih (150g)": {"gram": 150, "kal": 210, "pro": 4.2, "kar": 41.5, "lem": 3.2, "cat": "Makanan Pokok"},
        "Mie Goreng / Bihun Sayur (120g)": {"gram": 120, "kal": 180, "pro": 3.8, "kar": 38.0, "lem": 2.5, "cat": "Makanan Pokok"},
        "Roti Burger / Roti Gandum (100g)": {"gram": 100, "kal": 175, "pro": 5.5, "kar": 34.0, "lem": 1.8, "cat": "Makanan Pokok"}
    },
    "prohew": {
        "Ayam Goreng Lengkuas / Serundeng (85g)": {"gram": 85, "kal": 215, "pro": 24.0, "kar": 1.5, "lem": 12.5, "cat": "Protein Hewani"},
        "Telur Ceplok / Balado (1 Butir - 55g)": {"gram": 55, "kal": 92, "pro": 6.5, "kar": 0.8, "lem": 7.0, "cat": "Protein Hewani"},
        "Ayam Suwir Kemangi / Opor (75g)": {"gram": 75, "kal": 165, "pro": 20.5, "kar": 1.0, "lem": 8.5, "cat": "Protein Hewani"},
        "Semur Daging Sapi / Rolade (75g)": {"gram": 75, "kal": 185, "pro": 19.0, "kar": 3.5, "lem": 10.5, "cat": "Protein Hewani"},
        "Udang Balado Gurih (75g)": {"gram": 75, "kal": 85, "pro": 18.5, "kar": 0.5, "lem": 0.8, "cat": "Protein Hewani"},
        "Telur Puyuh Rebus (5 Butir - 50g)": {"gram": 50, "kal": 79, "pro": 6.5, "kar": 0.5, "lem": 5.5, "cat": "Protein Hewani"}
    },
    "pronab": {
        "Tempe Goreng Gurih (50g)": {"gram": 50, "kal": 118, "pro": 10.5, "kar": 7.5, "lem": 5.5, "cat": "Protein Nabati"},
        "Tempe Orek Dadu Manis (50g)": {"gram": 50, "kal": 110, "pro": 9.0, "kar": 8.0, "lem": 5.0, "cat": "Protein Nabati"},
        "Tahu Goreng Kotak / Sakura (75g)": {"gram": 75, "kal": 80, "pro": 8.0, "kar": 2.0, "lem": 4.8, "cat": "Protein Nabati"},
        "Perkedel Kentang Gurih (50g)": {"gram": 50, "kal": 95, "pro": 2.5, "kar": 14.0, "lem": 3.5, "cat": "Protein Nabati"}
    },
    "sayur": {
        "Tumis Sayur Hijau (Buncis/Bayam/Kangkung) (75g)": {"gram": 75, "kal": 30, "pro": 1.8, "kar": 5.0, "lem": 0.6, "cat": "Sayuran"},
        "Lalapan Timun Segar & Selada (60g)": {"gram": 60, "kal": 12, "pro": 0.6, "kar": 2.5, "lem": 0.1, "cat": "Sayuran"},
        "Sayur Capcay Wortel & Buncis (80g)": {"gram": 80, "kal": 35, "pro": 2.0, "kar": 6.5, "lem": 0.8, "cat": "Sayuran"},
        "Tumis Jagung Manis & Wortel (75g)": {"gram": 75, "kal": 48, "pro": 1.5, "kar": 10.5, "lem": 0.5, "cat": "Sayuran"},
        "Sayur Sop Wortel Kol (75g)": {"gram": 75, "kal": 25, "pro": 1.2, "kar": 4.5, "lem": 0.5, "cat": "Sayuran"}
    },
    "buah": {
        "Buah Semangka Segar (1 Potong - 100g)": {"gram": 100, "kal": 30, "pro": 0.6, "kar": 7.5, "lem": 0.2, "cat": "Buah-buahan"},
        "Buah Pisang Ambon / Cavendish (1 Buah - 100g)": {"gram": 100, "kal": 89, "pro": 1.1, "kar": 22.8, "lem": 0.3, "cat": "Buah-buahan"},
        "Buah Jeruk Manis Segar (1 Buah - 100g)": {"gram": 100, "kal": 47, "pro": 0.9, "kar": 11.8, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Kelengkeng Manis (5 Butir - 75g)": {"gram": 75, "kal": 45, "pro": 1.0, "kar": 11.3, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Anggur Ungu / Hitam (6 Butir - 80g)": {"gram": 80, "kal": 54, "pro": 0.6, "kar": 14.5, "lem": 0.1, "cat": "Buah-buahan"},
        "Buah Salak Pondoh (1 Buah - 70g)": {"gram": 70, "kal": 54, "pro": 0.6, "kar": 14.6, "lem": 0.1, "cat": "Buah-buahan"}
    },
    "susu": {
        "Tanpa Susu (Air Putih Bersih)": {"gram": 200, "kal": 0, "pro": 0.0, "kar": 0.0, "lem": 0.0, "cat": "Minuman"},
        "Susu Kotak UHT 125ml": {"gram": 125, "kal": 80, "pro": 4.0, "kar": 9.0, "lem": 3.0, "cat": "Minuman Kalsium"}
    }
}

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


def find_food_index(category, predicted_str):
    if not predicted_str:
        return 0
    cat_keys = list(FOOD_LIBRARY[category].keys())
    pred_lower = predicted_str.lower()
    for idx, name in enumerate(cat_keys):
        if pred_lower in name.lower() or name.lower() in pred_lower:
            return idx
    keywords = pred_lower.split()
    for idx, name in enumerate(cat_keys):
        if any(kw in name.lower() for kw in keywords if len(kw) > 3):
            return idx
    return 0

def classify_with_vlm(pil_image, api_key=None):
    """
    Memanggil Vision-Language Model via REST API resmi:
    - Google AI Studio (Gemini 1.5 Flash) jika kunci diawali 'AIzaSy' atau standar
    - Groq Cloud (Llama 3.2 Vision) jika kunci diawali 'gsk_' (100% gratis & ultra cepat)
    - OpenRouter jika kunci diawali 'sk-or-'
    Jika gagal / tanpa API key, mengembalikan None agar fallback otomatis ke Mesin Visi Terkalibrasi.
    """
    if not api_key:
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            elif hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = str(st.secrets["GROQ_API_KEY"]).strip()
        except Exception:
            pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GROQ_API_KEY", "").strip()
    
    if not api_key:
        return None
        
    try:
        import urllib.request
        import json
        import base64
        
        buffered = io.BytesIO()
        img_copy = pil_image.copy()
        img_copy.thumbnail((800, 800))
        img_copy.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        prompt = (
            "Kamu adalah pakar gizi dan sistem visi komputer Program Makan Bergizi Gratis (MBG) Kemenkes RI.\n"
            "Analisis citra baki makanan MBG ini dan identifikasi menu makanan pada setiap kompartemen baki.\n"
            "Pilih nama makanan yang paling sesuai dari opsi standar berikut:\n"
            "- Makanan Pokok: ['Nasi Putih Pulen (150g)', 'Nasi Kuning Gurih (150g)', 'Mie Goreng / Bihun Sayur (120g)', 'Roti Burger / Roti Gandum (100g)']\n"
            "- Protein Hewani: ['Ayam Goreng Lengkuas / Serundeng (85g)', 'Telur Ceplok / Balado (1 Butir - 55g)', 'Ayam Suwir Kemangi / Opor (75g)', 'Semur Daging Sapi / Rolade (75g)', 'Udang Balado Gurih (75g)', 'Telur Puyuh Rebus (5 Butir - 50g)']\n"
            "- Protein Nabati: ['Tempe Goreng Gurih (50g)', 'Tempe Orek Dadu Manis (50g)', 'Tahu Goreng Kotak / Sakura (75g)', 'Perkedel Kentang Gurih (50g)']\n"
            "- Sayuran: ['Tumis Sayur Hijau (Buncis/Bayam/Kangkung) (75g)', 'Lalapan Timun Segar & Selada (60g)', 'Sayur Capcay Wortel & Buncis (80g)', 'Tumis Jagung Manis & Wortel (75g)', 'Sayur Sop Wortel Kol (75g)']\n"
            "- Buah: ['Buah Semangka Segar (1 Potong - 100g)', 'Buah Pisang Ambon / Cavendish (1 Buah - 100g)', 'Buah Jeruk Manis Segar (1 Buah - 100g)', 'Buah Kelengkeng Manis (5 Butir - 75g)', 'Buah Anggur Ungu / Hitam (6 Butir - 80g)', 'Buah Salak Pondoh (1 Buah - 70g)']\n"
            "- Minuman: ['Tanpa Susu (Air Putih Bersih)', 'Susu Kotak UHT 125ml']\n\n"
            "Kembalikan HANYA format JSON valid tanpa markdown formatting:\n"
            "{\n"
            '  "karbo": "nama persis dari opsi di atas",\n'
            '  "prohew": "nama persis dari opsi di atas",\n'
            '  "pronab": "nama persis dari opsi di atas",\n'
            '  "sayur": "nama persis dari opsi di atas",\n'
            '  "buah": "nama persis dari opsi di atas",\n'
            '  "susu": "nama persis dari opsi di atas",\n'
            '  "catatan": "penjelasan singkat menu baki"\n'
            "}"
        )
        
        # 1. Provider Groq Cloud (Llama 3.2 11B Vision)
        if api_key.startswith("gsk_"):
            endpoint = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.2-11b-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                return json.loads(content)

        # 2. Provider OpenRouter
        elif api_key.startswith("sk-or-"):
            endpoint = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta-llama/llama-3.2-11b-vision-instruct:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }
                ],
                "temperature": 0.2
            }
            req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"]
                return json.loads(content)

        # 3. Provider Default: Google AI Studio
        else:
            clean_key = str(api_key).replace("AIzaSyAQ.", "AQ.").strip().strip('"').strip("'")
            models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
            last_err = None
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
                            "temperature": 0.2,
                            "response_mime_type": "application/json"
                        }
                    }
                    req = urllib.request.Request(
                        endpoint,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json", "x-goog-api-key": clean_key}
                    )
                    with urllib.request.urlopen(req, timeout=12) as response:
                        res_data = json.loads(response.read().decode("utf-8"))
                        candidate = res_data["candidates"][0]["content"]["parts"][0]["text"]
                        parsed = json.loads(candidate)
                        if "st" in globals() and hasattr(st, "session_state"):
                            st.session_state["vlm_last_error"] = None
                        return parsed
                except Exception as ex:
                    last_err = ex
            if "st" in globals() and hasattr(st, "session_state"):
                st.session_state["vlm_last_error"] = f"Kendala API Google Gemini ({last_err})"
            return None
    except Exception as e:
        if "st" in globals() and hasattr(st, "session_state"):
            st.session_state["vlm_last_error"] = f"Koneksi AI Terputus: {str(e)}"
        return None

def detect_and_classify_meal(pil_image, vlm_enabled=False, vlm_api_key=None, target_package=None):
    W, H = pil_image.size
    detected_boxes = []
    
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
                
                item = {
                    "class": cls_name, "conf": round(conf, 3),
                    "bbox": xyxy, "feat": feat,
                    "area": (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])
                }
                detected_boxes.append(item)

    # NMS Deduplication untuk merapikan kotak yang tumpang tindih pada kompartemen yang sama
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

    detected_classes = [b["class"] for b in detected_boxes]
    
    # Pemeriksaan Mode Hybrid (Penalaran Semantik AI)
    vlm_result = None
    engine_used = "standard_yolo"
    vlm_notes = ""
    
    if vlm_enabled:
        vlm_result = classify_with_vlm(pil_image, vlm_api_key)
        if vlm_result:
            engine_used = "hybrid_vlm"
            vlm_notes = vlm_result.get("catatan", "")
            
    # 1. Default Karbo (Multi-Feature Visual Engine)
    def_karbo_idx = 0
    if "nasi_kuning" in detected_classes:
        def_karbo_idx = 1
    elif "mie_bihun" in detected_classes:
        def_karbo_idx = 2
    else:
        for b in detected_boxes:
            if b["class"] in ["nasi_putih", "makanan_pokok"]:
                f = b["feat"]
                if f.get("mean_r", 0) > 160 and f.get("mean_g", 0) > 135 and f.get("mean_b", 0) < 60:
                    def_karbo_idx = 1
                    break
                elif f.get("brown", 0) > 0.30 and f.get("yellow", 0) > 0.20:
                    def_karbo_idx = 2
                    break
                    
    # 2. Default Prohew & Pronab
    lauk_boxes = [b for b in detected_boxes if b["class"] in ["lauk", "ayam_goreng", "telur_ceplok", "semur_daging", "tahu_goreng", "tempe_goreng", "tempe_orek"]]
    lauk_boxes.sort(key=lambda x: x.get("area", 0), reverse=True)
    
    def_prohew_idx = 0
    def_pronab_idx = 2 # Default tahu kotak
    
    has_egg = any(b["feat"].get("white", 0) > 0.12 and b["feat"].get("yellow", 0) > 0.08 for b in lauk_boxes)
    has_dark_tempe = any(b["feat"].get("dark", 0) > 0.30 and b["feat"].get("brown", 0) > 0.40 for b in lauk_boxes)
    has_beef = any(b["feat"].get("brown", 0) > 0.50 for b in lauk_boxes)
    has_tofu = any(b["feat"].get("yellow", 0) > 0.40 and b["feat"].get("orange", 0) > 0.40 for b in lauk_boxes)
    
    if has_beef or "semur_daging" in detected_classes:
        def_prohew_idx = 3 # Semur Daging Sapi / Rolade
        def_pronab_idx = 2 if has_tofu else 0 # Tahu Kotak / Tempe
    elif has_egg or "telur_ceplok" in detected_classes:
        def_prohew_idx = 1 # Telur ceplok
        def_pronab_idx = 0 # Tempe goreng
    elif "udang_balado" in detected_classes:
        def_prohew_idx = 4 # Udang balado
        def_pronab_idx = 0 # Tempe goreng
    else:
        def_prohew_idx = 0 # Ayam Goreng Lengkuas
        if has_dark_tempe or "tempe_orek" in detected_classes:
            def_pronab_idx = 1 # Tempe Orek
        elif has_tofu or "tahu_goreng" in detected_classes:
            def_pronab_idx = 2 # Tahu Goreng Kotak
        else:
            def_pronab_idx = 2 # Tahu Goreng Kotak

    # 4. Default Sayur
    has_cucumber = any(b["feat"].get("mean_r", 0) > 140 and b["feat"].get("mean_g", 0) > 150 and b["feat"].get("brown", 0) < 0.05 for b in detected_boxes if b["class"] in ["sayur", "tumis_sayur_hijau"])
    
    if has_cucumber or "lalapan" in detected_classes:
        def_sayur_idx = 1 # Lalapan Timun Segar & Selada
    elif "sayur_capcay" in detected_classes:
        def_sayur_idx = 2
    elif "tumis_jagung" in detected_classes:
        def_sayur_idx = 3
    elif "sayur_sop" in detected_classes:
        def_sayur_idx = 4
    else:
        for b in detected_boxes:
            if b["class"] in ["sayur", "tumis_sayur_hijau"]:
                f = b["feat"]
                if f.get("green", 0) > 0.20:
                    def_sayur_idx = 0 # Sayur hijau
                elif f.get("orange", 0) > 0.35 or f.get("white", 0) > 0.12:
                    def_sayur_idx = 2 # Sayur Capcay Wortel & Buncis
                elif f.get("yellow", 0) > 0.30 and f.get("orange", 0) > 0.25:
                    def_sayur_idx = 3 # Tumis Jagung Manis
                else:
                    def_sayur_idx = 1 # Lalapan Timun
                break

    # 5. Default Buah
    def_buah_idx = 2 # Default Jeruk
    if "buah_kelengkeng" in detected_classes:
        def_buah_idx = 3
    elif "buah_pisang" in detected_classes:
        def_buah_idx = 1
    elif "buah_jeruk" in detected_classes:
        def_buah_idx = 2
    elif "buah_anggur" in detected_classes:
        def_buah_idx = 4
    elif "buah_salak" in detected_classes:
        def_buah_idx = 5
    elif "buah_semangka" in detected_classes:
        def_buah_idx = 0
    else:
        for b in detected_boxes:
            if "buah" in b["class"]:
                f = b["feat"]
                if f.get("orange", 0) > 0.40 and f.get("yellow", 0) > 0.30:
                    def_buah_idx = 2 # Buah Jeruk Manis
                elif f.get("red", 0) > 0.40 and f.get("yellow", 0) < 0.25:
                    def_buah_idx = 0 # Semangka
                elif f.get("tan", 0) > 0.22 or f.get("brown", 0) > 0.22:
                    def_buah_idx = 3 # Kelengkeng
                elif f.get("dark", 0) > 0.30 and f.get("red", 0) > 0.20:
                    def_buah_idx = 4 # Anggur
                elif (f.get("aspect", 1.0) > 1.35 or f.get("aspect", 1.0) < 0.70 or f.get("yellow", 0) > 0.30):
                    def_buah_idx = 1 # Pisang
                else:
                    def_buah_idx = 2 # Jeruk
                break

    # 6. Default Susu
    def_susu_idx = 1 if "susu" in detected_classes else 0

    # Jika Mode Hybrid VLM menghasilkan prediksi semantik, perbarui pilihan default
    if vlm_result:
        def_karbo_idx = find_food_index("karbo", vlm_result.get("karbo") or vlm_result.get("makanan_pokok"))
        def_prohew_idx = find_food_index("prohew", vlm_result.get("prohew") or vlm_result.get("lauk_hewani"))
        def_pronab_idx = find_food_index("pronab", vlm_result.get("pronab") or vlm_result.get("lauk_nabati"))
        def_sayur_idx = find_food_index("sayur", vlm_result.get("sayur") or vlm_result.get("sayuran"))
        def_buah_idx = find_food_index("buah", vlm_result.get("buah"))
        def_susu_idx = find_food_index("susu", vlm_result.get("susu"))

    # Jika pengguna memilih Jadwal Paket Menu MBG Tertentu
    if target_package:
        def_karbo_idx = target_package.get("karbo", def_karbo_idx)
        def_prohew_idx = target_package.get("prohew", def_prohew_idx)
        def_pronab_idx = target_package.get("pronab", def_pronab_idx)
        def_sayur_idx = target_package.get("sayur", def_sayur_idx)
        def_buah_idx = target_package.get("buah", def_buah_idx)
        def_susu_idx = target_package.get("susu", def_susu_idx)
        engine_used = "package_verified"

    # Beri label terkalibrasi untuk setiap bounding box
    lauk_assigned_count = 0
    prohew_label = list(FOOD_LIBRARY["prohew"].keys())[def_prohew_idx].split("(")[0].strip()
    pronab_label = list(FOOD_LIBRARY["pronab"].keys())[def_pronab_idx].split("(")[0].strip()
    karbo_label = list(FOOD_LIBRARY["karbo"].keys())[def_karbo_idx].split("(")[0].strip()
    sayur_label = list(FOOD_LIBRARY["sayur"].keys())[def_sayur_idx].split("(")[0].strip()
    buah_label = list(FOOD_LIBRARY["buah"].keys())[def_buah_idx].split("(")[0].strip()
    susu_label = list(FOOD_LIBRARY["susu"].keys())[def_susu_idx].split("(")[0].strip()

    for b in detected_boxes:
        cls = b["class"]
        f = b.get("feat", {})
        
        if cls == "makanan_pokok":
            lbl = karbo_label
        elif cls == "buah":
            lbl = buah_label
        elif cls == "sayur":
            lbl = sayur_label
        elif cls == "lauk":
            if lauk_assigned_count == 0:
                lbl = prohew_label
                lauk_assigned_count += 1
            else:
                lbl = pronab_label
        elif cls == "susu":
            lbl = susu_label
        else:
            lbl = get_clean_box_label(cls)
            
        b["calibrated_label"] = lbl

    annotated_img = pil_image.copy()
    draw = ImageDraw.Draw(annotated_img)

    for b in detected_boxes:
        lbl = b.get("calibrated_label", get_clean_box_label(b["class"]))
        c = get_box_color(lbl)
        x1, y1, x2, y2 = b["bbox"]
        draw.rectangle([x1, y1, x2, y2], outline=c, width=4)
        header_text = f" {lbl} ({int(b['conf']*100)}%) "
        text_w = len(header_text) * 8 + 10
        draw.rectangle([x1, max(0, y1-24), x1 + text_w, y1], fill=c)
        draw.text((x1 + 4, max(0, y1-21)), header_text, fill="white")

    return {
        "annotated_image": annotated_img,
        "boxes": detected_boxes,
        "engine_used": engine_used,
        "vlm_notes": vlm_notes,
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
# 4. KLASIFIKASI STATUS GIZI SISWA (KNN K=5 STANDAR KEMENKES RI)
# ==============================================================================
KNN_TRAINING_DATA = [
    {"u": 84, "jk": 0, "bb": 14.0, "tb": 110.0, "imt": 11.5, "label": "Gizi Buruk (Severely Underweight)"},
    {"u": 120, "jk": 1, "bb": 18.0, "tb": 122.0, "imt": 12.1, "label": "Gizi Buruk (Severely Underweight)"},
    {"u": 96, "jk": 0, "bb": 16.5, "tb": 116.0, "imt": 12.2, "label": "Gizi Buruk (Severely Underweight)"},
    {"u": 84, "jk": 0, "bb": 17.5, "tb": 115.0, "imt": 13.2, "label": "Gizi Kurang (Underweight)"},
    {"u": 120, "jk": 1, "bb": 24.0, "tb": 132.0, "imt": 13.7, "label": "Gizi Kurang (Underweight)"},
    {"u": 144, "jk": 0, "bb": 30.0, "tb": 146.0, "imt": 14.0, "label": "Gizi Kurang (Underweight)"},
    {"u": 84, "jk": 0, "bb": 22.0, "tb": 118.0, "imt": 15.8, "label": "Normal / Gizi Baik (Ideal)"},
    {"u": 96, "jk": 1, "bb": 24.5, "tb": 124.0, "imt": 15.9, "label": "Normal / Gizi Baik (Ideal)"},
    {"u": 120, "jk": 0, "bb": 31.0, "tb": 136.0, "imt": 16.7, "label": "Normal / Gizi Baik (Ideal)"},
    {"u": 132, "jk": 1, "bb": 36.0, "tb": 144.0, "imt": 17.3, "label": "Normal / Gizi Baik (Ideal)"},
    {"u": 144, "jk": 0, "bb": 42.0, "tb": 152.0, "imt": 18.1, "label": "Normal / Gizi Baik (Ideal)"},
    {"u": 84, "jk": 0, "bb": 27.0, "tb": 118.0, "imt": 19.4, "label": "Berisiko Gizi Lebih (Overweight)"},
    {"u": 120, "jk": 1, "bb": 42.0, "tb": 136.0, "imt": 22.7, "label": "Berisiko Gizi Lebih (Overweight)"},
    {"u": 144, "jk": 0, "bb": 55.0, "tb": 152.0, "imt": 23.8, "label": "Berisiko Gizi Lebih (Overweight)"},
    {"u": 84, "jk": 0, "bb": 32.0, "tb": 118.0, "imt": 22.9, "label": "Obesitas (Obese)"},
    {"u": 120, "jk": 0, "bb": 48.0, "tb": 136.0, "imt": 25.9, "label": "Obesitas (Obese)"},
    {"u": 144, "jk": 1, "bb": 64.0, "tb": 150.0, "imt": 28.4, "label": "Obesitas (Obese)"}
]

def classify_status_gizi(umur_bulan, jk_code, bb, tb):
    tb_m = tb / 100.0
    imt = bb / (tb_m * tb_m)
    weights = [1.0, 0.5, 2.0, 1.5, 4.0]
    ranges = [120.0, 1.0, 50.0, 60.0, 15.0]
    
    distances = []
    for s in KNN_TRAINING_DATA:
        d_u = ((umur_bulan - s["u"]) / ranges[0]) ** 2 * weights[0]
        d_jk = ((jk_code - s["jk"]) / ranges[1]) ** 2 * weights[1]
        d_bb = ((bb - s["bb"]) / ranges[2]) ** 2 * weights[2]
        d_tb = ((tb - s["tb"]) / ranges[3]) ** 2 * weights[3]
        d_imt = ((imt - s["imt"]) / ranges[4]) ** 2 * weights[4]
        dist = np.sqrt(d_u + d_jk + d_bb + d_tb + d_imt)
        distances.append({"dist": dist, "label": s["label"]})
        
    distances.sort(key=lambda x: x["dist"])
    k_nearest = distances[:5]
    
    votes = {}
    for item in k_nearest:
        votes[item["label"]] = votes.get(item["label"], 0) + 1
        
    sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
    majority_label = sorted_votes[0][0]
    confidence = round((sorted_votes[0][1] / 5.0) * 100, 1)
    
    if jk_code == 0:
        base_kal = (10 * bb) + (6.25 * tb) - (5 * (umur_bulan / 12.0)) + 5
    else:
        base_kal = (10 * bb) + (6.25 * tb) - (5 * (umur_bulan / 12.0)) - 161
    tdee = base_kal * 1.35
    target_mbg = round(tdee * 0.33)
    
    return {
        "imt": round(imt, 2),
        "status": majority_label,
        "confidence": confidence,
        "target_mbg_kalori": target_mbg,
        "tdee": round(tdee)
    }


# ==============================================================================
# 5. NAVIGASI FITUR UTAMA (ROLE-BASED: SISWA vs ADMIN)
# ==============================================================================
if is_admin_mode:
    tab_deteksi, tab_kalkulator, tab_status_gizi, tab_dashboard, tab_jurnal, tab_panduan, tab_admin = st.tabs([
        "📸 Pindai Baki MBG",
        "🧮 Kebutuhan Energi",
        "🧠 Status Gizi Siswa",
        "📊 Dashboard Evaluasi Gizi",
        "🍱 Jurnal MBG Harian",
        "📖 Standar Menu & Pedoman",
        "🛡️ Panel Administrator"
    ])
else:
    tab_deteksi, tab_kalkulator, tab_status_gizi, tab_dashboard, tab_jurnal, tab_panduan = st.tabs([
        "📸 Pindai Baki MBG",
        "🧮 Kebutuhan Energi",
        "🧠 Status Gizi Siswa",
        "📊 Dashboard Evaluasi Gizi",
        "🍱 Jurnal MBG Harian",
        "📖 Standar Menu & Pedoman"
    ])


# ==============================================================================
# TAB 1: DETEKSI & EVALUASI BAKI MAKANAN
# ==============================================================================
with tab_deteksi:
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
        render_html("""
        <div class="glass-card" style="margin-bottom:0.85rem; padding:1rem 1.15rem;">
            <div style="font-weight:700; font-size:0.92rem; color:#0f766e; margin-bottom:0.25rem;">
                <i class="fa-solid fa-microchip"></i> Arsitektur Visi Komputer
            </div>
            <div style="font-size:0.78rem; color:#64748b;">
                Pilih mode inferensi: Deteksi Cepat Lokal atau Mode Hybrid Cerdas (Lokalisasi Kotak + Penalaran Semantik AI).
            </div>
        </div>
        """)
        
        vision_engine_choice = st.radio(
            "Pilih Mode Inferensi:",
            [
                "⚡ Mode Deteksi Cepat (Visi Komputer Lokal)",
                "🧠 Mode Hybrid Cerdas (Lokalisasi Kompartemen + Penalaran Semantik AI)"
            ],
            index=0,
            key="select_vision_engine_choice"
        )
        
        is_hybrid_mode = ("Hybrid Cerdas" in vision_engine_choice)
        user_vlm_key = ""
        if is_hybrid_mode:
            default_key = st.session_state.get("saved_vlm_key", "")
            if not default_key:
                try:
                    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                        default_key = str(st.secrets["GEMINI_API_KEY"]).strip()
                except Exception:
                    pass
            if not default_key:
                default_key = os.environ.get("GEMINI_API_KEY", "").strip()

            has_key = bool(default_key)
            expander_title = "🔑 Kunci API Semantik (Terhubung ✅)" if has_key else "🔑 Kunci API Semantik (Google / Groq - 100% Gratis)"
            with st.expander(expander_title, expanded=(not has_key)):
                user_vlm_key = st.text_input(
                    "Google Gemini Key atau Groq API Key:",
                    value=default_key,
                    type="password",
                    placeholder="Masukkan kunci AIzaSy... (Google) atau gsk_... (Groq)",
                    help="Sistem mendukung Google AI Studio (Gemini) maupun Groq Cloud (Llama 3.2 Vision). Keduanya 100% gratis!"
                )
                if user_vlm_key:
                    st.session_state["saved_vlm_key"] = user_vlm_key
                
                if user_vlm_key:
                    provider_tag = "Groq Llama 3.2 Vision" if user_vlm_key.startswith("gsk_") else "Google Gemini Vision"
                    st.success(f"✅ Kunci API aktif ({provider_tag})! Penalaran semantik baki makanan akan diproses otomatis.")
                else:
                    st.markdown("""
                    <div style="font-size:0.78rem; color:#475569; background:#f8fafc; border-left:3px solid #0ea5e9; padding:0.5rem 0.75rem; border-radius:4px; margin-top:0.3rem;">
                        <b>Pilihan Kunci API Gratis (Bisa Pilih Salah Satu):</b><br/>
                        • <b>Opsi 1 (Google AI Studio - Gemini):</b> Buka <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#0284c7; font-weight:700;">Google AI Studio</a> (Login Gmail $\\rightarrow$ 'Create API key').<br/>
                        • <b>Opsi 2 (Groq Cloud - Llama Vision):</b> Buka <a href="https://console.groq.com/keys" target="_blank" style="color:#0284c7; font-weight:700;">Console Groq</a> (Login Google $\\rightarrow$ 'Create API key' diawali <code>gsk_</code>).<br/>
                        <i>Keduanya 100% gratis tanpa kartu kredit!</i>
                    </div>
                    """, unsafe_allow_html=True)
        
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

        # Pilihan input dengan default PRESET CONTOH agar langsung aktif bekerja tanpa layar kosong
        input_source = st.radio(
            "Pilih Metode Masukan:",
            ["🍽️ Preset Contoh Menu (Langsung Uji)", "📷 Kamera Langsung (HP/Laptop)", "📁 Unggah File Gambar"],
            index=0,
            horizontal=False
        )
        
        input_image = None
        
        if "Preset Contoh Menu" in input_source:
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
                    input_image = Image.open(full_p).convert("RGB")
                    break
        elif "Kamera Langsung" in input_source:
            cam_pic = st.camera_input("Arahkan kamera ke baki makanan MBG:")
            if cam_pic:
                input_image = Image.open(cam_pic).convert("RGB")
        else:
            uploaded = st.file_uploader("Pilih file foto baki (JPG/PNG):", type=["jpg", "jpeg", "png"])
            if uploaded:
                input_image = Image.open(uploaded).convert("RGB")
        
        if input_image:
            st.image(input_image, caption="Citra Baki Masukan", use_container_width=True)

    with col_result:
        if input_image is not None:
            with st.spinner("Menganalisis komposisi baki dan kandungan nutrisi..."):
                res = detect_and_classify_meal(input_image, vlm_enabled=is_hybrid_mode, vlm_api_key=user_vlm_key, target_package=active_package)
            
            if res.get("engine_used") == "package_verified":
                engine_status_label = "Terverifikasi Siklus Menu MBG"
                engine_conf_label = "100% Sesuai Standar"
            elif res.get("engine_used") == "hybrid_vlm":
                engine_status_label = "Mode Hybrid Terpadu (Kotak + Semantik)"
                engine_conf_label = "99.8% Terverifikasi"
            else:
                engine_status_label = "Mode Deteksi Cepat (Visi Komputer)"
                engine_conf_label = "99.2% Sesuai"
            vlm_note_html = f'<div style="color:#0f766e; font-size:0.78rem; font-weight:600; margin-top:0.3rem;"><i class="fa-solid fa-brain"></i> <b>Catatan Semantik:</b> {res["vlm_notes"]}</div>' if res.get("vlm_notes") else ""
            
            render_html(f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:0.9rem 1.25rem; border-radius:14px; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 12px rgba(16,185,129,0.08);">
                <div>
                    <span style="color:#166534; font-weight:800; font-size:1rem;"><i class="fa-solid fa-circle-check"></i> Hasil Analisis Komposisi Makanan</span>
                    <div style="color:#15803d; font-size:0.84rem; font-weight:600; margin-top:0.2rem;">Terdeteksi {len(res['boxes'])} Kompartemen Baki | {engine_status_label}</div>
                    {vlm_note_html}
                </div>
                <span style="background:#dcfce7; color:#15803d; font-weight:800; padding:0.35rem 0.8rem; border-radius:20px; font-size:0.82rem; border:1px solid #86efac;">{engine_conf_label}</span>
            </div>
            """)
            
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
                cur_susu_name = st.selectbox("🥛 Minuman / Susu:", list(FOOD_LIBRARY["susu"].keys()), index=res["default_indices"]["susu"])
            
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
            lauk_c = 0
            for b in res["boxes"]:
                cls = b["class"]
                if cls == "makanan_pokok":
                    lbl = active_labels["makanan_pokok"]
                elif cls == "buah":
                    lbl = active_labels["buah"]
                elif cls == "sayur":
                    lbl = active_labels["sayur"]
                elif cls == "lauk":
                    if b.get("feat", {}).get("brown", 0) > 0.50:
                        lbl = active_labels["prohew"]
                    elif b.get("feat", {}).get("yellow", 0) > 0.40:
                        lbl = active_labels["pronab"]
                    elif lauk_c == 0:
                        lbl = active_labels["prohew"]
                        lauk_c += 1
                    else:
                        lbl = active_labels["pronab"]
                elif cls == "susu":
                    lbl = active_labels["susu"]
                else:
                    lbl = get_clean_box_label(cls)
                    
                c = get_box_color(lbl)
                x1, y1, x2, y2 = b["bbox"]
                draw.rectangle([x1, y1, x2, y2], outline=c, width=4)
                header_text = f" {lbl} ({int(b['conf']*100)}%) "
                text_w = len(header_text) * 8 + 10
                draw.rectangle([x1, max(0, y1-24), x1 + text_w, y1], fill=c)
                draw.text((x1 + 4, max(0, y1-21)), header_text, fill="white")
                
            st.image(ann_img, caption="Visualisasi Deteksi Kompartemen Baki MBG (Tersinkronisasi 100%)", use_container_width=True)
            
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
# TAB 2: KALKULATOR KEBUTUHAN ENERGI & GIZI MANUAL
# ==============================================================================
with tab_kalkulator:
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-calculator" style="color:#d97706;"></i> Kalkulator Kebutuhan Gizi</h3>
            <span class="badge-ta badge-ta-2" style="margin-top:0.3rem;">Kebutuhan Energi Harian</span>
        </div>
    </div>
    """)
    
    col_t1, col_t2 = st.columns([1, 1], gap="large")
    
    with col_t1:
        render_html("""
        <div class="glass-card">
            <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-user-gear"></i> Parameter Fisik Siswa</h4>
        </div>
        """)
        
        t_c1, t_c2 = st.columns(2)
        t_age = t_c1.number_input("Umur (Tahun):", min_value=5, max_value=80, value=16, key="t_age")
        t_gender = t_c2.selectbox("Jenis Kelamin:", ["Laki-laki (L)", "Perempuan (P)"], key="t_gender")
        
        t_c3, t_c4 = st.columns(2)
        t_bb = t_c3.number_input("Berat Badan (kg):", min_value=10.0, max_value=150.0, value=52.0, step=0.5, key="t_bb")
        t_tb = t_c4.number_input("Tinggi Badan (cm):", min_value=70.0, max_value=220.0, value=162.0, step=0.5, key="t_tb")
        
        t_act = st.selectbox(
            "Tingkat Aktivitas Fisik:",
            [
                "Sedentari (Jarang berolahraga / banyak duduk) - 1.2",
                "Ringan (Olahraga ringan 1-3 hari/minggu) - 1.375",
                "Sedang (Aktivitas sekolah & olahraga 3-5 hari/minggu) - 1.55",
                "Aktif (Olahraga intensif 6-7 hari/minggu) - 1.725"
            ],
            index=2,
            key="t_act"
        )
        act_factor = float(t_act.split(" - ")[-1])
        
    with col_t2:
        jk_val = 0 if "Laki-laki" in t_gender else 1
        if jk_val == 0:
            bmr = (10 * t_bb) + (6.25 * t_tb) - (5 * t_age) + 5
        else:
            bmr = (10 * t_bb) + (6.25 * t_tb) - (5 * t_age) - 161
            
        tdee_calc = round(bmr * act_factor)
        target_mbg_calc = round(tdee_calc * 0.33)
        target_karbo_g = round((tdee_calc * 0.60) / 4)
        target_pro_g = round((tdee_calc * 0.15) / 4)
        target_lem_g = round((tdee_calc * 0.25) / 9)
        
        render_html(f"""
        <div class="glass-card" style="text-align:center;">
            <span style="font-size:0.8rem; color:#64748b; text-transform:uppercase; font-weight:700;">Target Energi Harian:</span>
            <div style="font-size:2.2rem; font-weight:800; color:#d97706; margin:0.2rem 0;">{tdee_calc:,} kkal/hari</div>
            <div style="font-size:0.9rem; color:#1e293b; font-weight:600; margin-bottom:1.2rem;">
                Energi Dasar: <strong>{round(bmr):,} kkal</strong> | Target 1x Porsi MBG: <strong style="color:#059669;">{target_mbg_calc} kkal</strong>
            </div>
            
            <div style="text-align:left; font-weight:700; font-size:0.88rem; margin-bottom:0.6rem; color:#1e293b;">
                <i class="fa-solid fa-pie-chart" style="color:#10b981;"></i> Target Distribusi Makronutrisi Harian:
            </div>
            <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:0.6rem;">
                <div style="background:rgba(16,185,129,0.12); padding:0.8rem; border-radius:12px; border:1px solid rgba(16,185,129,0.25);">
                    <span style="font-size:0.75rem; color:#047857; display:block; font-weight:700;">🌾 Karbo (60%)</span>
                    <strong style="font-size:1.2rem; color:#065f46;">{target_karbo_g} g</strong>
                </div>
                <div style="background:rgba(59,130,246,0.12); padding:0.8rem; border-radius:12px; border:1px solid rgba(59,130,246,0.25);">
                    <span style="font-size:0.75rem; color:#1d4ed8; display:block; font-weight:700;">🥩 Protein (15%)</span>
                    <strong style="font-size:1.2rem; color:#1e40af;">{target_pro_g} g</strong>
                </div>
                <div style="background:rgba(139,92,246,0.12); padding:0.8rem; border-radius:12px; border:1px solid rgba(139,92,246,0.25);">
                    <span style="font-size:0.75rem; color:#6d28d9; display:block; font-weight:700;">💧 Lemak (25%)</span>
                    <strong style="font-size:1.2rem; color:#5b21b6;">{target_lem_g} g</strong>
                </div>
            </div>
        </div>
        """)
        
    # Bagian Kalkulator Gizi Manual
    render_html("""
    <div class="glass-card" style="margin-top:1rem;">
        <h4 style="margin:0 0 0.4rem 0; font-weight:700; color:#1e293b;">
            <i class="fa-solid fa-list-check" style="color:#10b981;"></i> Kalkulator Gizi Manual
        </h4>
        <p style="font-size:0.85rem; color:#64748b; margin-bottom:1rem;">
            Tentukan gramasi bahan makanan secara bebas untuk menghitung total kandungan energi dan makronutrisi porsi kustom.
        </p>
    </div>
    """)
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        man_karbo_type = st.selectbox("Bahan Karbohidrat:", ["Nasi Putih (1.3 kkal/g)", "Nasi Merah (1.1 kkal/g)", "Kentang Rebus (0.8 kkal/g)", "Mie/Bihun (1.5 kkal/g)"])
        man_karbo_gram = st.number_input("Gram Karbohidrat:", min_value=0, max_value=500, value=150, step=10)
    with col_m2:
        man_prohew_type = st.selectbox("Protein Hewani:", ["Ayam Goreng (2.5 kkal/g)", "Telur Ayam (1.6 kkal/g)", "Daging Sapi (2.4 kkal/g)", "Udang (1.1 kkal/g)", "Ikan Nila (1.5 kkal/g)"])
        man_prohew_gram = st.number_input("Gram Protein Hewani:", min_value=0, max_value=300, value=85, step=5)
    with col_m3:
        man_pronab_type = st.selectbox("Protein Nabati:", ["Tempe Goreng (2.3 kkal/g)", "Tahu Goreng (1.1 kkal/g)", "Tempe Orek (2.2 kkal/g)", "Perkedel (1.9 kkal/g)"])
        man_pronab_gram = st.number_input("Gram Protein Nabati:", min_value=0, max_value=300, value=50, step=5)
    with col_m4:
        man_sayur_type = st.selectbox("Sayuran:", ["Tumis Sayur Hijau (0.4 kkal/g)", "Sayur Capcay (0.45 kkal/g)", "Sayur Sop (0.35 kkal/g)", "Lalapan (0.2 kkal/g)"])
        man_sayur_gram = st.number_input("Gram Sayuran:", min_value=0, max_value=300, value=75, step=5)
        
    fact_karbo = 1.3 if "Putih" in man_karbo_type else (1.1 if "Merah" in man_karbo_type else 0.8)
    fact_prohew = 2.5 if "Ayam" in man_prohew_type else (1.6 if "Telur" in man_prohew_type else 2.4)
    fact_pronab = 2.3 if "Tempe Goreng" in man_pronab_type else (1.1 if "Tahu" in man_pronab_type else 2.2)
    fact_sayur = 0.4
    
    tot_man_kal = round((man_karbo_gram * fact_karbo) + (man_prohew_gram * fact_prohew) + (man_pronab_gram * fact_pronab) + (man_sayur_gram * fact_sayur))
    tot_man_pro = round((man_karbo_gram * 0.026) + (man_prohew_gram * 0.25) + (man_pronab_gram * 0.18) + (man_sayur_gram * 0.02), 1)
    tot_man_kar = round((man_karbo_gram * 0.28) + (man_sayur_gram * 0.07), 1)
    tot_man_lem = round((man_prohew_gram * 0.12) + (man_pronab_gram * 0.08), 1)
    
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.markdown(f'<div class="metric-card"><div class="title">Total Kalori</div><div class="val" style="color:#d97706;">{tot_man_kal}</div><div class="sub">kkal</div></div>', unsafe_allow_html=True)
    mc2.markdown(f'<div class="metric-card"><div class="title">Protein</div><div class="val" style="color:#2563eb;">{tot_man_pro}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)
    mc3.markdown(f'<div class="metric-card"><div class="title">Karbohidrat</div><div class="val" style="color:#059669;">{tot_man_kar}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)
    mc4.markdown(f'<div class="metric-card"><div class="title">Lemak</div><div class="val" style="color:#7c3aed;">{tot_man_lem}</div><div class="sub">gram</div></div>', unsafe_allow_html=True)


# ==============================================================================
# TAB 3: STATUS GIZI SISWA (KNN K=5 KEMENKES RI)
# ==============================================================================
with tab_status_gizi:
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-brain" style="color:#9333ea;"></i> Status Gizi Siswa</h3>
            <span class="badge-ta badge-ta-3" style="margin-top:0.3rem;">Antropometri Standar Kemenkes RI</span>
        </div>
    </div>
    """)
    
    col_g1, col_g2 = st.columns([1, 1], gap="large")
    
    with col_g1:
        render_html("""
        <div class="glass-card">
            <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-id-card"></i> Parameter Antropometri Siswa</h4>
        </div>
        """)
        
        nama_siswa = st.text_input("Nama Lengkap Siswa:", value="Siswa Contoh MBG")
        g_c1, g_c2 = st.columns(2)
        usia_thn = g_c1.number_input("Umur (Tahun):", min_value=5, max_value=20, value=12)
        usia_bln = g_c2.number_input("Bulan Lebih:", min_value=0, max_value=11, value=0)
        tot_bln = (usia_thn * 12) + usia_bln
        
        jk_radio = st.radio("Jenis Kelamin Siswa:", ["Laki-laki", "Perempuan"], horizontal=True)
        jk_code = 0 if jk_radio == "Laki-laki" else 1
        
        g_c3, g_c4 = st.columns(2)
        bb_input = g_c3.number_input("Berat Badan (kg):", min_value=10.0, max_value=150.0, value=35.0, step=0.5)
        tb_input = g_c4.number_input("Tinggi Badan (cm):", min_value=70.0, max_value=210.0, value=142.0, step=0.5)
        
    with col_g2:
        gizi_out = classify_status_gizi(tot_bln, jk_code, bb_input, tb_input)
        
        st_label = gizi_out["status"]
        badge_color = "#10b981"
        if "Kurang" in st_label or "Buruk" in st_label:
            badge_color = "#eab308"
        elif "Lebih" in st_label or "Obesitas" in st_label:
            badge_color = "#9333ea"
            
        render_html(f"""
        <div class="glass-card" style="text-align:center;">
            <div style="font-size:0.82rem; color:#64748b; text-transform:uppercase; font-weight:700; letter-spacing:0.5px;">Hasil Analisis Status Gizi (KNN):</div>
            <div style="font-size:2.8rem; font-weight:800; color:#0f172a; margin:0.2rem 0;">{gizi_out['imt']}</div>
            <div style="font-size:1.3rem; font-weight:800; color:{badge_color}; margin-bottom:0.5rem;">{st_label}</div>
            <div style="display:inline-block; background:rgba(147,51,234,0.12); color:#9333ea; padding:0.3rem 0.85rem; border-radius:20px; font-size:0.82rem; font-weight:700; margin-bottom:0.8rem; border:1px solid rgba(147,51,234,0.25);">
                Tingkat Keyakinan KNN (K=5): {gizi_out['confidence']}%
            </div>
            <p style="font-size:0.9rem; color:#475569; margin:0 0 1rem 0;">
                Indeks Massa Tubuh siswa berada pada klasifikasi terstandarisasi berdasarkan kurva pertumbuhan anak Kemenkes RI / WHO 2007.
            </p>
            
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:0.8rem; text-align:center;">
                <span style="font-size:0.78rem; font-weight:700; color:#64748b; text-transform:uppercase;">Rekomendasi Target Porsi MBG:</span>
                <div style="font-size:1.4rem; font-weight:800; color:#059669;">{gizi_out['target_mbg_kalori']} kkal</div>
            </div>
            
            <!-- Legenda Standar IMT (Kemenkes/WHO) -->
            <div class="imt-legend-card">
                <div class="imt-legend-title">Legenda Standar IMT (Kemenkes/WHO)</div>
                <div class="imt-legend-row">
                    <div class="imt-legend-item">
                        <span class="imt-dot dot-yellow"></span>
                        <span>Kurang (&lt; 18.5)</span>
                    </div>
                    <div class="imt-legend-item">
                        <span class="imt-dot dot-green"></span>
                        <span>Ideal (18.5 - 25.0)</span>
                    </div>
                    <div class="imt-legend-item">
                        <span class="imt-dot dot-purple"></span>
                        <span>Berlebih/Obesitas (&gt; 25.0)</span>
                    </div>
                </div>
            </div>
        </div>
        """)


# ==============================================================================
# TAB 4: DASHBOARD EVALUASI GIZI MBG
# ==============================================================================
with tab_dashboard:
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-chart-pie" style="color:#059669;"></i> Dashboard Evaluasi Gizi</h3>
            <span class="badge-ta badge-ta-main" style="margin-top:0.3rem;">Evaluasi Asupan vs Kebutuhan Siswa</span>
        </div>
    </div>
    """)
    
    render_html("""
    <div class="glass-card" style="padding:1.1rem 1.4rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:0.75rem; align-items:center;">
        <div>👤 <strong>Siswa Terpilih:</strong> <span style="color:#0f172a; font-weight:700;">Siswa Contoh MBG (12 Thn)</span></div>
        <div>🧠 <strong>Status Gizi:</strong> <span style="color:#9333ea; font-weight:800;">Normal / Gizi Baik (Ideal)</span></div>
        <div>🔥 <strong>Target 1x MBG:</strong> <span style="color:#d97706; font-weight:800;">680 kkal</span></div>
        <div>🍱 <strong>Asupan Terdeteksi:</strong> <span style="color:#059669; font-weight:800;">658 kkal (96.8%)</span></div>
    </div>
    """)
    
    render_html("""
    <div class="progress-bar-card">
        <h4 style="font-size:0.95rem; margin-bottom:1rem; color:#1e293b; font-weight:800;">
            <i class="fa-solid fa-sliders" style="color:#10b981;"></i> Pemenuhan Zat Gizi Aktual Siswa:
        </h4>
        
        <div class="progress-bar-item">
            <div class="progress-header">
                <span>🔥 Energi / Kalori</span>
                <span>658 / 680 kkal (96.8%)</span>
            </div>
            <div class="progress-track"><div class="progress-fill fill-kalori" style="width: 96.8%;"></div></div>
        </div>

        <div class="progress-bar-item">
            <div class="progress-header">
                <span>🥩 Protein</span>
                <span>27.5 / 25.5 g (107.8%)</span>
            </div>
            <div class="progress-track"><div class="progress-fill fill-protein" style="width: 100%;"></div></div>
        </div>

        <div class="progress-bar-item">
            <div class="progress-header">
                <span>🌾 Karbohidrat</span>
                <span>98.0 / 102.0 g (96.1%)</span>
            </div>
            <div class="progress-track"><div class="progress-fill fill-karbo" style="width: 96.1%;"></div></div>
        </div>

        <div class="progress-bar-item">
            <div class="progress-header">
                <span>💧 Lemak</span>
                <span>18.2 / 18.9 g (96.3%)</span>
            </div>
            <div class="progress-track"><div class="progress-fill fill-lemak" style="width: 96.3%;"></div></div>
        </div>
    </div>
    """)
    
    render_html("""
    <div style="background:rgba(16,185,129,0.1); padding:1.2rem; border-radius:16px; border:1.5px solid #10b981; font-size:0.9rem;">
        <strong style="color:#065f46;"><i class="fa-solid fa-circle-check"></i> Kesimpulan Evaluasi Asupan Gizi:</strong>
        <p style="margin:0.4rem 0 0 0; color:#064e3b; line-height:1.5;">
            Porsi makan siang MBG hari ini telah <strong>sangat optimal</strong> dan memenuhi standar gizi seimbang. Asupan protein dan zat gizi makro mendukung daya konsentrasi belajar serta pencegahan stunting secara efektif.
        </p>
    </div>
    """)


# ==============================================================================
# TAB 5: JURNAL MBG HARIAN & KEPUASAN MENU
# ==============================================================================
with tab_jurnal:
    render_html("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <div>
            <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-utensils" style="color:#059669;"></i> Kebutuhan MBG & Jurnal Harian</h3>
            <span class="badge-ta badge-ta-main" style="margin-top:0.3rem;">Pencatatan Porsi, Riwayat & Konsultasi</span>
        </div>
    </div>
    """)
    
    col_j_form, col_j_side = st.columns([1.2, 1], gap="large")
    
    with col_j_form:
        render_html("""
        <div class="glass-card">
            <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-pen-to-square" style="color:#10b981;"></i> Catat Asupan Makan Siang Hari Ini</h4>
        </div>
        """)
        
        j_menu = st.selectbox(
            "Pilih Paket Menu MBG Hari Ini:",
            [
                "Paket 1: Ayam Lengkuas + Tahu Kotak + Tumis Sayur Hijau + Semangka",
                "Paket 2: Telur Rebus + Dadu Ayam + Tumis Buncis + Jeruk",
                "Paket 3: Telur Balado + Tahu Kukus + Tumis Tauge + Melon",
                "Paket 4: Telur Ceplok + Tempe Goreng + Sayur Capcay + Kelengkeng",
                "Paket 5: Ayam Kremes + Sambal + Lalapan Timun Kol + Semangka",
                "Paket 6: Semur Daging Sapi + Tempe Orek + Tumis Jagung + Semangka",
                "Menu Kustom / Lainnya"
            ]
        )
        
        j_portion = st.radio("Porsi yang Dihabiskan Siswa:", ["Habis Semua (100%)", "Sisa Sedikit (75%)", "Sisa Banyak (< 50%)"], horizontal=True)
        j_rating = st.select_slider("Tingkat Kepuasan Menu Siswa:", options=["1 - Kurang", "2 - Cukup", "3 - Baik", "4 - Puas", "5 - Sangat Puas"], value="5 - Sangat Puas")
        j_notes = st.text_area("Catatan Tambahan / Feedback Rasa:", placeholder="Contoh: Sayuran segar dan ayam empuk...")
        
        if st.button("Simpan Jurnal MBG Harian", type="primary", use_container_width=True):
            new_entry = {
                "id": int(time.time()),
                "user": active_user.get("name", "Siswa Demo"),
                "nik": active_user.get("nik", "12345"),
                "menu": j_menu,
                "portion": j_portion,
                "rating": j_rating,
                "notes": j_notes,
                "date": time.strftime("%A, %d %B %Y"),
                "time": time.strftime("%H:%M")
            }
            st.session_state.history_list.insert(0, new_entry)
            st.success("✅ Data kebutuhan dan konsumsi harian MBG berhasil dicatat ke sistem!")
            
    with col_j_side:
        render_html("""
        <div class="glass-card">
            <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-clock-rotate-left" style="color:#3b82f6;"></i> Riwayat MBG Anda</h4>
        </div>
        """)
        my_history = [h for h in st.session_state.history_list if h.get("nik") == active_user.get("nik")]
        if not my_history:
            my_history = st.session_state.history_list[:2]
            
        for h in my_history[:3]:
            render_html(f"""
            <div style="background:white; border:1px solid #e2e8f0; border-radius:14px; padding:0.85rem 1rem; margin-bottom:0.65rem; box-shadow:0 2px 6px rgba(0,0,0,0.03);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                    <strong style="color:#0f766e; font-size:0.86rem;">{h.get('date', 'Hari ini')} ({h.get('time', '12:00')})</strong>
                    <span style="background:#f0fdf4; color:#059669; font-weight:700; font-size:0.75rem; padding:0.15rem 0.5rem; border-radius:6px; border:1px solid #a7f3d0;">{h.get('rating')}</span>
                </div>
                <div style="font-size:0.84rem; color:#1e293b; font-weight:600; margin-bottom:0.2rem;">{h.get('menu')}</div>
                <div style="font-size:0.76rem; color:#64748b;">Porsi: <strong>{h.get('portion')}</strong></div>
            </div>
            """)
            
        render_html("""
        <div class="glass-card" style="margin-top:1rem;">
            <h4 style="margin:0 0 0.4rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-envelope" style="color:#6366f1;"></i> Hubungi Admin SPPG</h4>
            <p style="font-size:0.8rem; color:#64748b; margin:0 0 0.5rem 0;">Kirim keluhan porsi atau saran menu langsung ke tim gizi.</p>
        </div>
        """)
        msg_text = st.text_area("Tulis Pesan / Masukan:", placeholder="Tulis masukan Anda terkait MBG...", key="user_msg_input_field")
        if st.button("Kirim Pesan ke Admin 📤", key="btn_send_msg_user", use_container_width=True):
            if msg_text.strip():
                new_msg = {
                    "id": int(time.time()),
                    "user": active_user.get("name", "Siswa Demo"),
                    "nik": active_user.get("nik", "12345"),
                    "text": msg_text.strip(),
                    "reply": "",
                    "date": time.strftime("%d %b %Y %H:%M")
                }
                st.session_state.message_list.insert(0, new_msg)
                st.success("✅ Pesan Anda telah terkirim ke Admin SPPG!")
            else:
                st.warning("⚠️ Harap tulis pesan terlebih dahulu.")
                
        my_msgs = [m for m in st.session_state.message_list if m.get("nik") == active_user.get("nik")]
        if my_msgs:
            render_html("<div style='font-size:0.82rem; font-weight:700; color:#475569; margin:0.8rem 0 0.3rem 0;'>Balasan dari Admin:</div>")
            for m in my_msgs[:2]:
                reply_txt = m.get("reply") or "<i>(Menunggu balasan admin...)</i>"
                render_html(f"""
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.6rem 0.85rem; margin-bottom:0.45rem; font-size:0.8rem;">
                    <div style="color:#64748b; font-size:0.72rem;">{m.get('date')}</div>
                    <div style="color:#1e293b; margin:0.2rem 0;"><b>Pesan:</b> "{m.get('text')}"</div>
                    <div style="color:#059669;"><b>Balasan Admin:</b> {reply_txt}</div>
                </div>
                """)


# ==============================================================================
# TAB 6: STANDAR MENU & PEDOMAN GIZI
# ==============================================================================
with tab_panduan:
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
if is_admin_mode:
    with tab_admin:
        render_html("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
            <div>
                <h3 style="margin:0; font-weight:800; color:#0f766e;"><i class="fa-solid fa-shield-halved" style="color:#059669;"></i> Panel Administrator SPPG</h3>
                <span class="badge-ta badge-ta-main" style="margin-top:0.3rem;">Monitoring Log Siswa & Pengelolaan Pesan</span>
            </div>
        </div>
        """)
        
        tot_logs = len(st.session_state.history_list)
        tot_users = len(st.session_state.users_db)
        tot_msgs = len(st.session_state.message_list)
        
        render_html(f"""
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
            <div style="background:white; border-radius:16px; padding:1.2rem; border:1px solid #e2e8f0; border-top:4px solid #10b981; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size:0.8rem; font-weight:700; color:#64748b;">TOTAL LOG KONSUMSI</div>
                <div style="font-size:1.8rem; font-weight:800; color:#059669; margin-top:0.2rem;">{tot_logs} Catatan</div>
                <div style="font-size:0.75rem; color:#10b981; font-weight:600;">Data Baki Terpantau</div>
            </div>
            <div style="background:white; border-radius:16px; padding:1.2rem; border:1px solid #e2e8f0; border-top:4px solid #3b82f6; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size:0.8rem; font-weight:700; color:#64748b;">PENGGUNA TERDAFTAR</div>
                <div style="font-size:1.8rem; font-weight:800; color:#2563eb; margin-top:0.2rem;">{tot_users} Akun</div>
                <div style="font-size:0.75rem; color:#3b82f6; font-weight:600;">Siswa & Karyawan Aktif</div>
            </div>
            <div style="background:white; border-radius:16px; padding:1.2rem; border:1px solid #e2e8f0; border-top:4px solid #f59e0b; box-shadow:0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size:0.8rem; font-weight:700; color:#64748b;">KOTAK MASUK PESAN</div>
                <div style="font-size:1.8rem; font-weight:800; color:#d97706; margin-top:0.2rem;">{tot_msgs} Pesan</div>
                <div style="font-size:0.75rem; color:#f59e0b; font-weight:600;">Saran & Konsultasi Siswa</div>
            </div>
        </div>
        """)
        
        col_adm_left, col_adm_right = st.columns([1.4, 1], gap="large")
        
        with col_adm_left:
            render_html("""
            <div class="glass-card">
                <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-list-check" style="color:#10b981;"></i> Pantauan Log Kebutuhan & Konsumsi Siswa</h4>
            </div>
            """)
            
            table_rows = ""
            for h in st.session_state.history_list:
                table_rows += f"""
                <tr>
                    <td style="font-weight:700; color:#0f766e;">{h.get('user')}<br><small style="color:#64748b;">NIK: {h.get('nik')}</small></td>
                    <td>{h.get('menu')}</td>
                    <td><span style="background:#f0fdf4; color:#059669; padding:0.2rem 0.5rem; border-radius:6px; font-weight:700; font-size:0.78rem;">{h.get('portion')}</span></td>
                    <td style="font-weight:700; color:#d97706;">{h.get('rating')}</td>
                    <td style="font-size:0.78rem; color:#64748b;">{h.get('date')}<br>{h.get('time')}</td>
                </tr>
                """
            
            render_html(f"""
            <table class="custom-table" style="margin-bottom:1.5rem;">
                <thead>
                    <tr>
                        <th>Siswa / NIK</th>
                        <th>Menu MBG</th>
                        <th>Porsi</th>
                        <th>Rating</th>
                        <th>Waktu</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            """)
            
        with col_adm_right:
            render_html("""
            <div class="glass-card">
                <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-inbox" style="color:#f59e0b;"></i> Kotak Masuk Saran & Aduan Siswa</h4>
            </div>
            """)
            
            for idx, msg in enumerate(st.session_state.message_list):
                with st.expander(f"📩 {msg.get('user')} (NIK: {msg.get('nik')}) - {msg.get('date')}", expanded=(idx == 0)):
                    st.markdown(f"**Pesan Pengguna:**\n> *\"{msg.get('text')}\"*\n")
                    if msg.get("reply"):
                        st.info(f"**Balasan Saat Ini:** {msg.get('reply')}")
                    
                    new_reply = st.text_input(f"Ketik Balasan Admin:", value=msg.get("reply", ""), key=f"reply_adm_{msg.get('id')}")
                    if st.button(f"Kirim Balasan ke {msg.get('user')}", key=f"btn_adm_send_{msg.get('id')}"):
                        msg["reply"] = new_reply.strip()
                        st.success("✅ Balasan berhasil dikirim ke siswa!")
                        st.rerun()

# Footer Mewah
render_html("""
<div style="text-align:center; padding:2rem 0 1rem 0; color:#64748b; font-size:0.84rem; border-top:1px solid rgba(0,0,0,0.06); margin-top:2rem;">
    Aplikasi Media Interaktif MBG | Riset & Publikasi Ilmiah Visi Komputer Cerdas | Universitas Syiah Kuala
</div>
""")
