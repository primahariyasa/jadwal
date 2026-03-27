import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta

# Set page ke wide agar nyaman di layar, tapi CSS akan mengatur saat print
st.set_page_config(layout="wide", page_title="Roster Pro - A4 Ready")

# --- INJEKSI TAILWIND & CUSTOM PRINT CSS ---
st.markdown("""
<script src="https://cdn.tailwindcss.com"></script>
<style>
    /* CSS Khusus Cetak A4 */
    @media print {
        @page {
            size: A4 landscape;
            margin: 5mm;
        }
        body { background: white; }
        .no-print { display: none !important; }
        .print-area { width: 100%; zoom: 85%; } /* Zoom disesuaikan agar pas A4 */
        .stMarkdown, .stAlert { display: none; }
    }
    
    /* Styling Tabel ala Excel */
    .table-roster { border: 2px solid black; width: 100%; border-collapse: collapse; font-family: 'Arial', sans-serif; }
    .table-roster th { border: 1px solid black; padding: 4px; background-color: #f3f4f6; font-size: 11px; text-align: center; }
    .table-roster td { border: 1px solid black; padding: 4px; text-align: center; font-size: 11px; font-weight: bold; }
    
    /* Warna Label Shift */
    .shift-off { background-color: #ef4444 !important; color: white; }      /* Merah */
    .shift-pagi { background-color: #86efac !important; color: black; }     /* Hijau */
    .shift-middle { background-color: #fef08a !important; color: black; }   /* Kuning */
    .shift-midfull { background-color: #3b82f6 !important; color: white; }  /* Biru */
    
    .week-label { font-size: 18px; font-weight: bold; background-color: #f9fafb; }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR PENGATURAN ===
with st.sidebar:
    st.markdown("<h2 class='text-2xl font-bold mb-4'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1: tahun = st.number_input("Tahun", value=2026)
    with col2: bulan_idx = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    
    label_siang = st.text_input("Label Shift Siang", "MIDDLE")
    rotasi = st.slider("Rotasi Blok (Hari)", 1, 4, 2)
    
    st.divider()
    tandem_raw = st.text_area("👥 Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_raw = st.text_area("👤 Single (Nama)", "WIRA\nDERY")
    libur_raw = st.text_area("🏖️ Libur (Nama,Hari)", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === LOGIKA MESIN PENJADWALAN ===
def generate_schedule():
    # Parsing inputs
    tandems = [t.split(',') for t in tandem_raw.split('\n') if ',' in t]
    singles = [s.strip() for s in single_raw.split('\n') if s.strip()]
    libur_dict = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_raw.split('\n') if ',' in l}
    
    semua_karyawan = []
    for t in tandems: semua_karyawan.extend([t[0].strip().upper(), t[1].strip().upper()])
    semua_karyawan.extend([s.upper() for s in singles])
    
    _, jml_hari = calendar.monthrange(tahun, bulan_idx)
    hari_nama_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    # Init matrix
    matrix = {emp: {} for emp in semua_karyawan}
    
    # 1. Tentukan OFF days & Mandatori H-1/H+1
    for emp in semua_karyawan:
        libur_tetap = libur_dict.get(emp, "")
        for tgl in range(1, jml_hari + 1):
            dt = date(tahun, bulan_idx, tgl)
            if hari_nama_indo[dt.weekday()] == libur_tetap:
                matrix[emp][tgl] = "OFF"
                # H-1 Libur -> Pagi
                if tgl > 1: matrix[emp][tgl-1] = "PAGI"
                # H+1 Libur -> Siang/Middle
                if tgl < jml_hari: matrix[emp][tgl+1] = label_siang

    # 2. Isi Sisa Shift untuk Tandem
    for t in tandems:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        curr_e1 = "PAGI"
        cnt = 0
        
        for tgl in range(1, jml_hari + 1):
            # Jika sudah diisi oleh aturan OFF/H-1/H+1
            s1, s2 = matrix[e1].get(tgl), matrix[e2].get(tgl)
            
            if s1 == "OFF": 
                matrix[e2][tgl] = "MID/FULL"
                cnt = 0 # reset rotasi
            elif s2 == "OFF": 
                matrix[e1][tgl] = "MID/FULL"
                cnt = 0
            else:
                # Cek jika salah satu sudah punya mandatori (H-1/H+1)
                if s1 and not s2:
                    matrix[e2][tgl] = "PAGI" if s1 == label_siang else label_siang
                elif s2 and not s1:
                    matrix[e1][tgl] = "PAGI" if s2 == label_siang else label_siang
                elif not s1 and not s2:
                    # Rotasi normal
                    if cnt >= rotasi:
                        curr_e1 = label_siang if curr_e1 == "PAGI" else "PAGI"
                        cnt = 0
                    matrix[e1][tgl] = curr_e1
                    matrix[e2][tgl] = "PAGI" if curr_e1 == label_siang else label_siang
                    cnt += 1

    # 3. Isi Sisa Shift untuk Single
    for s_emp in singles:
        emp = s_emp.upper()
        for tgl in range(1, jml_hari + 1):
            if not matrix[emp].get(tgl):
                matrix[emp][tgl] = "PAGI"
                
    return matrix, semua_karyawan, jml_hari, hari_nama_indo

# === RENDER INTERFACE ===
st.markdown("<div class='no-print bg-blue-50 p-4 rounded-lg mb-6'>💡 <b>Tips Cetak:</b> Setelah klik Generate, tekan <b>Ctrl + P</b>. Pastikan 'Layout' diatur ke <b>Landscape</b> dan 'Margins' ke <b>None/Minimum</b>.</div>", unsafe_allow_html=True)

if st.sidebar.button("🚀 GENERATE JADWAL", use_container_width=True):
    matrix, karyawan, jml_hari, hari_indo = generate_schedule()
    
    # HTML Table Construction
    html_code = f"""
    <div class="print-area">
        <h1 class="text-center text-2xl font-bold underline mb-4">JADWAL KERJA OFFICE BULAN {calendar.month_name[bulan_idx].upper()} {tahun}</h1>
        <table class="table-roster">
            <thead>
                <tr>
                    <th rowspan="2" style="width: 80px;">HARI</th>
                    <th rowspan="2" style="width: 40px;">TGL</th>
                    <th colspan="{len(karyawan)}">NAMA KARYAWAN</th>
                    <th rowspan="2" style="width: 50px;">MINGGU KE</th>
                </tr>
                <tr>
                    {"".join([f"<th>{name}</th>" for name in karyawan])}
                </tr>
            </thead>
            <tbody>
    """
    
    for tgl in range(1, jml_hari + 1):
        dt = date(tahun, bulan_idx, tgl)
        h_nama = hari_indo[dt.weekday()]
        
        # Logika background hari Minggu
        row_style = "background-color: #fffbeb;" if h_nama == "MINGGU" else ""
        
        html_code += f"<tr style='{row_style}'><td>{h_nama}</td><td>{tgl}</td>"
        
        for emp in karyawan:
            shift = matrix[emp][tgl]
            cls = ""
            if shift == "OFF": cls = "shift-off"
            elif shift == label_siang: cls = "shift-middle"
            elif shift == "PAGI": cls = "shift-pagi"
            elif shift == "MID/FULL": cls = "shift-midfull"
            
            html_code += f"<td class='{cls}'>{shift}</td>"
        
        # Logika Minggu Ke (Rowspan)
        # Menghitung kapan kolom minggu ke muncul (setiap hari Senin atau tanggal 1)
        if tgl == 1 or dt.weekday() == 0:
            # Hitung sisa hari sampai minggu depan atau akhir bulan
            rem = 7 - dt.weekday()
            days_left = (jml_hari - tgl) + 1
            span = min(rem, days_left)
            m_ke = (tgl + 6 - dt.weekday() ) // 7 + (1 if date(tahun, bulan_idx, 1).weekday() > 0 else 0)
            # Sederhananya kita pakai hitungan minggu kalender:
            m_ke = dt.isocalendar()[1] - date(tahun, bulan_idx, 1).isocalendar()[1] + 1
            html_code += f"<td rowspan='{span}' class='week-label'>{m_ke}</td>"
            
        html_code += "</tr>"
        
    html_code += "</tbody></table></div>"
    
    st.markdown(html_code, unsafe_allow_html=True)
else:
    st.info("Silakan atur parameter di sebelah kiri dan klik Generate.")
