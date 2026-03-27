import streamlit as st
import pandas as pd
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Sistem Jadwal Cerdas")

# --- KAMUS HARI & BULAN ---
hari_indo = {"Senin": 0, "Selasa": 1, "Rabu": 2, "Kamis": 3, "Jumat": 4, "Sabtu": 5, "Minggu": 6}
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

# === SIDEBAR: PENGATURAN ===
st.sidebar.header("⚙️ Pengaturan Jadwal")

tahun = st.sidebar.number_input("Tahun", min_value=2024, max_value=2030, value=date.today().year)
bulan_idx = st.sidebar.selectbox("Bulan", range(1, 13), index=date.today().month - 1, format_func=lambda x: bulan_indo[x-1])
nama_shift_siang = st.sidebar.radio("Sebutan Shift Siang/Sore:", ["Middle", "Siang"])
blok_hari = st.sidebar.slider("Rotasi Selang-seling tiap berapa hari?", 1, 4, 2)

st.sidebar.subheader("👥 Karyawan Tandem")
input_tandem = st.sidebar.text_area("Format: Nama1,Nama2", "Prima,Bella\nRaka,Subawa")

st.sidebar.subheader("👤 Karyawan Single")
input_single = st.sidebar.text_area("Format: Nama", "Joko\nBudi")

st.sidebar.subheader("🏖️ Jadwal Libur Rutin")
input_libur = st.sidebar.text_area(
    "Format: Nama,Hari Libur", 
    "Prima,Minggu\nBella,Senin\nJoko,Sabtu"
)

