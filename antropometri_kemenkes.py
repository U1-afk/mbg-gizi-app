# -*- coding: utf-8 -*-
"""
Modul Antropometri Standar Kemenkes RI (Permenkes No. 2 Tahun 2020) & WHO 2007
Tabel 15: Standar IMT/U Anak Laki-Laki 5-18 Tahun
Tabel 16: Standar IMT/U Anak Perempuan 5-18 Tahun
"""

# Basis titik referensi per tahun (bulan: [ -3SD, -2SD, -1SD, Median, +1SD, +2SD, +3SD ])
# Tabel 15 (Laki-laki)
REF_BOYS = {
    60:  [12.1, 13.0, 14.1, 15.3, 16.6, 18.3, 20.2],
    72:  [12.1, 13.0, 14.1, 15.3, 16.8, 18.5, 20.7],
    84:  [12.2, 13.1, 14.2, 15.5, 17.0, 19.0, 21.6],
    96:  [12.4, 13.3, 14.4, 15.7, 17.4, 19.7, 22.8],
    108: [12.6, 13.5, 14.6, 16.0, 17.9, 20.5, 24.3],
    120: [12.8, 13.7, 14.9, 16.4, 18.5, 21.4, 26.1],
    132: [13.1, 14.1, 15.3, 16.9, 19.2, 22.5, 28.0],
    144: [13.4, 14.5, 15.8, 17.5, 19.9, 23.6, 30.0],
    156: [13.8, 14.9, 16.4, 18.2, 20.8, 24.8, 31.7],
    168: [14.3, 15.5, 17.0, 19.0, 21.8, 25.9, 33.1],
    180: [14.7, 16.0, 17.6, 19.8, 22.7, 27.0, 34.1],
    192: [15.1, 16.5, 18.2, 20.5, 23.5, 27.9, 34.8],
    204: [15.4, 16.9, 18.8, 21.1, 24.3, 28.6, 35.2],
    216: [15.7, 17.3, 19.2, 21.7, 24.9, 29.2, 35.4],
    228: [15.9, 17.6, 19.6, 22.2, 25.4, 29.7, 35.5]
}

# Tabel 16 (Perempuan)
REF_GIRLS = {
    60:  [11.8, 12.7, 13.9, 15.2, 16.9, 18.9, 21.3],
    72:  [11.7, 12.7, 13.9, 15.3, 17.0, 19.2, 22.1],
    84:  [11.8, 12.7, 13.9, 15.4, 17.3, 19.8, 23.3],
    96:  [11.9, 12.9, 14.1, 15.7, 17.7, 20.6, 24.8],
    108: [12.1, 13.1, 14.4, 16.1, 18.3, 21.5, 26.5],
    120: [12.4, 13.5, 14.8, 16.6, 19.0, 22.6, 28.4],
    132: [12.7, 13.9, 15.3, 17.2, 19.9, 23.7, 30.2],
    144: [13.2, 14.4, 16.0, 18.0, 20.8, 25.0, 31.9],
    156: [13.6, 14.9, 16.6, 18.8, 21.8, 26.2, 33.4],
    168: [14.0, 15.4, 17.2, 19.6, 22.7, 27.3, 34.7],
    180: [14.4, 15.9, 17.8, 20.2, 23.5, 28.2, 35.5],
    192: [14.6, 16.2, 18.2, 20.7, 24.1, 28.9, 36.1],
    204: [14.7, 16.4, 18.4, 21.0, 24.5, 29.3, 36.3],
    216: [14.7, 16.4, 18.6, 21.3, 24.8, 29.5, 36.3],
    228: [14.7, 16.5, 18.7, 21.4, 25.0, 29.7, 36.2]
}

def get_permenkes_reference_row(usia_bulan, jk_code):
    """
    Mengambil baris nilai referensi [ -3SD, -2SD, -1SD, Median, +1SD, +2SD, +3SD ]
    dengan interpolasi linier presisi bulan per bulan.
    jk_code: 0 untuk Laki-laki, 1 untuk Perempuan.
    """
    ref_dict = REF_BOYS if jk_code == 0 else REF_GIRLS
    u = max(60, min(228, int(usia_bulan)))
    
    # Cari titik bawah dan titik atas
    keys = sorted(ref_dict.keys())
    if u in ref_dict:
        return ref_dict[u]
    
    k_low = keys[0]
    k_high = keys[-1]
    for i in range(len(keys) - 1):
        if keys[i] <= u <= keys[i+1]:
            k_low = keys[i]
            k_high = keys[i+1]
            break
            
    frac = (u - k_low) / float(k_high - k_low)
    v_low = ref_dict[k_low]
    v_high = ref_dict[k_high]
    
    interpolated = [round(v_low[j] + frac * (v_high[j] - v_low[j]), 2) for j in range(7)]
    return interpolated

