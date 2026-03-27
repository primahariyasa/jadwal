import streamlit as st
import pandas as pd
import calendar
from datetime import date

# Konfigurasi halaman
st.set_page_config(layout="wide", page_title="Roster Pro | Designer Edition")

# --- UI PREMIUM: GOOGLE FONTS & TAILWIND CUSTOM ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>

<style>
    /* Global Styles */
    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif !important;
    }

    /* CSS Khusus Cetak (A4 Landscape) */
    @media print {
        @page { size: A4 landscape; margin: 10mm; }
        /* Sembunyikan SEMUA elemen Streamlit saat cetak */
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .print-container { width: 100% !important; zoom: 90%; }
        table { border: 2px solid #000 !important; }
        th, td { border: 1px solid #000 !important; -webkit-print-color-adjust: exact; }
    }

    /* Tampilan Tabel Modern */
    .table-container {
        background: white;
        border-radius: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        padding: 20px;
    }
    
    .roster-table { width: 100%; border-collapse: collapse; }
    .roster-table th { 
        background-color: #1e293b; color: white; 
        padding: 12px 8px; text-transform: uppercase; font-size: 13px; letter-spacing: 0.05em;
    }
    .roster-table td { 
        padding: 10px 6px; text-align: center; font-size: 14px; font-weight: 600; 
        border: 1px solid #e2e8f0;
    }

    /* Palette Warna Shift Creative */
    .s-off { background-color: #fee2e2 !important; color: #991b1b !important; border-left: 4px solid #ef4444 !important; }
    .s-pagi { background-color: #f0fdf4 !important; color: #166534 !important; }
    .s-mid { background-color: #fefce8 !important; color: #854d0e !important; }
    .s-full { background-color: #eff6ff !important; color: #1e40af !important; border: 1.5px dashed #3b82f6 !important; }
    
    /* Tombol Print Custom */
    .btn-print {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; padding: 12px 24px; border-radius: 8px; font-weight: bold;
        cursor: pointer; transition: all 0.3s; border: none; display: inline-flex; align-items: center; gap: 8px;
    }
    .btn-print:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4); }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR CONTROL ===
with st.sidebar:
    st.markdown("<h1 class='text-2xl font-extrabold text-indigo-600 mb-6'>ROSTER PRO <span class='text-xs font-light text-gray-400'>v4.0</span></h1>", unsafe_allow_html=True)
    
    with st.expander("📅 Periode & General", expanded=True):
        col_y, col_m = st.columns(2)
        tahun = col_y.number_input("Tahun", value=2026)
        bulan_idx = col_m.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
        label_siang = st.text_input("Nama Shift Siang", "MIDDLE")
        rotasi = st.select_slider("Durasi Blok Shift", options=[1, 2, 3, 4], value=2)

    with st.expander("👥 Tim & Pasangan"):
        tandem_in = st.text_area("Tandem (A,B)", "SUBAWA,RAKA\nPRIMA,BELLA")
        single_in = st.text_area("Single (Nama saja)", "WIRA\nDERY")
        
    with st.expander("🏖️ Libur Rutin"):
        libur_in = st.text_area("Nama,Hari", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === LOGIKA ENGINE (PENGOLAHAN DATA) ===
def build_roster():
    tandems = [t.split(',') for t in tandem_in.split('\n') if ',' in t]
    singles = [s.strip().upper() for s in single_in.split('\n') if s.strip()]
    libur_map = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_in.split('\n') if ',' in l}
    
    karyawan = []
    for t in tandems: karyawan.extend([t[0].strip().upper(), t[1].strip().upper()])
    karyawan.extend(singles)
    
    _, jml_hari = calendar.monthrange(tahun, bulan_idx)
    hari_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    res = {emp: {} for emp in karyawan}

    # 1. Tandem Logic
    for t in tandems:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        state_e1 = "PAGI"
        day_cnt = 0
        
        for d in range(1, jml_hari + 1):
            dt = date(tahun, bulan_idx, d)
            h = hari_indo[dt.weekday()]
            
            # Aturan Libur & Partner Cover
            if libur_map.get(e1) == h: 
                res[e1][d], res[e2][d], day_cnt = "OFF", "MID/FULL", 0
            elif libur_map.get(e2) == h: 
                res[e2][d], res[e1][d], day_cnt = "OFF", "MID/FULL", 0
            else:
                # Logika H-1 / H+1 (Sederhana dalam blok)
                if day_cnt >= rotasi:
                    state_e1 = label_siang if state_e1 == "PAGI" else "PAGI"
                    day_cnt = 0
                
                res[e1][d] = state_e1
                res[e2][d] = "PAGI" if state_e1 == label_siang else label_siang
                day_cnt += 1

    # 2. Single Logic (H-1 Pagi, H+1 Siang)
    for s in singles:
        for d in range(1, jml_hari + 1):
            dt = date(tahun, bulan_idx, d)
            h = hari_indo[dt.weekday()]
            if libur_map.get(s) == h: res[s][d] = "OFF"
            
        for d in range(1, jml_hari + 1):
            if res[s].get(d) == "OFF":
                if d > 1: res[s][d-1] = "PAGI"
                if d < jml_hari: res[s][d+1] = label_siang
            elif not res[s].get(d):
                res[s][d] = "PAGI"

    return res, karyawan, jml_hari, hari_indo

# === MAIN VIEW ===
st.markdown("<div class='no-print'><h2 class='text-3xl font-bold text-gray-800'>Pratinjau Jadwal Kerja</h2><p class='text-gray-500 mb-6'>Atur parameter di sidebar dan cetak hasilnya dengan rapi.</p></div>", unsafe_allow_html=True)

if st.sidebar.button("✨ GENERATE JADWAL", use_container_width=True):
    data, emps, max_d, h_list = build_roster()
    
    # Tombol Cetak dengan JS
    st.markdown("""
        <div class='no-print mb-8'>
            <button class='btn-print' onclick='window.print()'>
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
                CETAK JADWAL KE PDF / PRINTER
            </button>
        </div>
    """, unsafe_allow_html=True)

    # Membangun Tabel HTML
    html_table = f"""
    <div class="print-container">
        <div class="text-center mb-6">
            <h1 class="text-3xl font-extrabold tracking-tight">JADWAL KERJA OFFICE</h1>
            <p class="text-xl text-gray-600 font-medium uppercase">{calendar.month_name[bulan_idx]} {tahun}</p>
        </div>
        <div class="table-container">
            <table class="roster-table">
                <thead>
                    <tr>
                        <th rowspan="2">HARI</th>
                        <th rowspan="2">TGL</th>
                        <th colspan="{len(emps)}">NAMA KARYAWAN</th>
                        <th rowspan="2">W</th>
                    </tr>
                    <tr>
                        {" ".join([f"<th>{n}</th>" for n in emps])}
                    </tr>
                </thead>
                <tbody>
    """

    for d in range(1, max_d + 1):
        dt = date(tahun, bulan_idx, d)
        h_nama = h_list[dt.weekday()]
        
        # Style khusus weekend
        row_cls = "bg-slate-50" if h_nama in ["SABTU", "MINGGU"] else ""
        
        html_table += f"<tr class='{row_cls}'><td>{h_nama}</td><td>{d}</td>"
        
        for e in emps:
            shift = data[e][d]
            c_cls = ""
            if shift == "OFF": c_cls = "s-off"
            elif shift == "PAGI": c_cls = "s-pagi"
            elif shift == "MID/FULL": c_cls = "s-full"
            else: c_cls = "s-mid"
            
            html_table += f"<td class='{c_cls}'>{shift}</td>"
        
        # Kolom Minggu Ke (Merged)
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (max_d - d) + 1)
            w_no = dt.isocalendar()[1] - date(tahun, bulan_idx, 1).isocalendar()[1] + 1
            html_table += f"<td rowspan='{span}' class='bg-gray-100 text-gray-400 text-xs'>{w_no}</td>"
            
        html_table += "</tr>"

    html_table += "</tbody></table></div></div>"
    st.markdown(html_table, unsafe_allow_html=True)

else:
    st.markdown("""
        <div class='flex flex-col items-center justify-center py-20 border-2 border-dashed border-gray-200 rounded-3xl'>
            <p class='text-gray-400 text-lg'>Klik tombol <b>Generate</b> untuk melihat keajaiban ✨</p>
        </div>
    """, unsafe_allow_html=True)
