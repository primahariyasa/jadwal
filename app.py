import streamlit as st
import pandas as pd
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Pilot Jadwal Otomatis")

st.title("🗓️ Aplikasi Pembuat Jadwal Kerja Otomatis")
st.markdown("Aplikasi pilot untuk mengatur jadwal karyawan berpasangan (tandem) dan individu.")

# === SIDEBAR: PENGATURAN ===
st.sidebar.header("⚙️ Pengaturan Jadwal")

# 1. Setting Bulan & Tahun
tahun = st.sidebar.number_input("Tahun", min_value=2024, max_value=2030, value=date.today().year)
bulan = st.sidebar.selectbox("Bulan", range(1, 13), index=date.today().month - 1)

# 2. Kustomisasi Shift
nama_shift_siang = st.sidebar.radio("Sebutan untuk Shift Siang/Sore:", ["Middle", "Siang"])

# 3. Input Data Karyawan Tandem
st.sidebar.subheader("👥 Karyawan Tandem (Partner)")
st.sidebar.caption("Format: Nama1,Nama2 (pisahkan dengan koma/enter)")
input_tandem = st.sidebar.text_area(
    "Daftar Tandem", 
    "Prima,Bella\nRaka,Subawa"
)

# 4. Input Data Karyawan Single
st.sidebar.subheader("👤 Karyawan Tanpa Partner")
st.sidebar.caption("Otomatis diset ke shift Pagi (atau sesuai input)")
input_single = st.sidebar.text_area(
    "Daftar Single (Format: Nama,Shift)", 
    "Joko,Pagi\nBudi,Pagi"
)

# 5. Request Libur
st.sidebar.subheader("🏖️ Request Libur")
st.sidebar.caption("Format: Nama,Tanggal (Contoh: Prima,15 berarti Prima libur tgl 15)")
input_libur = st.sidebar.text_area(
    "Daftar Request Libur", 
    "Prima,15\nSubawa,10"
)

# === LOGIKA PEMBUATAN JADWAL ===
if st.button("🚀 Buat Jadwal Sekarang", type="primary"):
    # Parsing input dari text area
    tandem = [baris.split(',') for baris in input_tandem.split('\n') if ',' in baris]
    single = [baris.split(',') for baris in input_single.split('\n') if ',' in baris]
    libur = [baris.split(',') for baris in input_libur.split('\n') if ',' in baris]

    # Menentukan jumlah hari dalam bulan terpilih
    _, jml_hari = calendar.monthrange(tahun, bulan)
    daftar_hari = list(range(1, jml_hari + 1))

    # Mengumpulkan semua nama karyawan
    semua_karyawan = []
    for t in tandem:
        semua_karyawan.extend([t[0].strip(), t[1].strip()])
    for s in single:
        semua_karyawan.append(s[0].strip())

    # Membuat DataFrame kosong
    df_jadwal = pd.DataFrame(index=semua_karyawan, columns=daftar_hari)

    # Langkah 1: Isi jadwal untuk Karyawan Single
    for s in single:
        nama_emp = s[0].strip()
        shift_emp = s[1].strip()
        df_jadwal.loc[nama_emp, :] = shift_emp

    # Langkah 2: Proses aturan Request Libur
    aturan_paksa = {emp: {} for emp in semua_karyawan}
    for l in libur:
        nama_emp = l[0].strip()
        tgl_libur = int(l[1].strip())
        
        if nama_emp in aturan_paksa:
            # Hari H = Libur
            aturan_paksa[nama_emp][tgl_libur] = 'Libur'
            # H-1 = Wajib Pagi
            if tgl_libur > 1:
                aturan_paksa[nama_emp][tgl_libur - 1] = 'Pagi'
            # H+1 = Wajib Middle/Siang
            if tgl_libur < jml_hari:
                aturan_paksa[nama_emp][tgl_libur + 1] = nama_shift_siang

    # Langkah 3: Isi jadwal untuk Karyawan Tandem (Selang-seling)
    for t in tandem:
        emp1 = t[0].strip()
        emp2 = t[1].strip()

        # Variabel untuk melacak shift terakhir agar bisa selang-seling
        shift_terakhir_emp1 = nama_shift_siang # Set awal agar hari ke-1 emp1 dapat Pagi

        for hari in daftar_hari:
            # Cek apakah ada aturan paksa (efek libur) di hari ini
            aturan1 = aturan_paksa[emp1].get(hari)
            aturan2 = aturan_paksa[emp2].get(hari)

            # Jika salah satu libur
            if aturan1 == 'Libur':
                df_jadwal.loc[emp1, hari] = 'Libur'
                df_jadwal.loc[emp2, hari] = aturan2 if aturan2 else 'Pagi' # Partner otomatis Pagi jika tidak ada aturan lain
            elif aturan2 == 'Libur':
                df_jadwal.loc[emp2, hari] = 'Libur'
                df_jadwal.loc[emp1, hari] = aturan1 if aturan1 else 'Pagi'
            else:
                s1 = aturan1
                s2 = aturan2

                # Jika emp1 ada aturan wajib (misal H-1 libur wajib Pagi)
                if s1 and not s2:
                    s2 = nama_shift_siang if s1 == 'Pagi' else 'Pagi' # Partner menyesuaikan
                # Jika emp2 ada aturan wajib
                elif s2 and not s1:
                    s1 = nama_shift_siang if s2 == 'Pagi' else 'Pagi'
                # Jika tidak ada aturan libur, lakukan selang-seling normal
                elif not s1 and not s2:
                    s1 = nama_shift_siang if shift_terakhir_emp1 == 'Pagi' else 'Pagi'
                    s2 = 'Pagi' if s1 == nama_shift_siang else nama_shift_siang

                # Simpan ke dataframe
                df_jadwal.loc[emp1, hari] = s1
                df_jadwal.loc[emp2, hari] = s2

                # Catat shift terakhir (abaikan jika libur)
                if s1 != 'Libur':
                    shift_terakhir_emp1 = s1

    # === TAMPILKAN HASIL ===
    st.success(f"Berhasil membuat jadwal untuk Bulan {bulan} Tahun {tahun}!")
    
    # Kustomisasi warna untuk memudahkan pembacaan di Streamlit
    def color_coding(val):
        color = ''
        if val == 'Libur':
            color = 'background-color: #ffcccc; color: red;'
        elif val == 'Pagi':
            color = 'background-color: #cce5ff; color: blue;'
        elif val == 'Middle' or val == 'Siang':
            color = 'background-color: #e5ffcc; color: green;'
        return color

    st.dataframe(df_jadwal.style.map(color_coding), use_container_width=True)
