import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Sistem Jadwal Kerja v3")

# --- KONFIGURASI ---
hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
bulan_indo = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

st.title("📋 Manajemen Jadwal Kerja Otomatis")
st.markdown("Tampilan terstruktur berdasarkan Minggu, Tanggal, dan Nama Karyawan.")

# === SIDEBAR: PENGATURAN ===
st.sidebar.header("⚙️ Parameter Jadwal")

tahun = st.sidebar.number_input("Tahun", min_value=2024, max_value=2030, value=date.today().year)
bulan_idx = st.sidebar.selectbox("Bulan", range(1, 13), index=date.today().month - 1, format_func=lambda x: bulan_indo[x-1])
nama_shift_siang = st.sidebar.radio("Sebutan Shift Siang:", ["Middle", "Siang"])
blok_hari = st.sidebar.slider("Rotasi Shift (Hari)", 1, 4, 3)

with st.sidebar.expander("👥 Input Karyawan", expanded=True):
    input_tandem = st.text_area("Tandem (Nama1,Nama2)", "Prima,Bella\nRaka,Subawa")
    input_single = st.text_area("Single (Nama)", "Joko\nBudi")

with st.sidebar.expander("🏖️ Libur Rutin", expanded=True):
    input_libur = st.text_area("Nama,Hari (Contoh: Prima,Minggu)", "Prima,Minggu\nBella,Senin\nJoko,Sabtu")

# === LOGIKA PEMPROSESAN ===
if st.button("🔄 Generate & Tampilkan Jadwal", type="primary"):
    # Parsing Data
    list_tandem = [b.split(',') for b in input_tandem.split('\n') if ',' in b]
    list_single = [b.strip() for b in input_single.split('\n') if b.strip()]
    list_libur = [b.split(',') for b in input_libur.split('\n') if ',' in b]
    
    _, jml_hari = calendar.monthrange(tahun, bulan_idx)
    semua_karyawan = [t[0].strip() for t in list_tandem] + [t[1].strip() for t in list_tandem] + list_single
    
    # Penentuan Libur & Aturan H-1/H+1
    aturan_paksa = {emp: {} for emp in semua_karyawan}
    hari_map = {"Senin":0, "Selasa":1, "Rabu":2, "Kamis":3, "Jumat":4, "Sabtu":5, "Minggu":6}
    
    for l in list_libur:
        emp, hr = l[0].strip(), l[1].strip().capitalize()
        if emp in aturan_paksa and hr in hari_map:
            target_hari = hari_map[hr]
            for tgl in range(1, jml_hari + 1):
                if calendar.weekday(tahun, bulan_idx, tgl) == target_hari:
                    aturan_paksa[emp][tgl] = 'Libur'
                    if tgl > 1: aturan_paksa[emp][tgl-1] = 'Pagi'
                    if tgl < jml_hari: aturan_paksa[emp][tgl+1] = nama_shift_siang

    # Penampung Data Akhir (Long Format)
    data_jadwal = []

    # Fungsi bantu hitung minggu ke- berapa dalam bulan tersebut
    def get_week_of_month(tgl):
        first_day = date(tahun, bulan_idx, 1)
        dom = tgl
        adjusted_dom = dom + first_day.weekday()
        return (adjusted_dom - 1) // 7 + 1

    # Logika Isi Shift (Tandem)
    for t in list_tandem:
        e1, e2 = t[0].strip(), t[1].strip()
        curr_s1 = 'Pagi'
        cnt = 0
        for tgl in range(1, jml_hari + 1):
            at1, at2 = aturan_paksa[e1].get(tgl), aturan_paksa[e2].get(tgl)
            
            if at1 == 'Libur': s1, s2, cnt = 'Libur', (at2 if at2 else 'Pagi'), 0
            elif at2 == 'Libur': s2, s1, cnt = 'Libur', (at1 if at1 else 'Pagi'), 0
            else:
                if at1: s1, s2, curr_s1, cnt = at1, (nama_shift_siang if at1=='Pagi' else 'Pagi'), at1, 1
                elif at2: s2, s1, curr_s1, cnt = at2, (nama_shift_siang if at2=='Pagi' else 'Pagi'), (nama_shift_siang if at2=='Pagi' else 'Pagi'), 1
                else:
                    if cnt >= blok_hari:
                        curr_s1 = nama_shift_siang if curr_s1 == 'Pagi' else 'Pagi'
                        cnt = 0
                    s1, s2 = curr_s1, ('Pagi' if curr_s1 == nama_shift_siang else nama_shift_siang)
                    cnt += 1
            
            # Simpan ke list besar
            dt = date(tahun, bulan_idx, tgl)
            data_jadwal.append({"Minggu": f"Minggu {get_week_of_month(tgl)}", "Tanggal": dt, "Hari": hari_indo[dt.weekday()], "Nama": e1, "Shift": s1})
            data_jadwal.append({"Minggu": f"Minggu {get_week_of_month(tgl)}", "Tanggal": dt, "Hari": hari_indo[dt.weekday()], "Nama": e2, "Shift": s2})

    # Logika Isi Shift (Single)
    for e in list_single:
        for tgl in range(1, jml_hari + 1):
            s = aturan_paksa[e].get(tgl, 'Pagi')
            dt = date(tahun, bulan_idx, tgl)
            data_jadwal.append({"Minggu": f"Minggu {get_week_of_month(tgl)}", "Tanggal": dt, "Hari": hari_indo[dt.weekday()], "Nama": e, "Shift": s})

    # Konversi ke DataFrame
    df_final = pd.DataFrame(data_jadwal)
    df_final = df_final.sort_values(by=['Tanggal', 'Nama'])

    # === DISPLAY TABEL ===
    st.subheader(f"📅 Jadwal Kerja Periode {bulan_indo[bulan_idx-1]} {tahun}")
    
    # Gunakan Filter di Streamlit untuk interaksi ekstra
    search_nama = st.multiselect("Filter Nama Karyawan:", semua_karyawan)
    if search_nama:
        df_display = df_final[df_final['Nama'].isin(search_nama)]
    else:
        df_display = df_final

    # Styling DataFrame
    def style_shift(row):
        color = ''
        if row.Shift == 'Libur': color = 'background-color: #ffcccc'
        elif row.Shift == 'Pagi': color = 'background-color: #cce5ff'
        else: color = 'background-color: #e5ffcc'
        return [color] * len(row)

    st.dataframe(
        df_display, 
        column_config={
            "Tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
            "Shift": st.column_config.SelectboxColumn("Shift", options=["Pagi", "Middle", "Siang", "Libur"])
        },
        use_container_width=True,
        hide_index=True
    )

    # Export CSV
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Jadwal (Excel/CSV)", data=csv, file_name=f"Jadwal_{bulan_indo[bulan_idx-1]}_{tahun}.csv", mime='text/csv')

    st.success("✅ Jadwal berhasil disusun dengan rotasi per-blok dan aturan libur otomatis.")
