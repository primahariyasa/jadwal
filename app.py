import streamlit as st
import pandas as pd
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Cetak Jadwal Kerja")

# --- CSS CUSTOM UNTUK TAMPILAN PERSIS GAMBAR & SIAP CETAK ---
st.markdown("""
<style>
    @media print {
        .stButton, .stSidebar, header { display: none !important; }
        .main .block-container { padding: 0; }
    }
    .print-container { font-family: 'Arial', sans-serif; color: black; }
    .jadwal-table { width: 100%; border-collapse: collapse; border: 2px solid black; }
    .jadwal-table th { border: 1px solid black; padding: 8px; text-align: center; background-color: white; font-weight: bold; text-transform: uppercase; }
    .jadwal-table td { border: 1px solid black; padding: 6px; text-align: center; font-weight: bold; font-size: 14px; }
    
    /* Warna Shift */
    .bg-off { background-color: #FF0000 !important; color: black; }       /* Merah */
    .bg-middle { background-color: #FFFF00 !important; color: black; }    /* Kuning */
    .bg-pagi { background-color: #92D050 !important; color: black; }      /* Hijau Muda */
    .bg-midfull { background-color: #0070C0 !important; color: white; }    /* Biru */
    
    .header-main { background-color: white; font-size: 20px; text-align: center; margin-bottom: 10px; text-decoration: underline; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR PENGATURAN ===
st.sidebar.header("⚙️ Konfigurasi")
tahun = st.sidebar.number_input("Tahun", value=2026)
bulan_idx = st.sidebar.selectbox("Bulan", range(1, 13), index=3) # Default April
blok_hari = st.sidebar.slider("Rotasi Shift (Hari)", 1, 5, 2)

# Input Karyawan Tandem & Single sesuai Gambar
tandem_input = st.sidebar.text_area("Pasangan (Nama1,Nama2)", "Subawa,Raka\nPrima,Bella")
single_input = st.sidebar.text_area("Single (Nama)", "Wira\nDery")
libur_input = st.sidebar.text_area("Libur Rutin (Nama,Hari)", "Subawa,Rabu\nRaka,Jumat\nPrima,Minggu\nBella,Sabtu\nWira,Selasa\nDery,Kamis")

if st.sidebar.button("Generate Jadwal"):
    # Parsing
    tandems = [t.split(',') for t in tandem_input.split('\n') if ',' in t]
    singles = [s.strip() for s in single_input.split('\n') if s.strip()]
    liburs = {l.split(',')[0].strip(): l.split(',')[1].strip() for l in libur_input.split('\n') if ',' in l}
    
    semua_karyawan = []
    for t in tandems: semua_karyawan.extend([t[0].strip(), t[1].strip()])
    semua_karyawan.extend(singles)

    # Logika Waktu
    _, jml_hari = calendar.monthrange(tahun, bulan_idx)
    hari_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    # Init Data Jadwal
    jadwal_matrix = {emp: {} for emp in semua_karyawan}

    # PROSES LOGIKA PENJADWALAN
    for t in tandems:
        e1, e2 = t[0].strip(), t[1].strip()
        curr_s1 = "Pagi"
        cnt = 0
        
        for tgl in range(1, jml_hari + 1):
            dt = date(tahun, bulan_idx, tgl)
            h_nama = hari_indo[dt.weekday()]
            
            # Cek Libur
            is_e1_off = (liburs.get(e1).upper() == h_nama)
            is_e2_off = (liburs.get(e2).upper() == h_nama)
            
            if is_e1_off:
                s1, s2 = "OFF", "MID/FULL"
                cnt = 0
            elif is_e2_off:
                s1, s2 = "MID/FULL", "OFF"
                cnt = 0
            else:
                # Logika H-1 dan H+1 Libur
                # (Disederhanakan untuk Pilot: Rotasi per Blok)
                if cnt >= blok_hari:
                    curr_s1 = "MIDDLE" if curr_s1 == "Pagi" else "Pagi"
                    cnt = 0
                s1 = curr_s1
                s2 = "Pagi" if s1 == "MIDDLE" else "MIDDLE"
                cnt += 1
                
            jadwal_matrix[e1][tgl] = s1
            jadwal_matrix[e2][tgl] = s2

    for s_emp in singles:
        for tgl in range(1, jml_hari + 1):
            dt = date(tahun, bulan_idx, tgl)
            h_nama = hari_indo[dt.weekday()]
            if liburs.get(s_emp).upper() == h_nama:
                s = "OFF"
            else:
                s = "PAGI" # Default Single sesuai permintaan
            jadwal_matrix[s_emp][tgl] = s

    # === RENDERING HTML TABLE ===
    nama_bulan = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]
    
    html_res = f"""
    <div class="print-container">
        <div class="header-main">JADWAL KERJA OFFICE BULAN {nama_bulan[bulan_idx-1]} {tahun}</div>
        <table class="jadwal-table">
            <tr>
                <th rowspan="2">HARI</th>
                <th rowspan="2">TANGGAL</th>
                <th colspan="{len(semua_karyawan)}">NAMA KARYAWAN</th>
                <th rowspan="2">MINGGU KE</th>
            </tr>
            <tr>
                {" ".join([f"<th>{name}</th>" for name in semua_karyawan])}
            </tr>
    """

    # Isi Baris
    for tgl in range(1, jml_hari + 1):
        dt = date(tahun, bulan_idx, tgl)
        h_nama = hari_indo[dt.weekday()]
        
        # Hitung Minggu Ke (Sesuai gambar: baris per 7 hari)
        minggu_ke = (tgl - 1) // 7 + 1
        
        html_res += f"<tr><td>{h_nama}</td><td>{tgl}</td>"
        
        for emp in semua_karyawan:
            shift = jadwal_matrix[emp][tgl]
            cls = ""
            if shift == "OFF": cls = "bg-off"
            elif shift == "MIDDLE": cls = "bg-middle"
            elif shift == "Pagi": cls = "bg-pagi"
            elif shift == "MID/FULL": cls = "bg-midfull"
            
            html_res += f"<td class='{cls}'>{shift}</td>"
        
        # Kolom Minggu Ke dengan Rowspan (hanya muncul di baris pertama tiap minggu)
        if (tgl - 1) % 7 == 0:
            html_res += f"<td rowspan='7' style='font-size: 24px;'>{minggu_ke}</td>"
        
        html_res += "</tr>"

    html_res += "</table></div>"
    
    st.markdown(html_res, unsafe_allow_html=True)
    st.info("💡 Tekan **Ctrl + P** untuk mencetak hasil ini ke PDF atau Printer.")
else:
    st.warning("Silakan klik tombol 'Generate Jadwal' di sidebar untuk melihat hasil.")
