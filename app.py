import streamlit as st
import streamlit.components.v1 as components
import calendar
from datetime import date

st.set_page_config(layout="wide", page_title="Roster Pro v12")

# --- SIDEBAR INPUT ---
with st.sidebar:
    st.header("📋 Data Penjadwalan")
    divisi = st.text_input("Nama Divisi", "OFFICE")
    tahun = st.number_input("Tahun", value=2026)
    bulan = st.selectbox("Bulan", range(1, 13), index=3, format_func=lambda x: calendar.month_name[x])
    label_mid = st.text_input("Label Shift Siang", "MIDDLE")
    hari_rotasi = st.slider("Rotasi Shift (Hari)", 1, 5, 2)
    
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

    for n in names:
        off_day = libur_map.get(n)
        for d in range(1, last_day + 1):
            if h_indo[date(tahun, bulan, d).weekday()] == off_day:
                sched[n][d] = "OFF"
                if d > 1 and sched[n][d-1] != "OFF": sched[n][d-1] = "PAGI"
                if d < last_day: sched[n][d+1] = label_mid

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
                if not sched[e2][d]: sched[e2][d] = s2_rot
    for s in singles:
        for d in range(1, last_day + 1):
            if not sched[s][d]: sched[s][d] = "PAGI"
    return sched, names, last_day, h_indo

# --- RENDER HTML ---
if st.sidebar.button("🚀 GENERATE JADWAL", type="primary", use_container_width=True):
    data, staff, d_max, h_list = process_logic()
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Inter', Helvetica, Arial, sans-serif; background: white; margin: 0; padding: 10px; color: #333; }}
            .container {{ width: 100%; margin: 0 auto; }}
            
            .header-info {{ text-align: center; margin-bottom: 15px; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            .header-info h1 {{ font-size: 24px; margin: 0; letter-spacing: 1px; }}
            .header-info h2 {{ font-size: 16px; margin: 5px 0; color: #666; }}

            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                border: 2px solid black; 
                table-layout: fixed; 
            }}
            
            /* Header Tabel */
            th {{ background: #2d3436; color: white; border: 1px solid black; padding: 6px 2px; font-size: 11px; }}
            .col-hari {{ width: 70px; }}
            .col-tgl {{ width: 45px; }}
            .col-week {{ width: 50px; }}

            /* Cell Tabel */
            td {{ border: 1px solid black; padding: 5px 2px; text-align: center; font-size: 11px; font-weight: 700; }}
            
            /* Pembesaran Tanggal ala Kalender */
            .tgl-cell {{ font-size: 16px !important; font-weight: 900 !important; color: #000; }}
            .hari-cell {{ font-size: 11px; font-weight: 600; text-transform: uppercase; }}

            /* Warna Shift */
            .OFF {{ background-color: #d63031 !important; color: white !important; }}
            .PAGI {{ background-color: #55efc4 !important; color: #003d2b !important; }}
            .{label_mid} {{ background-color: #fdcb6e !important; color: #5d4000 !important; }}
            .MID-FULL {{ background-color: #0984e3 !important; color: white !important; }}
            
            .week-label {{ font-size: 14px !important; color: #2d3436; }}

            .no-print-zone {{ text-align: center; margin-bottom: 20px; }}
            .btn-print {{ 
                background: #00b894; color: white; border: none; padding: 12px 30px; 
                border-radius: 5px; font-weight: bold; cursor: pointer; font-size: 16px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}

            @media print {{
                .no-print-zone {{ display: none; }}
                @page {{ size: A4 landscape; margin: 8mm; }}
                body {{ zoom: 82%; -webkit-print-color-adjust: exact; }}
                table {{ width: 100% !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="no-print-zone">
            <button class="btn-print" onclick="window.print()">🖨️ PRINT JADWAL (A4 LANDSCAPE)</button>
        </div>
        <div class="container">
            <div class="header-info">
                <h1>JADWAL KERJA DIVISI {divisi.upper()}</h1>
                <h2>PERIODE: {calendar.month_name[bulan].upper()} {tahun}</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th class="col-hari">HARI</th>
                        <th class="col-tgl">TGL</th>
                        {" ".join([f"<th>{n}</th>" for n in staff])}
                        <th class="col-week">WEEK</th>
                    </tr>
                </thead>
                <tbody>
    """

    for d in range(1, d_max + 1):
        dt = date(tahun, bulan, d)
        h_name = h_list[dt.weekday()]
        row_bg = "background-color: #f8f9fa;" if h_name == "MINGGU" else ""
        
        html_content += f"<tr style='{row_bg}'>"
        html_content += f"<td class='hari-cell'>{h_name}</td>"
        html_content += f"<td class='tgl-cell'>{d}</td>"
        
        for n in staff:
            val = data[n][d]
            cls = val.replace("/", "-") if val else ""
            html_content += f"<td class='{cls}'>{val}</td>"
        
        # Kolom Week (Keterangan Minggu)
        if d == 1 or dt.weekday() == 0:
            span = min(7 - dt.weekday(), (d_max - d) + 1)
            w_idx = (d + date(tahun, bulan, 1).weekday() - 1) // 7 + 1
            html_content += f"<td rowspan='{span}' class='week-label'>Mgg {w_idx}</td>"
        html_content += "</tr>"

    html_content += "</tbody></table></div></body></html>"
    components.html(html_content, height=1200, scrolling=True)

else:
    st.info("Atur parameter lalu klik Generate.")