def evaluate_status_permenkes(usia_bulan, jk_code, imt):
    """
    Mengevaluasi Status Gizi & Z-Score berdasarkan Permenkes No. 2 Tahun 2020 Pasal 4 ayat (6):
    a. Gizi Buruk (Severely Thinness): < -3 SD
    b. Gizi Kurang (Thinness): -3 SD s.d. < -2 SD
    c. Gizi Baik (Normal / Ideal): -2 SD s.d. +1 SD
    d. Gizi Lebih (Overweight): +1 SD s.d. +2 SD
    e. Obesitas (Obese): > +2 SD
    """
    row = get_permenkes_reference_row(usia_bulan, jk_code)
    sd_m3, sd_m2, sd_m1, median, sd_p1, sd_p2, sd_p3 = row
    
    # Hitung Z-Score aproksimasi piecewise linear standar Kemenkes/WHO
    if imt < sd_m3:
        zscore = -3.0 - ((sd_m3 - imt) / (sd_m2 - sd_m3 if sd_m2 != sd_m3 else 1.0))
        label = "Gizi Buruk"
        desc = "Indeks Massa Tubuh berada di bawah ambang batas sangat kurus (< -3 SD). Sangat membutuhkan intervensi gizi terpadu kalori & protein tinggi."
    elif imt < sd_m2:
        zscore = -3.0 + ((imt - sd_m3) / (sd_m2 - sd_m3))
        label = "Gizi Kurang"
        desc = "Berat badan kurang menurut standar umur (-3 SD s.d. < -2 SD). Disarankan menambah porsi karbohidrat dan lauk protein pada baki MBG."
    elif imt <= sd_p1:
        if imt <= median:
            zscore = -2.0 + ((imt - sd_m2) / (median - sd_m2)) * 2.0
        else:
            zscore = 0.0 + ((imt - median) / (sd_p1 - median)) * 1.0
        label = "Normal (Ideal)"
        desc = "Status gizi baik dan seimbang (-2 SD s.d. +1 SD). Pertahankan pemenuhan porsi gizi seimbang MBG dan aktivitas fisik aktif."
    elif imt <= sd_p2:
        zscore = 1.0 + ((imt - sd_p1) / (sd_p2 - sd_p1))
        label = "Gizi Lebih (Overweight)"
        desc = "Indeks massa tubuh berada pada ambang batas berlebih (+1 SD s.d. +2 SD). Batasi makanan berlemak tinggi dan perbanyak porsi sayur berserat."
    else:
        zscore = 2.0 + ((imt - sd_p2) / (sd_p3 - sd_p2 if sd_p3 != sd_p2 else 1.0))
        label = "Obesitas"
        desc = "Indeks massa tubuh tinggi melampaui ambang batas (> +2 SD). Disarankan konsultasi pola makan teratur dan tingkatkan olahraga."
        
    return {
        "zscore": round(zscore, 2),
        "label": label,
        "desc": desc,
        "thresholds": {
            "minus_3sd": sd_m3,
            "minus_2sd": sd_m2,
            "minus_1sd": sd_m1,
            "median": median,
            "plus_1sd": sd_p1,
            "plus_2sd": sd_p2,
            "plus_3sd": sd_p3
        }
    }

# Quick test
if __name__ == "__main__":
    test_cases = [
        (144, 0, 17.5, "Laki-laki 12 Thn, IMT 17.5"),
        (120, 1, 26.5, "Perempuan 10 Thn, IMT 26.5"),
        (156, 1, 12.5, "Perempuan 13 Thn, IMT 12.5"),
        (84, 0, 13.5, "Laki-laki 7 Thn, IMT 13.5")
    ]
    for u, jk, imt, note in test_cases:
        res = evaluate_status_permenkes(u, jk, imt)
        print(f"{note} -> Label: {res['label']} (Z-Score: {res['zscore']} SD)")
        print(f"   Ambang Batas: -2SD={res['thresholds']['minus_2sd']}, Med={res['thresholds']['median']}, +1SD={res['thresholds']['plus_1sd']}, +2SD={res['thresholds']['plus_2sd']}")
