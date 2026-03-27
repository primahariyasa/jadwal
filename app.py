import streamlit as st
import streamlit.components.v1 as components
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Fix Roster AGM1")

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("⚙️ Konfigurasi")
    divisi = st.text_input("Nama Divisi", "AGM1")
    tahun = st.number_input("Tahun", value=2026)
    bulan = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_mid = st.text_input("Label Shift Siang", "MIDDLE")
    hari_rotasi = st.slider("Ganti Shift Setiap (Hari)", 1, 5, 2)
    
    st.divider()
    tandem_txt = st.text_area("Tandem (Nama1,Nama2)", "SUBAWA,RAKA\nPRIMA,BELLA")
    single_txt = st.text_area("Single (Nama)", "WIRA\nDERY")
    libur_txt = st.text_area("Libur Rutin (Nama,Hari)", "PRIMA,MINGGU\nBELLA,SABTU\nWIRA,SELASA\nDERY,KAMIS\nSUBAWA,RABU\nRAKA,JUMAT")

# --- ENGINE LOGIC ---
def process_logic():
    tandem_pairs = [t.split(',') for t in tandem_txt.split('\n') if ',' in t]
    singles = [s.strip().upper() for s in single_txt.split('\n') if s.strip()]
    libur_map = {l.split(',')[0].strip().upper(): l.split(',')[1].strip().upper() for l in libur_txt.split('\n') if ',' in l}
    
    names = []
    for p in tandem_pairs: names.extend([p[0].strip().upper(), p[1].strip().upper()])
    names.extend(singles)
    
    _, last_day = calendar.monthrange(tahun, bulan)
    h_indo = ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
    
    sched = {n: {d: None for d in range(1, last_day + 1)} for n in names}

    # 1. Tandai OFF dan Wajib Pagi/Middle
    for n in names:
        off_day = libur_map.get(n)
        for d in range(1, last_day + 1):
            if h_indo[date(tahun, bulan, d).weekday()] == off_day:
                sched[n][d] = "OFF"
                if d > 1 and sched[n][d-1] != "OFF": sched[n][d-1] = "PAGI"
                if d < last_day: sched[n][d+1] = label_mid

    # 2. Logic Tandem dengan Rotasi Adil
    for p in tandem_pairs:
        e1, e2 = p[0].strip().upper(), p[1].strip().upper()
        for d in range(1, last_day + 1):
            blok = (d - 1) // hari_rotasi
            s1_rot = "PAGI" if blok % 2 == 0 else label_mid
            s2_rot = label_mid if blok % 2 == 0 else "PAGI"

            if sched[e1][d] == "OFF": sched[e2][d] = "MID/FULL"
            elif sched[e2][d] == "OFF": sched[e1][d] = "MID/FULL"
            else:
                if not sched[e1][d]: sched[e1][d] = s1_rot
                if not sched[e2][d]: sched[e2][d] = s2_rot if sched[e1][d] != s2_rot else s2_rot # safety check

    # 3. Logic Single
    for s in singles:
        for d in range(1, last_day + 1):
            if not sched[s][d]: sched[s][d] = "PAGI"
                
    return sched, names, last_day, h_indo

# --- RENDER KE HTML STRING ---
if st.sidebar.button("🚀 GENERATE JADWAL", type="primary", use_container_width=True):
    data, staff, d_max, h_list = process_logic()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: white; margin: 0; padding: 20px; }}
            .container {{ text-align: center; width: 100%; }}
            .btn-print {{ 
                background: #10b981; color: white; border: none; padding: 12px 24px; 
                border-radius: 6px; font-weight: bold; cursor: pointer; margin-bottom: 20px;
            }}
            table {{ width: 100%; border-collapse: collapse; border: 2px solid black; }}
            th {{ background: #333; color: white; border: 1px solid black; padding: 8px; font-size: 12px; }}
            td {{ border: 1px solid black; padding: 6px; text-align: center; font-size: 11px; font-weight: bold; }}
            
            .OFF {{ background-color: #FF0000 !important; color: white !important; }}
            .PAGI {{ background-color: #92D050 !important; color: black !important; }}
            .{label_mid} {{ background-color: #FFFF00 !important; color: black !important; }}
            .MID-FULL {{ background-color: #0070C0 !important; color: white !important; }}
            
            @media print {{
                .btn-print {{ display: none; }}
                @page {{ size: A4 landscape; margin: 5mm; }}
                body {{ padding: 0; }}
                table {{ -webkit-print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <button class="btn-print" onclick="window.print()">🖨️ CETAK JADWAL KE PDF</button>
            <h1 style="text-decoration: underline; margin: 0;">JADWAL KERJA DIVISI {divisi.upper()}</h1>
            <h2 style="margin: 5px 0 20px 0;">BULAN {calendar.month_name[bulan].upper()} {tahun}</h2>
            
            <table>
                <thead>
                    <tr>
                        <th rowspan="2" style="width: 70px;">HARI</th>
                        <th rowspan="2" style="width: 30px;">TGL</th>
                        <th colspan="{len(staff)}">NAMA KARYAWAN</th>
                        <th rowspan="2" style="width: 30px;">W</th>
                    </tr>
                    <tr>
                        {" ".join([f"<th>{n}</th>" for n in staff])}
                    </tr>
                </thead>
                <tbody>
    """

    for d in range(1, d_max + 1):
        dt = date(tahun, bulan, d)
        h_name = h_list[dt.weekday()]
        row_bg = "background-color: #f2f2f2;" if h_name == "MINGGU" else ""
        
        html_content += f"<tr style='{row_bg}'><td>{h_name}</td><td>{d}</td>"
        
        for n in staff:
            val = data[n][d]
            cls = val.replace("/", "-") if val else ""
            html_content += f"<td class='{cls}'>{val}</td>"
        
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            w_idx = (d + date(tahun, bulan, 1).weekday() - 1) // 7 + 1
            html_content += f"<td rowspan='{span}' style='background: white; color: #888;'>{w_idx}</td>"
        html_content += "</tr>"

    html_content += "</tbody></table></div></body></html>"

    # INI KUNCINYA: Menggunakan Components untuk render HTML murni
    components.html(html_content, height=1200, scrolling=True)

else:
    st.info("Atur parameter lalu klik GENERATE JADWAL")