# === LOGIKA PEMBUATAN JADWAL ===
if st.button("🚀 Generate Kalender Jadwal", type="primary"):
    # Parsing Input
    tandem = [b.split(',') for b in input_tandem.split('\n') if ',' in b]
    single = [b.strip() for b in input_single.split('\n') if b.strip()]
    libur_rutin = [b.split(',') for b in input_libur.split('\n') if ',' in b]

    # Data waktu
    _, jml_hari = calendar.monthrange(tahun, bulan_idx)
    daftar_hari = list(range(1, jml_hari + 1))
    
    semua_karyawan = [t[0].strip() for t in tandem] + [t[1].strip() for t in tandem] + single
    df_jadwal = pd.DataFrame(index=semua_karyawan, columns=daftar_hari)

    # 1. Tentukan Tanggal Libur berdasarkan Hari Rutin
    aturan_paksa = {emp: {} for emp in semua_karyawan}
    
    for l in libur_rutin:
        emp = l[0].strip()
        hari_libur = l[1].strip().capitalize()
        if emp in aturan_paksa and hari_libur in hari_indo:
            idx_hari_libur = hari_indo[hari_libur]
            
            # Cari semua tanggal di bulan ini yang jatuh pada hari tersebut
            for tgl in daftar_hari:
                if calendar.weekday(tahun, bulan_idx, tgl) == idx_hari_libur:
                    aturan_paksa[emp][tgl] = 'Libur'
                    if tgl > 1:
                        aturan_paksa[emp][tgl - 1] = 'Pagi' # H-1 Wajib Pagi
                    if tgl < jml_hari:
                        aturan_paksa[emp][tgl + 1] = nama_shift_siang # H+1 Wajib Middle/Siang

    # 2. Proses Karyawan Single
    for emp in single:
        for tgl in daftar_hari:
            # Ikuti aturan libur/H-1/H+1, jika tidak ada, kembalikan ke default (Pagi)
            df_jadwal.loc[emp, tgl] = aturan_paksa[emp].get(tgl, 'Pagi')

    # 3. Proses Karyawan Tandem (Rotasi per Blok Hari)
    for t in tandem:
        emp1, emp2 = t[0].strip(), t[1].strip()
        
        shift_sekarang_e1 = 'Pagi'
        counter_blok = 0

        for tgl in daftar_hari:
            at1 = aturan_paksa[emp1].get(tgl)
            at2 = aturan_paksa[emp2].get(tgl)

            # Jika ada yang libur
            if at1 == 'Libur':
                s1, s2 = 'Libur', (at2 if at2 and at2 != 'Libur' else 'Pagi')
                counter_blok = 0 # Reset ritme
            elif at2 == 'Libur':
                s2, s1 = 'Libur', (at1 if at1 and at1 != 'Libur' else 'Pagi')
                counter_blok = 0
            else:
                # Cek paksaan H-1/H+1
                if at1 and not at2:
                    s1 = at1
                    s2 = nama_shift_siang if s1 == 'Pagi' else 'Pagi'
                    shift_sekarang_e1 = s1
                    counter_blok = 1
                elif at2 and not at1:
                    s2 = at2
                    s1 = nama_shift_siang if s2 == 'Pagi' else 'Pagi'
                    shift_sekarang_e1 = s1
                    counter_blok = 1
                else:
                    # Rotasi normal menggunakan Blok Hari
                    if counter_blok >= blok_hari:
                        shift_sekarang_e1 = nama_shift_siang if shift_sekarang_e1 == 'Pagi' else 'Pagi'
                        counter_blok = 0
                    
                    s1 = shift_sekarang_e1
                    s2 = 'Pagi' if s1 == nama_shift_siang else nama_shift_siang
                    counter_blok += 1
            
            df_jadwal.loc[emp1, tgl] = s1
            df_jadwal.loc[emp2, tgl] = s2

    # === TAMPILAN KALENDER HTML (SIAP CETAK) ===
    st.markdown(f"<h2 style='text-align: center;'>Jadwal Kerja - {bulan_indo[bulan_idx-1]} {tahun}</h2>", unsafe_allow_html=True)
    
    # Render UI Kalender
    cal_html = """
    <style>
        .calendar-table {width: 100%; border-collapse: collapse; font-family: sans-serif; table-layout: fixed;}
        .calendar-table th {background-color: #4CAF50; color: white; border: 1px solid #ddd; padding: 10px; text-align: center;}
        .calendar-table td {border: 1px solid #ddd; padding: 5px; vertical-align: top; height: 120px;}
        .tgl-header {font-weight: bold; border-bottom: 1px solid #eee; margin-bottom: 5px; padding-bottom: 3px; color: #333;}
        .shift-item {font-size: 12px; margin: 2px 0; padding: 2px 4px; border-radius: 3px;}
        .shift-Pagi {background-color: #e3f2fd; color: #0d47a1;}
        .shift-Middle {background-color: #e8f5e9; color: #1b5e20;}
        .shift-Siang {background-color: #e8f5e9; color: #1b5e20;}
        .shift-Libur {background-color: #ffebee; color: #b71c1c; font-weight: bold;}
        
        @media print {
            body { -webkit-print-color-adjust: exact; }
            .stSidebar, button { display: none !important; }
            .calendar-table td { height: 100px; }
        }
    </style>
    <table class="calendar-table">
        <tr>
            <th>Senin</th><th>Selasa</th><th>Rabu</th><th>Kamis</th><th>Jumat</th><th>Sabtu</th><th>Minggu</th>
        </tr>
    """

    # Buat matriks kalender
    cal_matrix = calendar.monthcalendar(tahun, bulan_idx)
    
    for minggu in cal_matrix:
        cal_html += "<tr>"
        for hari in minggu:
            if hari == 0:
                cal_html += "<td style='background-color: #f9f9f9;'></td>" # Hari kosong di awal/akhir bulan
            else:
                cal_html += f"<td><div class='tgl-header'>{hari}</div>"
                for emp in semua_karyawan:
                    shift = df_jadwal.loc[emp, hari]
                    # Format tampilan: Prima (Pagi)
                    cal_html += f"<div class='shift-item shift-{shift}'><b>{emp}</b>: {shift}</div>"
                cal_html += "</td>"
        cal_html += "</tr>"
    cal_html += "</table>"

    st.markdown(cal_html, unsafe_allow_html=True)
    
    st.info("💡 **Tips:** Untuk mencetak kalender ini secara rapi, Anda bisa langsung menekan **Ctrl + P** (Windows) atau **Cmd + P** (Mac) di browser Anda.")
