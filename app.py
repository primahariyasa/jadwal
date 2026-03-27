import streamlit as st
import calendar
from datetime import date, timedelta

# Konfigurasi Dasar
st.set_page_config(layout="wide", page_title="Sistem Jadwal Kerja Divisi")

# --- CSS STABIL UNTUK CETAK A4 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    
    body { font-family: 'Roboto', sans-serif; }

    /* Pengaturan Print */
    @media print {
        @page { size: A4 landscape; margin: 10mm; }
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"] {
            display: none !important;
        }
        .main .block-container { padding: 0 !important; margin: 0 !important; }
        .print-area { width: 100% !important; display: block !important; }
        table { width: 100% !important; border-collapse: collapse !important; table-layout: fixed; }
        th, td { border: 1.5pt solid black !important; padding: 4px !important; font-size: 9pt !important; }
        .bg-off { background-color: #ff0000 !important; color: white !important; -webkit-print-color-adjust: exact; }
        .bg-pagi { background-color: #d9ead3 !important; -webkit-print-color-adjust: exact; }
        .bg-mid { background-color: #fff2cc !important; -webkit-print-color-adjust: exact; }
        .bg-full { background-color: #cfe2f3 !important; -webkit-print-color-adjust: exact; }
    }

    /* UI Table Desktop */
    .roster-table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 2px solid #333; }
    .roster-table th { background-color: #f3f4f6; border: 1px solid #333; padding: 8px; font-size: 11px; font-weight: bold; text-align: center; }
    .roster-table td { border: 1px solid #333; padding: 6px; text-align: center; font-size: 11px; font-weight: bold; }
    
    /* Warna Sel */
    .bg-off { background-color: #ff0000; color: white; }
    .bg-pagi { background-color: #d9ead3; color: #274e13; }
    .bg-mid { background-color: #fff2cc; color: #7f6000; }
    .bg-full { background-color: #cfe2f3; color: #073763; }

    .btn-print {
        background-color: #059669; color: white; padding: 12px 24px; border: none;
        border-radius: 6px; font-weight: bold; cursor: pointer; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# === SIDEBAR INPUT ===
with st.sidebar:
    st.header("📋 Parameter Laporan")
    divisi = st.text_input("Nama Divisi", "OPERASIONAL")
    tahun = st.number_input("Tahun", value=2026)
    bulan = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_siang = st.text_input("Nama Shift Siang", "MIDDLE")
    rotasi = st.slider("Blok Rotasi (Hari)", 1, 4, 2)
    
    st.divider()
    tandem_raw = st.text_area("Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_raw = st.text_area("Single (Nama)", "WIRA\nDERY")
    libur_raw = st.text_area("Libur Rutin (Nama,Hari)", "SUBAWA,RABU\nRAKA,JUMAT\nPRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS")

# === LOGIKA ENGINE V6 (PRECISION) ===
def generate_schedule():
    tandems = [t.split(',') for t in tandem_raw.split('\n') if ',' in t]
    singles = [s.strip().upper() for s in single_raw.split('\n') if s.strip()]
    libur_dict = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_raw.split('\n') if ',' in l}
    
    karyawan = []
    for t in tandems: karyawan.extend([t[0].strip().upper(), t[1].strip().upper()])
    karyawan.extend(singles)
    
    _, jml_hari = calendar.monthrange(tahun, bulan)
    hari_nama = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    # Init matrix dengan None
    matrix = {emp: {d: None for d in range(1, jml_hari + 1)} for emp in karyawan}

    # 1. Tentukan OFF (Libur Rutin)
    for emp in karyawan:
        day_off = libur_dict.get(emp)
        for d in range(1, jml_hari + 1):
            if hari_nama[date(tahun, bulan, d).weekday()] == day_off:
                matrix[emp][d] = "OFF"

    # 2. Tentukan Aturan H-1 (Pagi) dan H+1 (Middle)
    for emp in karyawan:
        for d in range(1, jml_hari + 1):
            if matrix[emp][d] == "OFF":
                if d > 1 and matrix[emp][d-1] != "OFF": 
                    matrix[emp][d-1] = "PAGI"
                if d < jml_hari and matrix[emp][d+1] != "OFF": 
                    matrix[emp][d+1] = label_siang

    # 3. Proses Tandem (Partner Coverage & Rotation)
    for t in tandems:
        e1, e2 = t[0].strip().upper(), t[1].strip().upper()
        curr_e1_state = "PAGI"
        cnt = 0
        
        for d in range(1, jml_hari + 1):
            s1, s2 = matrix[e1][d], matrix[e2][d]
            
            # Kasus: Salah satu OFF
            if s1 == "OFF" and s2 != "OFF":
                matrix[e2][d] = "MID/FULL"
                cnt = 0
            elif s2 == "OFF" and s1 != "OFF":
                matrix[e1][d] = "MID/FULL"
                cnt = 0
            # Kasus: Keduanya masuk (Normal Rotation)
            elif not s1 and not s2:
                if cnt >= rotasi:
                    curr_e1_state = label_siang if curr_e1_state == "PAGI" else "PAGI"
                    cnt = 0
                matrix[e1][d] = curr_e1_state
                matrix[e2][d] = "PAGI" if curr_e1_state == label_siang else label_siang
                cnt += 1
            # Kasus: Sudah ada mandatori H-1/H+1 di salah satu
            elif s1 and not s2:
                matrix[e2][d] = "PAGI" if s1 == label_siang else label_siang
            elif s2 and not s1:
                matrix[e1][d] = "PAGI" if s2 == label_siang else label_siang
    
    # 4. Proses Single (Sisa yang kosong)
    for s in singles:
        for d in range(1, jml_hari + 1):
            if not matrix[s][d]:
                matrix[s][d] = "PAGI"
                
    return matrix, karyawan, jml_hari, hari_nama

# === TAMPILAN ===
st.title("🖥️ Jadwal Kerja System")

if st.sidebar.button("🚀 GENERATE JADWAL", type="primary"):
    data, emps, d_max, h_list = generate_schedule()
    
    # Tombol Cetak
    st.markdown("""
        <div class="no-print">
            <button class="btn-print" onclick="window.print()">🖨️ CETAK JADWAL (PDF A4)</button>
        </div>
    """, unsafe_allow_html=True)

    # HTML Output
    html_res = f"""
    <div class="print-area">
        <div style="text-align:center; margin-bottom: 20px;">
            <h2 style="margin:0; text-decoration: underline;">JADWAL KERJA DIVISI {divisi.upper()}</h2>
            <h3 style="margin:5px 0;">PERIODE: {calendar.month_name[bulan].upper()} {tahun}</h3>
        </div>
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
        h_nama = h_list[dt.weekday()]
        
        # Style row jika hari Minggu
        row_style = "style='background-color:#f9f9f9;'" if h_nama == "MINGGU" else ""
        
        html_res += f"<tr {row_style}><td>{h_nama}</td><td>{d}</td>"
        
        for e in emps:
            shift = data[e][d]
            cls = ""
            if shift == "OFF": cls = "bg-off"
            elif shift == "PAGI": cls = "bg-pagi"
            elif shift in ["MIDDLE", "SIANG"]: cls = "bg-mid"
            elif shift == "MID/FULL": cls = "bg-full"
            else: cls = "bg-mid" # Untuk label kustom
            
            html_res += f"<td class='{cls}'>{shift}</td>"
        
        # Kolom Minggu Ke (Merged)
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            # Hitung minggu ke- berapa dalam bulan
            w_no = (d + date(tahun, bulan, 1).weekday() - 1) // 7 + 1
            html_res += f"<td rowspan='{span}' style='background:#fff;'>{w_no}</td>"
            
        html_res += "</tr>"

    html_res += "</tbody></table></div>"
    st.markdown(html_res, unsafe_allow_html=True)
    
else:
    st.info("Atur parameter divisi dan karyawan di sidebar, lalu klik Generate.")
