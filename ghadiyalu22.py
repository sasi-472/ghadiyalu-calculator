import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from pytz import timezone

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="Ghadiyalu Calculator",
    page_icon="⏱️",
    layout="centered"
)

# -------------------------------------------------
# UI Styles
# -------------------------------------------------
st.markdown("""
<style>
.main { background-color: #f5f7fa; }
.section-header {
    background-color: #4a90e2;
    color: white;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 20px;
    margin-top: 20px;
}
.sun-box {
    background: linear-gradient(90deg, #f6d365, #fda085);
    padding: 12px;
    border-radius: 10px;
    text-align: center;
    font-weight: 600;
    margin-bottom: 15px;
    font-size: 18px;
}
.date-week-box {
    background-color: #ffffff;
    color: #1E3A8A;
    padding: 10px;
    border-radius: 10px;
    text-align: center;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# App Title
# -------------------------------------------------
st.markdown("<h1 style='text-align:center;'>⏱️ Ghadiyalu Calculator</h1>", unsafe_allow_html=True)

# -------------------------------------------------
# Date Selection
# -------------------------------------------------
st.subheader("📅 Select Date")

c1, c2, c3 = st.columns(3)
with c1:
    day = st.selectbox("Day", range(1, 32))
with c2:
    month = st.selectbox("Month", range(1, 13))
with c3:
    year = st.selectbox("Year", range(2000, 2031), index=25)

date_error = False
try:
    calc_date = date(year, month, day)
    st.success(f"Selected Date: {calc_date.strftime('%d-%m-%Y')}")
except ValueError:
    st.error("Invalid date selected")
    date_error = True

# -------------------------------------------------
# Sunrise / Sunset
# -------------------------------------------------
st.subheader("🌅 Sun Timings")

c4, c5 = st.columns(2)
with c4:
    sunrise_str = st.text_input("Sunrise (HH:MM)", "06:00")
with c5:
    sunset_str = st.text_input("Sunset (HH:MM)", "18:00")

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def parse_hhmm(val):
    return datetime.strptime(val, "%H:%M").time()

def seconds_per_ghadi(total_minutes):
    return int(round((total_minutes * 60) / 30))

def build_ghadi_rows(
    start_dt,
    sec_per_ghadi,
    batch_label,
    fixed_weekday=None,
    fixed_date=None
):
    rows = []
    cur = start_dt

    for i in range(1, 31):
        nxt = cur + timedelta(seconds=sec_per_ghadi)

        rows.append({
            "Date": fixed_date if fixed_date else cur.strftime("%d/%m/%Y"),
            "Week": fixed_weekday if fixed_weekday else cur.strftime("%A"),
            "Batch": batch_label,
            "Ghadi No": i,
            "Start Time": cur.strftime("%H:%M:%S"),
            "End Time": nxt.strftime("%H:%M:%S"),
        })

        cur = nxt

    return rows

def highlight_current(df, now):
    ist = timezone("Asia/Kolkata")
    if now.tzinfo is None:
        now = ist.localize(now)

    def style(row):
        start = ist.localize(datetime.combine(
            now.date(),
            datetime.strptime(row["Start Time"], "%H:%M:%S").time()
        ))
        end = ist.localize(datetime.combine(
            now.date(),
            datetime.strptime(row["End Time"], "%H:%M:%S").time()
        ))
        if end <= start:
            end += timedelta(days=1)
        if start <= now <= end:
            return ["background-color:#1B5E20;color:white;font-weight:bold"] * len(row)
        return [""] * len(row)

    return df.style.apply(style, axis=1)

# -------------------------------------------------
# PDF Generator
# -------------------------------------------------
def generate_pdf(morning_df, evening_df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()
    elements = []

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    elements.append(Paragraph("<b>GHADIYALU</b>", title_style))

    elements.append(Paragraph(
        f"Date: {calc_date.strftime('%d/%m/%Y')} | Sunrise: {sunrise_str} | Sunset: {sunset_str}",
        styles["Normal"]
    ))

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1.2, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ])

    col_widths = [2.4*cm, 2.6*cm, 3.2*cm, 1.8*cm, 3*cm, 3*cm]

    elements.append(Paragraph("<br/><b>Morning ghadiyalu</b>", styles["Heading2"]))
    m_table = Table(
        [morning_df.columns.tolist()] + morning_df.values.tolist(),
        colWidths=col_widths,
        repeatRows=1
    )
    m_table.setStyle(table_style)
    elements.append(m_table)

    elements.append(Paragraph("<br/><b>Evening ghadiyalu</b>", styles["Heading2"]))
    e_table = Table(
        [evening_df.columns.tolist()] + evening_df.values.tolist(),
        colWidths=col_widths,
        repeatRows=1
    )
    e_table.setStyle(table_style)
    elements.append(e_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------------------------------------
# Calculate
# -------------------------------------------------
st.divider()

if st.button("🔍 Calculate Ghadiyalu", use_container_width=True) and not date_error:
    ist = timezone("Asia/Kolkata")

    sunrise = ist.localize(datetime.combine(calc_date, parse_hhmm(sunrise_str)))
    sunset = ist.localize(datetime.combine(calc_date, parse_hhmm(sunset_str)))
    if sunset <= sunrise:
        sunset += timedelta(days=1)

    next_sunrise = sunrise + timedelta(days=1)

    day_minutes = (sunset - sunrise).total_seconds() / 60
    night_minutes = (next_sunrise - sunset).total_seconds() / 60

    morning_df = pd.DataFrame(
        build_ghadi_rows(
            sunrise,
            seconds_per_ghadi(day_minutes),
            "Morning ghadiya"
        )
    )

    evening_df = pd.DataFrame(
        build_ghadi_rows(
            sunset,
            seconds_per_ghadi(night_minutes),
            "Evening ghadiya",
            fixed_weekday=sunset.strftime("%A"),
            fixed_date=calc_date.strftime("%d/%m/%Y")
        )
    )

    now = datetime.now(ist)

    st.markdown(
        f"<div class='date-week-box'>📅 {calc_date.strftime('%d/%m/%Y')} | {calc_date.strftime('%A')}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='sun-box'>🌅 {sunrise_str} | 🌇 {sunset_str}</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='section-header'>🌅 Morning ghadiyalu</div>", unsafe_allow_html=True)
    st.dataframe(highlight_current(morning_df, now), hide_index=True, use_container_width=True)

    st.markdown("<div class='section-header'>🌙 Evening ghadiyalu</div>", unsafe_allow_html=True)
    st.dataframe(highlight_current(evening_df, now), hide_index=True, use_container_width=True)

    pdf = generate_pdf(morning_df, evening_df)
    st.download_button("⬇ Download PDF", pdf, "ghadiyalu.pdf", "application/pdf")

st.divider()
st.caption("© Ghadiyalu Calculator")
