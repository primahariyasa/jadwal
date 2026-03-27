import streamlit as st
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Cetak Jadwal Divisi")

# --- CSS MURNI: COMPACT & CENTERED ---
st.markdown("""
<style>
    /* Reset & Font */
    body { background-color: white; }
    .report-container { 
        max-width: 1200px; 
        margin: 0 auto; 
        padding: 10px;
        text-align: center; 
    }
    
    /* Judul Rata Tengah */
    .title-block { margin-bottom: 20px; }
    .title-block h1 { margin: 0; font-size: 22px; text-decoration: underline; }
    .title-block h2 { margin: 5px 0; font-size: 16px; color: #444; }

    /* Tabel Ramping (Compact) */
    .roster-table { 
        width: 100%; 
        border-collapse: collapse; 
        border: 2px solid black; 
        margin: 0 auto;
        table-layout: auto;
    }
    .roster-table th { 
        background-color: #f2f2f2; 
        border: 1px solid black; 
        padding: 5px 2px; 
        font-size: 11px; 
        text-transform: uppercase;
    }
    .roster-table td { 
        border: 1px solid black; 
        padding: 4px 2px; 
        font-size: 12px; 
        font-weight: bold; 
        text-align: center;
    }

    /* Warna Shift (Sesuai Gambar) */
    .off { background-color: #FF0000 !important; color: white !important; }
    .pagi { background-color: #92D050 !important; color: black !important; }
    .mid { background-color: #FFFF00 !important; color: black !important; }
    .full { background-color: #0070C0 !important; color: white !important; }

    /* Tombol Cetak Custom */
    .no-print-zone { margin-bottom: 20px; }
    .btn-cetak {
        background-color: #1a73e8;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        font-weight: bold;
        cursor: pointer;
    }

    /* LOGIKA CETAK A4 LANDSCAPE */
    @media print {
        @page { size: A4 landscape; margin: 10mm; }
        .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], header, footer {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .roster-table { width: 100% !important; }
        .roster-table td, .roster-table th { -webkit-print-color-adjust: exact; }
    }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR INPUT ===
with st.sidebar:
    st.header("📋 Input Data")
    divisi = st.text_input("Nama Divisi", "OPERASIONAL")
    tahun = st.number_input("Tahun", value=2026)
    bulan = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_siang = st.text_input("Label Shift Siang", "MIDDLE")
    rotasi_hari = st.slider("Rotasi Tiap (Hari)", 1, 5, 2)
    
    st.divider()
    tandem_txt = st.text_area("Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_txt = st.text_area("Single (Nama)", "WIRA\nDERY")
    libur_txt = st.text_area("Libur (Nama,Hari)", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === LOGIKA ROTASI (STABLE PHASE) ===
def get_roster():
    pairs = [t.split(',') for t in tandem_txt.split('\n') if ',' in t]
    singles = [s.strip().upper() for s in single_txt.split('\n') if s.strip()]
    liburs = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_txt.split('\n') if ',' in l}
    
    staff = []
    for p in pairs: staff.extend([p[0].strip().upper(), p[1].strip().upper()])
    staff.extend(singles)
    
    _, last_day = calendar.monthrange(tahun, bulan)
    h_names = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    res = {e: {d: None for d in range(1, last_day + 1)} for e in staff}

    # 1. Plot OFF & H-1/H+1 Mandatori
    for e in staff:
        off_day = liburs.get(e)
        for d in range(1, last_day + 1):
            if h_names[date(tahun, bulan, d).weekday()] == off_day:
                res[e][d] = "OFF"
                if d > 1 and res[e].get(d-1) != "OFF": res[e][d-1] = "PAGI"
                if d < last_day: res[e][d+1] = label_siang

    # 2. Plot Tandem Rotation
    for p in pairs:
        e1, e2 = p[0].strip().upper(), p[1].strip().upper()
        for d in range(1, last_day + 1):
            phase = (d - 1) // rotasi_hari % 2
            def_s1 = "PAGI" if phase == 0 else label_siang
            def_s2 = label_siang if phase == 0 else "PAGI"

            if res[e1][d] == "OFF": res[e2][d] = "MID/FULL"
            elif res[e2][d] == "OFF": res[e1][d] = "MID/FULL"
            else:
                # Isi jika masih kosong (belum kena H-1/H+1)
                if not res[e1][d] and not res[e2][d]:
                    res[e1][d], res[e2][d] = def_s1, def_s2
                elif res[e1][d] and not res[e2][d]:
                    res[e2][d] = label_siang if res[e1][d] == "PAGI" else "PAGI"
                elif res[e2][d] and not res[e1][d]:
                    res[e1][d] = label_siang if res[e2][d] == "PAGI" else "PAGI"

    # 3. Plot Single
    for s in singles:
        for d in range(1, last_day + 1):
            if not res[s][d]: res[s][d] = "PAGI"
                
    return res, staff, last_day, h_names

# === RENDER ===
if st.sidebar.button("🔄 GENERATE JADWAL", type="primary"):
    data, names, d_max, h_list = get_roster()
    
    # Area yang akan diprint
    html_body = f"""
    <div class="no-print-zone no-print">
        <button class="btn-cetak" onclick="window.print()">🖨️ CETAK JADWAL (PDF)</button>
    </div>
    
    <div class="report-container">
        <div class="title-block">
            <h1>JADWAL KERJA DIVISI {divisi.upper()}</h1>
            <h2>PERIODE: {calendar.month_name[bulan].upper()} {tahun}</h2>
        </div>
        
        <table class="roster-table">
            <thead>
                <tr>
                    <th style="width:70px;">HARI</th>
                    <th style="width:30px;">TGL</th>
                    {" ".join([f"<th>{n}</th>" for n in names])}
                    <th style="width:25px;">W</th>
                </tr>
            </thead>
            <tbody>
    """

    for d in range(1, d_max + 1):
        dt = date(tahun, bulan, d)
        h_txt = h_list[dt.weekday()]
        row_bg = "style='background-color:#f9f9f9;'" if h_txt == "MINGGU" else ""
        
        html_body += f"<tr {row_bg}><td>{h_txt}</td><td>{d}</td>"
        
        for n in names:
            s = data[n][d]
            cls = "off" if s == "OFF" else "pagi" if s == "PAGI" else "mid" if s == label_siang else "full"
            html_body += f"<td class='{cls}'>{s}</td>"
        
        # Kolom W (Minggu Ke) - Minimalis
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            w_num = (d + date(tahun, bulan, 1).weekday() - 1) // 7 + 1
            html_body += f"<td rowspan='{span}' style='color:#ccc; font-size:10px;'>{w_num}</td>"
        
        html_body += "</tr>"

    html_body += "</tbody></table></div>"
    st.markdown(html_body, unsafe_allow_html=True)
else:
    st.markdown("<center><h3>Silakan klik Generate Jadwal di Sidebar</h3></center>", unsafe_allow_html=True)
