import streamlit as st
import calendar
from datetime import date

# Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Sistem Penjadwalan Kerja")

# --- CSS STABLE UNTUK TAMPILAN & PRINT ---
st.markdown("""
<style>
    /* Font Global */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Sembunyikan elemen Streamlit saat print */
    @media print {
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .print-container { width: 100% !important; margin: 0 !important; }
        table { font-size: 10pt !important; width: 100% !important; border-collapse: collapse !important; }
        th, td { border: 1px solid #000 !important; padding: 4px !important; }
        .s-off { background-color: #ffcccc !important; color: red !important; }
        .s-pagi { background-color: #d1f7d1 !important; }
        .s-mid { background-color: #fff4cc !important; }
        .s-full { background-color: #d1e9ff !important; }
    }

    /* UI Desktop */
    .table-wrapper {
        background: white;
        padding: 20px;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-top: 10px;
    }

    .roster-table {
        width: 100%;
        border-collapse: collapse;
        color: #1e293b;
    }

    .roster-table th {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 10px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
    }

    .roster-table td {
        border: 1px solid #cbd5e1;
        padding: 8px;
        text-align: center;
        font-size: 13px;
        font-weight: 600;
    }

    /* Warna Shift */
    .s-off { background-color: #fee2e2; color: #b91c1c; }
    .s-pagi { background-color: #f0fdf4; color: #15803d; }
    .s-mid { background-color: #fefce8; color: #a16207; }
    .s-full { background-color: #eff6ff; color: #1d4ed8; }

    /* Tombol Cetak */
    .print-btn {
        background-color: #2563eb;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
        margin-bottom: 20px;
    }
    .print-btn:hover { background-color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR (LOGIC CONTROL) ===
with st.sidebar:
    st.title("📋 Setting Jadwal")
    thn = st.number_input("Tahun", value=2026)
    bln = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_mid = st.text_input("Label Shift Siang", "MIDDLE")
    rotasi_hari = st.slider("Rotasi Tiap (Hari)", 1, 5, 2)
    
    st.subheader("👥 Tim Tandem")
    tandem_txt = st.text_area("Nama1,Nama2", "SUBAWA,RAKA\nPRIMA,BELLA")
    
    st.subheader("👤 Tim Single")
    single_txt = st.text_area("Nama", "WIRA\nDERY")
    
    st.subheader("🏖️ Libur Rutin")
    libur_txt = st.text_area("Nama,Hari", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === ENGINE LOGIC (DIPERTAHANKAN) ===
def hitung_jadwal():
    t_list = [x.split(',') for x in tandem_txt.split('\n') if ',' in x]
    s_list = [x.strip().upper() for x in single_txt.split('\n') if x.strip()]
    l_map = {x.split(',')[0].strip().upper(): x.split(',')[1].strip().upper() for x in libur_txt.split('\n') if ',' in x}
    
    semua_staf = []
    for t in t_list: semua_staf.extend([t[0].strip().upper(), t[1].strip().upper()])
    semua_staf.extend(s_list)
    
    _, hari_maks = calendar.monthrange(thn, bln)
    h_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    res = {e: {} for e in semua_staf}

    # Logika Tandem
    for t in t_list:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        current_s1 = "PAGI"
        cnt = 0
        for d in range(1, hari_maks + 1):
            dt = date(thn, bln, d)
            hr = h_indo[dt.weekday()]
            
            if l_map.get(e1) == hr: res[e1][d], res[e2][d], cnt = "OFF", "MID/FULL", 0
            elif l_map.get(e2) == hr: res[e2][d], res[e1][d], cnt = "OFF", "MID/FULL", 0
            else:
                if cnt >= rotasi_hari:
                    current_s1 = label_mid if current_s1 == "PAGI" else "PAGI"
                    cnt = 0
                res[e1][d] = current_s1
                res[e2][d] = "PAGI" if current_s1 == label_mid else label_mid
                cnt += 1

    # Logika Single (H-1 Pagi, H+1 Siang)
    for s in s_list:
        for d in range(1, hari_maks + 1):
            dt = date(thn, bln, d)
            if l_map.get(s) == h_indo[dt.weekday()]: res[s][d] = "OFF"
            
        for d in range(1, hari_maks + 1):
            if res[s].get(d) == "OFF":
                if d > 1: res[s][d-1] = "PAGI"
                if d < hari_maks: res[s][d+1] = label_mid
            elif not res[s].get(d):
                res[s][d] = "PAGI"
                
    return res, semua_staf, hari_maks, h_indo

# === TAMPILAN UTAMA ===
st.title("Jadwal Kerja Otomatis")

if st.sidebar.button("GENERATE JADWAL", type="primary"):
    data_final, staf_final, maks_d, h_nama_list = hitung_jadwal()
    
    # Tombol Cetak (HTML Button + Script)
    st.markdown("""
        <div class="no-print">
            <button class="print-btn" onclick="window.print()">🖨️ CETAK KE PDF (A4)</button>
        </div>
    """, unsafe_allow_html=True)

    # Membangun Tabel
    html_output = f"""
    <div class="print-container">
        <center>
            <h2 style="margin-bottom:0;">JADWAL KERJA KARYAWAN</h2>
            <h3 style="margin-top:5px; text-transform:uppercase;">BULAN {calendar.month_name[bln]} {thn}</h3>
        </center>
        <div class="table-wrapper">
            <table class="roster-table">
                <thead>
                    <tr>
                        <th rowspan="2">HARI</th>
                        <th rowspan="2">TGL</th>
                        <th colspan="{len(staf_final)}">NAMA KARYAWAN</th>
                        <th rowspan="2">W</th>
                    </tr>
                    <tr>
                        {"".join([f"<th>{n}</th>" for n in staf_final])}
                    </tr>
                </thead>
                <tbody>
    """

    for d in range(1, maks_d + 1):
        dt = date(thn, bln, d)
        h_str = h_nama_list[dt.weekday()]
        
        # Highlight Baris Weekend
        row_bg = "style='background-color:#f1f5f9;'" if h_str in ["SABTU", "MINGGU"] else ""
        
        html_output += f"<tr {row_bg}><td>{h_str}</td><td>{d}</td>"
        
        for s in staf_final:
            val = data_final[s][d]
            cls = ""
            if val == "OFF": cls = "s-off"
            elif val == "PAGI": cls = "s-pagi"
            elif val == "MID/FULL": cls = "s-full"
            else: cls = "s-mid"
            
            html_output += f"<td class='{cls}'>{val}</td>"
        
        # Logika Gabung Minggu (W)
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (maks_d - d) + 1)
            # Hitung minggu ke berapa
            first_day_val = date(thn, bln, 1).isocalendar()[1]
            week_no = dt.isocalendar()[1] - first_day_val + 1
            html_output += f"<td rowspan='{span}' style='background:#fff; color:#94a3b8;'>{week_no}</td>"
            
        html_output += "</tr>"

    html_output += "</tbody></table></div></div>"
    st.markdown(html_output, unsafe_allow_html=True)
else:
    st.info("Atur parameter di sidebar lalu klik tombol Generate.")
