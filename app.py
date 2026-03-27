import streamlit as st
import calendar
from datetime import date

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide", page_title="Sistem Jadwal Kerja Divisi")

# --- CSS MURNI (TANPA FRAMEWORK) UNTUK STABILITAS TAMPILAN & CETAK ---
st.markdown("""
<style>
    /* Font & Reset */
    * { font-family: 'Segoe UI', Arial, sans-serif; }
    
    /* Tombol Cetak Visual */
    .print-btn-container {
        margin: 20px 0;
        no-print;
    }
    .my-print-button {
        background-color: #047857;
        color: white;
        padding: 12px 25px;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
        font-size: 16px;
    }
    .my-print-button:hover { background-color: #065f46; }

    /* Tabel Jadwal */
    .roster-table {
        width: 100%;
        border-collapse: collapse;
        border: 2px solid #000;
        background-color: white;
    }
    .roster-table th {
        background-color: #1e293b;
        color: white;
        border: 1px solid #000;
        padding: 10px 5px;
        font-size: 12px;
        text-transform: uppercase;
    }
    .roster-table td {
        border: 1px solid #000;
        padding: 8px 4px;
        text-align: center;
        font-size: 13px;
        font-weight: bold;
    }

    /* Warna Shift sesuai instruksi */
    .off { background-color: #ff0000 !important; color: white !important; }
    .pagi { background-color: #92d050 !important; color: black !important; }
    .siang { background-color: #ffff00 !important; color: black !important; }
    .midfull { background-color: #0070c0 !important; color: white !important; }

    /* Pengaturan Print A4 Landscape */
    @media print {
        @page { size: A4 landscape; margin: 1cm; }
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], header, footer {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .roster-table { width: 100% !important; border: 2px solid #000 !important; }
        .roster-table td, .roster-table th { border: 1px solid #000 !important; -webkit-print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR INPUT ===
with st.sidebar:
    st.header("⚙️ Pengaturan")
    divisi = st.text_input("Nama Divisi", "OPERASIONAL")
    tahun = st.number_input("Tahun", value=2026)
    bulan = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_siang = st.text_input("Label Shift Siang", "MIDDLE")
    rotasi_hari = st.slider("Rotasi setiap berapa hari?", 1, 5, 2)
    
    st.divider()
    tandem_txt = st.text_area("Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_txt = st.text_area("Single (Nama)", "WIRA\nDERY")
    libur_txt = st.text_area("Libur Rutin (Nama,Hari)", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === ENGINE LOGIC (PERBAIKAN ROTASI & H-1/H+1) ===
def build_data():
    tandem_pairs = [t.split(',') for t in tandem_txt.split('\n') if ',' in t]
    single_list = [s.strip().upper() for s in single_txt.split('\n') if s.strip()]
    libur_map = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_txt.split('\n') if ',' in l}
    
    all_staff = []
    for t in tandem_pairs: all_staff.extend([t[0].strip().upper(), t[1].strip().upper()])
    all_staff.extend(single_list)
    
    _, days_in_month = calendar.monthrange(tahun, bulan)
    h_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    # 1. Inisialisasi Matrix Kosong
    sched = {e: {d: None for d in range(1, days_in_month + 1)} for e in all_staff}

    # 2. Plot Libur (OFF) & Aturan H-1 / H+1 (WAJIB)
    for e in all_staff:
        day_off_name = libur_map.get(e)
        for d in range(1, days_in_month + 1):
            if h_indo[date(tahun, bulan, d).weekday()] == day_off_name:
                sched[e][d] = "OFF"
    
    # Berikan aturan H-1 dan H+1 secara menyeluruh sebelum rotasi
    for e in all_staff:
        for d in range(1, days_in_month + 1):
            if sched[e][d] == "OFF":
                if d > 1 and sched[e][d-1] != "OFF": sched[e][d-1] = "PAGI"
                if d < days_in_month and sched[e][d+1] != "OFF": sched[e][d+1] = label_siang

    # 3. Plot Rotasi Tandem (Saling Selang-Seling)
    for t in tandem_pairs:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        
        for d in range(1, days_in_month + 1):
            # Penentuan Shift Default berdasarkan Matematika Rotasi (0 atau 1)
            # Ini memastikan shift berganti setiap 'rotasi_hari'
            phase = (d - 1) // rotasi_hari % 2
            def_s1 = "PAGI" if phase == 0 else label_siang
            def_s2 = label_siang if phase == 0 else "PAGI"

            # Cek Kondisi
            s1, s2 = sched[e1][d], sched[e2][d]

            if s1 == "OFF": sched[e2][d] = "MID/FULL"
            elif s2 == "OFF": sched[e1][d] = "MID/FULL"
            else:
                # Jika tidak ada yang libur, cek apakah ada yang sudah kena aturan H-1/H+1
                if s1 and not s2:
                    sched[e2][d] = label_siang if s1 == "PAGI" else "PAGI"
                elif s2 and not s1:
                    sched[e1][d] = label_siang if s2 == "PAGI" else "PAGI"
                elif not s1 and not s2:
                    # Keduanya kosong, gunakan default rotasi
                    sched[e1][d] = def_s1
                    sched[e2][d] = def_s2
    
    # 4. Plot Sisa untuk Single
    for s in single_list:
        for d in range(1, days_in_month + 1):
            if not sched[s][d]:
                sched[s][d] = "PAGI"
                
    return sched, all_staff, days_in_month, h_indo

# === TAMPILAN UTAMA ===
st.markdown(f"<div class='no-print'><h2>Jadwal Kerja Divisi {divisi}</h2></div>", unsafe_allow_html=True)

if st.sidebar.button("🚀 GENERATE JADWAL", type="primary"):
    data, emps, d_max, h_names = build_data()
    
    # Tombol Cetak (HTML Button + Script)
    st.markdown("""
        <div class="no-print" style="margin-bottom:20px;">
            <button class="my-print-button" onclick="window.print()">🖨️ CETAK JADWAL KE PDF (A4)</button>
        </div>
    """, unsafe_allow_html=True)

    # Membangun Output HTML
    html_output = f"""
    <div class="print-area">
        <center>
            <h1 style="margin-bottom:0px; font-size: 24px;">JADWAL KERJA DIVISI {divisi.upper()}</h1>
            <h2 style="margin-top:5px; font-size: 18px;">BULAN {calendar.month_name[bulan].upper()} {tahun}</h2>
        </center>
        <table class="roster-table">
            <thead>
                <tr>
                    <th style="width: 80px;">HARI</th>
                    <th style="width: 35px;">TGL</th>
                    {" ".join([f"<th>{n}</th>" for n in emps])}
                    <th style="width: 30px;">W</th>
                </tr>
            </thead>
            <tbody>
    """

    for d in range(1, d_max + 1):
        dt = date(tahun, bulan, d)
        h_txt = h_names[dt.weekday()]
        
        # Row style untuk hari Minggu agar jelas
        row_bg = "style='background-color:#f2f2f2;'" if h_txt == "MINGGU" else ""
        
        html_output += f"<tr {row_bg}><td>{h_txt}</td><td>{d}</td>"
        
        for e in emps:
            shift = data[e][d]
            cls = ""
            if shift == "OFF": cls = "off"
            elif shift == "PAGI": cls = "pagi"
            elif shift == label_siang: cls = "siang"
            elif shift == "MID/FULL": cls = "midfull"
            
            html_output += f"<td class='{cls}'>{shift}</td>"
        
        # Kolom Minggu (W) Merged
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            # Hitung nomor minggu dalam bulan
            w_idx = (d + date(tahun, bulan, 1).weekday() - 1) // 7 + 1
            html_output += f"<td rowspan='{span}' style='background-color: white; font-size: 16px; color: #999;'>{w_idx}</td>"
            
        html_output += "</tr>"

    html_output += "</tbody></table></div>"
    st.markdown(html_output, unsafe_allow_html=True)

else:
    st.info("Silakan isi data di samping dan klik tombol Generate.")
