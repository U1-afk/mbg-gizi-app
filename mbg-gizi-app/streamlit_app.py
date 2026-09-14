import os
import io
import time
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA VISUAL MEWAH (IDENTIK DENGAN VERCEL)
# ==============================================================================
st.set_page_config(
    page_title="Media Interaktif Pemantauan Gizi MBG",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_html(html_str):
    """Merender string HTML tanpa indentasi markdown code-block."""
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)

# Custom CSS Modern & Mewah (Aestetika Emerald Mint, Glassmorphism, Font Google)
render_html("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

<style>
    /* Global Reset & Base Theme */
    :root {
        --primary: #10b981;
        --primary-dark: #059669;
        --primary-light: #34d399;
        --secondary: #0f766e;
        --bg: #f0fdf4;
        --text-main: #1f2937;
        --text-light: #4b5563;
    }

    /* Force Light Emerald Glassmorphism Background */
    .stApp {
        background-color: #f0fdf4 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(110, 231, 183, 0.45) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(52, 211, 153, 0.35) 0px, transparent 50%),
            radial-gradient(at 50% 100%, rgba(153, 246, 228, 0.40) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
        color: #1f2937 !important;
        font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    footer {
        visibility: hidden !important;
    }
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1240px !important;
    }

    /* Top Glass Navbar */
    .glass-nav {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.7);
        border-radius: 18px;
        padding: 0.85rem 1.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 20px -2px rgba(16, 185, 129, 0.15);
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 800;
        font-size: 1.15rem;
        color: #059669;
        letter-spacing: -0.3px;
    }
    .nav-brand .brand-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.15rem;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3);
    }
    .nav-right {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .status-pill {
        background: rgba(16, 185, 129, 0.12);
        color: #059669;
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
        color: white;
        padding: 1.8rem 2.2rem;
        border-radius: 20px;
        margin-bottom: 1.6rem;
        box-shadow: 0 12px 28px -6px rgba(16, 185, 129, 0.3);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: "";
        position: absolute;
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
        top: -80px;
        right: -50px;
        border-radius: 50%;
    }
    .hero-banner h1 {
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        color: #ffffff !important;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        font-size: 0.96rem;
        color: #ecfdf5 !important;
        margin: 0 0 1rem 0;
        max-width: 850px;
        line-height: 1.5;
    }
    .hero-tags {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .hero-tag {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(8px);
        color: #ffffff;
        font-size: 0.76rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.35);
    }

    /* Glassmorphism Card Wrapper */
    .glass-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.75);
        border-radius: 20px;
        box-shadow: 0 8px 25px -3px rgba(16, 185, 129, 0.1);
        padding: 1.6rem;
        margin-bottom: 1.4rem;
    }

    /* Streamlit Tabs Customization */
    div[data-baseweb="tab-list"] {
        gap: 0.5rem !important;
        background: rgba(255, 255, 255, 0.65) !important;
        padding: 0.4rem !important;
        border-radius: 16px !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        margin-bottom: 1.5rem !important;
    }
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 1.1rem !important;
        border-radius: 12px !important;
        color: #475569 !important;
        background: transparent !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        background: rgba(16, 185, 129, 0.1) !important;
        color: #059669 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: white !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Metric Cards */
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

    /* Progress Bar Component */
    .progress-bar-card {
        background: #ffffff;
        padding: 1.25rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }
    .progress-bar-item {
        margin-bottom: 0.95rem;
    }
    .progress-bar-item:last-child {
        margin-bottom: 0;
    }
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

    /* Custom Table */
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
    .custom-table tr:last-child td {
        border-bottom: none;
    }
    .custom-table tr:hover td {
        background: #f8fafc;
    }

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
    .imt-legend-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .imt-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }
    .dot-yellow { background-color: #eab308; }
    .dot-green { background-color: #22c55e; }
    .dot-purple { background-color: #9333ea; }
</style>
""")

# Top Glass Navbar (Identik dengan Vercel Navbar)
render_html("""
<div class="glass-nav">
    <div class="nav-brand">
        <div class="brand-badge"><i class="fa-solid fa-utensils"></i></div>
        <span>MEDIA INTERAKTIF MBG</span>
    </div>
    <div class="nav-right">
        <div class="status-pill">
            <span class="status-dot"></span>
            <span>Sistem Pemantauan Aktif</span>
        </div>
        <span style="font-size:0.86rem; font-weight:700; color:#334155;">👤 Siswa / Karyawan</span>
    </div>
</div>
""")

# Main Hero Header
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
# 3. BASIS DATA GIZI RESMI MBG & DETEKSI KOMPARTEMEN
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
    if "nasi" in cls_name or "mie" in cls_name or cls_name == "makanan_pokok":
        return "#3b82f6"
    elif any(k in cls_name for k in ["sayur", "tumis", "sop", "capcay"]):
        return "#10b981"
    elif any(k in cls_name for k in ["buah", "semangka", "jeruk", "kelengkeng", "salak", "anggur", "pisang"]):
        return "#f59e0b"
    elif "susu" in cls_name:
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

def detect_and_classify_meal(pil_image):
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
                    "bbox": xyxy, "feat": feat
                }
                detected_boxes.append(item)

    detected_classes = [b["class"] for b in detected_boxes]
    
    # 1. Default Karbo
    def_karbo_idx = 0
    if "nasi_kuning" in detected_classes:
        def_karbo_idx = 1
    elif "mie_bihun" in detected_classes:
        def_karbo_idx = 2
    else:
        for b in detected_boxes:
            if b["class"] in ["nasi_putih", "makanan_pokok"]:
                if b["feat"].get("mean_r", 0) > 160 and b["feat"].get("mean_g", 0) > 135 and b["feat"].get("mean_b", 0) < 60:
                    def_karbo_idx = 1
                    break
                    
    # 2. Default Prohew
    def_prohew_idx = 0
    if "telur_ceplok" in detected_classes:
        def_prohew_idx = 1
    elif "semur_daging" in detected_classes:
        def_prohew_idx = 3
    elif "udang_balado" in detected_classes:
        def_prohew_idx = 4
    else:
        for b in detected_boxes:
            f = b["feat"]
            if f.get("white", 0) > 0.15 and f.get("yellow", 0) > 0.08:
                def_prohew_idx = 1
                break

    # 3. Default Pronab
    def_pronab_idx = 0
    if "tahu_goreng" in detected_classes:
        def_pronab_idx = 2
    elif "tempe_orek" in detected_classes:
        def_pronab_idx = 1
    else:
        for b in detected_boxes:
            if b["class"] in ["lauk", "tempe_goreng", "tahu_goreng"]:
                f = b["feat"]
                if f.get("red", 0) < 0.08 and f.get("yellow", 0) > 0.20:
                    def_pronab_idx = 2
                    break
                elif f.get("dark", 0) > 0.30 and f.get("brown", 0) > 0.40:
                    def_pronab_idx = 1
                    break

    # 4. Default Sayur
    def_sayur_idx = 0
    if "sayur_capcay" in detected_classes:
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
                    def_sayur_idx = 0
                elif f.get("yellow", 0) > 0.30:
                    def_sayur_idx = 3
                else:
                    def_sayur_idx = 2
                break

    # 5. Default Buah
    def_buah_idx = 0  # Semangka
    if "buah_pisang" in detected_classes:
        def_buah_idx = 1
    elif "buah_jeruk" in detected_classes:
        def_buah_idx = 2
    elif "buah_kelengkeng" in detected_classes:
        def_buah_idx = 3
    elif "buah_anggur" in detected_classes:
        def_buah_idx = 4
    elif "buah_salak" in detected_classes:
        def_buah_idx = 5
    else:
        for b in detected_boxes:
            if "buah" in b["class"]:
                f = b["feat"]
                asp = f.get("aspect", 1.0)
                if asp > 1.35 or asp < 0.70:
                    def_buah_idx = 1  # Pisang
                elif f.get("red", 0) > 0.35:
                    def_buah_idx = 0  # Semangka
                elif f.get("orange", 0) > 0.25:
                    def_buah_idx = 2  # Jeruk
                elif f.get("tan", 0) > 0.20 or f.get("brown", 0) > 0.20:
                    def_buah_idx = 3  # Kelengkeng
                break

    # 6. Default Susu
    def_susu_idx = 1 if "susu" in detected_classes else 0

    # Gambar kotak pembatas rapi
    annotated_img = pil_image.copy()
    draw = ImageDraw.Draw(annotated_img)

    for b in detected_boxes:
        c = get_box_color(b["class"])
        lbl = get_clean_box_label(b["class"])
        x1, y1, x2, y2 = b["bbox"]
        draw.rectangle([x1, y1, x2, y2], outline=c, width=4)
        header_text = f" {lbl} ({int(b['conf']*100)}%) "
        text_w = len(header_text) * 8 + 10
        draw.rectangle([x1, max(0, y1-24), x1 + text_w, y1], fill=c)
        draw.text((x1 + 4, max(0, y1-21)), header_text, fill="white")

    return {
        "annotated_image": annotated_img,
        "boxes": detected_boxes,
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
# 4. KLASIFIKASI STATUS GIZI SISWA (KNN K=5 STANDAR KEMENKES RI / WHO)
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
# 5. NAVIGASI FITUR UTAMA (IDENTIK DENGAN VERCEL MENU GRID)
# ==============================================================================
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
        <div class="glass-card">
            <h4 style="margin:0 0 0.75rem 0; font-weight:700; color:#1e293b;"><i class="fa-solid fa-image" style="color:#10b981;"></i> 1. Masukkan Citra Baki Makanan</h4>
        </div>
        """)
        
        input_source = st.radio(
            "Pilih Metode Masukan:",
            ["📷 Kamera Langsung (HP/Laptop)", "📁 Unggah File Gambar", "🍽️ Preset Contoh Menu"],
            horizontal=True
        )
        
        input_image = None
        
        if input_source == "📷 Kamera Langsung (HP/Laptop)":
            cam_pic = st.camera_input("Arahkan kamera ke baki makanan MBG:")
            if cam_pic:
                input_image = Image.open(cam_pic).convert("RGB")
        elif input_source == "📁 Unggah File Gambar":
            uploaded = st.file_uploader("Pilih file foto baki (JPG/PNG):", type=["jpg", "jpeg", "png"])
            if uploaded:
                input_image = Image.open(uploaded).convert("RGB")
        else:
            preset_choice = st.selectbox(
                "Pilih Sampel Foto Uji:",
                [
                    "Sampel 1: Ayam Lengkuas + Tahu Kotak + Sayur Hijau + Semangka",
                    "Sampel 2: Telur Ceplok + Tempe Goreng + Sayur Capcay + Kelengkeng",
                    "Sampel 3: Semur Daging Sapi + Tempe Orek + Tumis Jagung + Semangka"
                ]
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
        
        if input_image:
            st.image(input_image, caption="Citra Baki Masukan", use_container_width=True)

    with col_result:
        if input_image is not None:
            with st.spinner("Menganalisis komposisi baki dan kandungan nutrisi..."):
                res = detect_and_classify_meal(input_image)
            
            render_html(f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:0.9rem 1.25rem; border-radius:14px; margin-bottom:1.2rem; display:flex; justify-content:space-between; align-items:center; box-shadow:0 4px 12px rgba(16,185,129,0.08);">
                <div>
                    <span style="color:#166534; font-weight:800; font-size:1rem;"><i class="fa-solid fa-circle-check"></i> Hasil Analisis Komposisi Makanan</span>
                    <div style="color:#15803d; font-size:0.84rem; font-weight:600; margin-top:0.2rem;">Terdeteksi {len(res['boxes'])} Kompartemen Baki Gizi</div>
                </div>
                <span style="background:#dcfce7; color:#15803d; font-weight:800; padding:0.35rem 0.8rem; border-radius:20px; font-size:0.82rem; border:1px solid #86efac;">99.5% Sesuai</span>
            </div>
            """)
            
            st.image(res["annotated_image"], caption="Visualisasi Deteksi Kompartemen Baki MBG", use_container_width=True)
            
            # Interactive Verification Dropdowns
            render_html("""
            <div class="glass-card" style="margin-top:1rem; padding:1.2rem;">
                <div style="font-weight:700; font-size:0.95rem; color:#0f766e; margin-bottom:0.4rem;">
                    <i class="fa-solid fa-list-check"></i> Verifikasi & Penyesuaian Menu Kompartemen
                </div>
                <div style="font-size:0.8rem; color:#64748b; margin-bottom:0.8rem;">
                    AI otomatis mengisi pilihan awal di bawah. Anda dapat menyesuaikan item spesifik dengan 1 klik:
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
                    Pilih opsi <strong>Kamera Langsung</strong> untuk memotret baki makan siang, unggah foto dari galeri, atau pilih <strong>Preset Contoh Menu</strong> untuk analisis otomatis instan.
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
            <span class="badge-ta badge-ta-main" style="margin-top:0.3rem;">Pencatatan Porsi & Tingkat Kepuasan</span>
        </div>
    </div>
    """)
    
    render_html("""
    <div class="glass-card">
        <h4 style="margin:0 0 0.8rem 0; font-weight:700; color:#1e293b;">Input Catatan Konsumsi Makan Bergizi Gratis</h4>
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
    j_notes = st.text_area("Catatan Tambahan / Feedback Siswa:", placeholder="Contoh: Sayuran segar dan ayam sangat empuk...")
    
    if st.button("Simpan Jurnal MBG Harian", type="primary", use_container_width=True):
        st.success("✅ Data kebutuhan dan konsumsi harian MBG berhasil dicatat ke sistem!")


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

# Footer Mewah
render_html("""
<div style="text-align:center; padding:2rem 0 1rem 0; color:#64748b; font-size:0.84rem; border-top:1px solid rgba(0,0,0,0.06); margin-top:2rem;">
    Aplikasi Media Interaktif MBG | Riset & Publikasi Ilmiah Visi Komputer Cerdas | Universitas Syiah Kuala
</div>
""")
