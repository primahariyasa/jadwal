import streamlit as st
import calendar
from datetime import date

# Konfigurasi halaman agar lebar maksimal
st.set_page_config(layout="wide", page_title="Jadwal Kerja Divisi")

# --- CSS SEDERHANA & AMPUH ---
st.markdown("""
<style>
    /* Mengatur agar konten Streamlit memenuhi layar & rata tengah */
    .main .block-container {
        padding-top: 2rem;
        max-width: 95%;
    }
    
    /* CSS Tabel untuk Tampilan Layar & Cetak */
    .center-content {
        text-align: center;
        width: 100%;
    }
    
    .roster-table {
        margin: 0 auto;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        width: 100%;
        border: 2px solid black;
    }
    
    .roster-table th {
        background-color: #333;
        color: white;
        border: 1px solid black;
        padding: 8px 4px;
        font-size: 12px;
    }
    
    .roster-table td {
        border: 1px solid black;
        padding: 6px 2px;
        text-align: center;
        font-size: 13px;
        font-weight: bold;
    }

    /* Warna Shift Standar */
    .bg-off { background-color: #FF0000 !important; color: white !important; }
    .bg-pagi { background-color: #92D050 !important; color: black !important; }
    .bg-siang { background-color: #FFFF00 !important; color: black !important; }
    .bg-full { background-color: #0070C0 !important; color: white !important; }

    /* Tombol Cetak yang "Beneran" Berfungsi */
    .btn-print {
        background-color: #28a745;
        color: white;
        padding: 15px 30px;
        border: none;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        margin-bottom: 20px;
    }

    @media print {
        /* Sembunyikan semua UI Streamlit saat cetak */
        [data-testid="stSidebar"], [data-testid="stHeader"], .no-print, header, footer {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .roster-table { width: 100% !important; }
        .roster-table td, .roster-table th { -webkit-print-color-adjust: exact; }
        body { background-color: white !important; }
    }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR INPUT ===
with st.sidebar:
    st.title("⚙️ Pengaturan")
    divisi_name = st.text_input("Nama Divisi", "OPERASIONAL")
    thn = st.number_input("Tahun", value=2026)
    bln = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_siang = st.text_input("Label Shift Siang", "MIDDLE")
    hari_rotasi = st.slider("Ganti Shift Setiap (Hari)", 1, 7, 2)
    
    st.divider()
    tandem_input = st.text_area("Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_input = st.text_area("Single (Nama)", "WIRA\nDERY")
    libur_input = st.text_area("Libur Rutin (Nama,Hari)", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === LOGIKA ROTASI YANG KONSISTEN ===
def generate_data():
    tandem_list = [t.split(',') for t in tandem_input.split('\n') if ',' in t]
    single_list = [s.strip().upper() for s in single_input.split('\n') if s.strip()]
    libur_dict = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_input.split('\n') if ',' in l}
    
    staff_names = []
    for t in tandem_list: staff_names.extend([t[0].strip().upper(), t[1].strip().upper()])
    staff_names.extend(single_list)
    
    _, days_count = calendar.monthrange(thn, bln)
    hari_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    final_roster = {s: {d: "" for d in range(1, days_count + 1)} for s in staff_names}

    # 1. Tentukan Libur & H-1/H+1
    for s in staff_names:
        off_day = libur_dict.get(s)
        for d in range(1, days_count + 1):
            if hari_indo[date(thn, bln, d).weekday()] == off_day:
                final_roster[s][d] = "OFF"
                if d > 1 and final_roster[s][d-1] != "OFF": final_roster[s][d-1] = "PAGI"
                if d < days_count: final_roster[s][d+1] = label_siang

    # 2. Rotasi Tandem
    for t in tandem_list:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        for d in range(1, days_count + 1):
            # Rumus rotasi berdasarkan blok hari
            blok = (d - 1) // hari_rotasi
            s1_default = "PAGI" if blok % 2 == 0 else label_siang
            s2_default = label_siang if blok % 2 == 0 else "PAGI"
            
            if final_roster[e1][d] == "OFF": final_roster[e2][d] = "MID/FULL"
            elif final_roster[e2][d] == "OFF": final_roster[e1][d] = "MID/FULL"
            else:
                if not final_roster[e1][d]: final_roster[e1][d] = s1_default
                if not final_roster[e2][d]: final_roster[e2][d] = s2_default
                
    # 3. Sisa Single
    for s in single_list:
        for d in range(1, days_count + 1):
            if not final_roster[s][d]: final_roster[s][d] = "PAGI"
            
    return final_roster, staff_names, days_count, hari_indo

# === RENDER JADWAL ===
if st.sidebar.button("🚀 GENERATE JADWAL", type="primary"):
    roster, emps, d_max, h_list = generate_data()
    
    # Tombol Print
    st.markdown("""
        <div class="center-content no-print">
            <button class="btn-print" onclick="window.print()">🖨️ CETAK JADWAL KE PDF</button>
        </div>
    """, unsafe_allow_html=True)

    # HTML Table
    html = f"""
    <div class="center-content">
        <h1 style="text-decoration: underline;">JADWAL KERJA DIVISI {divisi_name.upper()}</h1>
        <h2 style="margin-bottom: 20px;">BULAN {calendar.month_name[bln].upper()} {thn}</h2>
        
        <table class="roster-table">
            <thead>
                <tr>
                    <th rowspan="2" style="width: 80px;">HARI</th>
                    <th rowspan="2" style="width: 40px;">TGL</th>
                    <th colspan="{len(emps)}">NAMA KARYAWAN</th>
                    <th rowspan="2" style="width: 40px;">W</th>
                </tr>
                <tr>
                    {" ".join([f"<th>{n}</th>" for n in emps])}
                </tr>
            </thead>
            <tbody>
    """

    for d in range(1, d_max + 1):
        dt = date(thn, bln, d)
        h_str = h_list[dt.weekday()]
        row_style = "style='background-color:#eee;'" if h_str == "MINGGU" else ""
        
        html += f"<tr {row_style}><td>{h_str}</td><td>{d}</td>"
        
        for e in emps:
            val = roster[e][d]
            cls = "bg-off" if val == "OFF" else "bg-pagi" if val == "PAGI" else "bg-siang" if val == label_siang else "bg-full"
            html += f"<td class='{cls}'>{val}</td>"
        
        # Kolom Minggu (W)
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            w_num = (d + date(thn, bln, 1).weekday() - 1) // 7 + 1
            html += f"<td rowspan='{span}' style='background-color: white; font-weight: normal; color: gray;'>{w_num}</td>"
        
        html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("Atur parameter di sebelah kiri lalu klik Generate.")
