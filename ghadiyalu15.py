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

# -------------------------------------------------
# Page Config & Theme
# -------------------------------------------------

st.set_page_config(page_title="Ghadiyalu Calculator", layout="centered")

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
    color: black;
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

[data-testid="stSidebar"] { background-color: #e3eefc; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Title
# -------------------------------------------------

st.markdown("<h1 style='text-align:center;'>⏱️ Ghadiyalu Calculator</h1>", unsafe_allow_html=True)

# -------------------------------------------------
# Sidebar Inputs
# -------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    calc_date = st.date_input(
        "Select Date",
        value=date.today(),
        min_value=date(1972, 1, 1),
        max_value=date(2073, 12, 31)
    )

    sunrise_str = st.text_input("Sunrise Time (HH:MM)", "06:00", max_chars=5)
    sunset_str = st.text_input("Sunset Time (HH:MM)", "18:00", max_chars=5)

# -------------------------------------------------
# Helper Functions
# -------------------------------------------------

def parse_hhmm(value):
    return datetime.strptime(value, "%H:%M").time()

def minutes_to_seconds_per_ghadi(total_minutes):
    return int(round((total_minutes * 60) / 30))

def build_ghadi_rows(start_dt, seconds_per_ghadi, batch_label, fixed_weekday=None):
    rows = []
    cur = start_dt

    for i in range(1, 31):
        nxt = cur + timedelta(seconds=seconds_per_ghadi)

        week_day = fixed_weekday if fixed_weekday else cur.strftime("%A")

        rows.append({
            "Date": cur.strftime("%d/%m/%Y"),
            "Week": week_day,
            "Batch": batch_label,
            "Ghadi No": i,
            "Start Time": cur.strftime("%H:%M:%S"),
            "End Time": nxt.strftime("%H:%M:%S"),
        })

        cur = nxt

    return rows

def highlight_current_ghadi(df, current_dt):
    def style_row(row):
        start = datetime.combine(
            current_dt.date(),
            datetime.strptime(row["Start Time"], "%H:%M:%S").time()
        )
        end = datetime.combine(
            current_dt.date(),
            datetime.strptime(row["End Time"], "%H:%M:%S").time()
        )
        if end < start:
            end += timedelta(days=1)

        ist = timezone("Asia/Kolkata")
        start = ist.localize(start)
        end = ist.localize(end)

        if start <= current_dt <= end:
            return ["background-color:#1B5E20;color:white;font-weight:bold"] * len(row)
        return [""] * len(row)

    return df.style.apply(style_row, axis=1)

# -------------------------------------------------
# PDF Generator
# -------------------------------------------------

def generate_pdf(morning_df, evening_df, calc_date, sunrise_str, sunset_str):
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

    elements.append(Paragraph("<b>Ghadiyalu Calculator</b>", styles["Title"]))
    elements.append(Paragraph(
        f"Date: {calc_date.strftime('%d/%m/%Y')} | "
        f"Sunrise: {sunrise_str} | Sunset: {sunset_str}",
        styles["Normal"]
    ))

    elements.append(Paragraph("<br/><b>Morning Ghadiyas</b>", styles["Heading2"]))

    m_data = [morning_df.columns.tolist()] + morning_df.values.tolist()
    m_table = Table(m_data, repeatRows=1)
    m_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))
    elements.append(m_table)

    elements.append(Paragraph("<br/><b>Evening Ghadiyas</b>", styles["Heading2"]))

    e_data = [evening_df.columns.tolist()] + evening_df.values.tolist()
    e_table = Table(e_data, repeatRows=1)
    e_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))
    elements.append(e_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------------------------------------
# Main Logic
# -------------------------------------------------

if st.button("🔍 Calculate Ghadiyalu"):
    try:
        ist = timezone("Asia/Kolkata")

        sunrise_time = parse_hhmm(sunrise_str)
        sunset_time = parse_hhmm(sunset_str)

        sunrise_dt = ist.localize(datetime.combine(calc_date, sunrise_time))
        sunset_dt = ist.localize(datetime.combine(calc_date, sunset_time))

        if sunset_dt <= sunrise_dt:
            sunset_dt += timedelta(days=1)

        next_sunrise_dt = sunrise_dt + timedelta(days=1)

        st.markdown(
            f"""
            <div class='date-week-box'>
                📅 Date: {calc_date.strftime('%d/%m/%Y')} |
                🗓️ {calc_date.strftime('%A')}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div class='sun-box'>🌅 Sunrise: {sunrise_str} | 🌇 Sunset: {sunset_str}</div>",
            unsafe_allow_html=True
        )

        day_minutes = (sunset_dt - sunrise_dt).total_seconds() / 60
        night_minutes = (next_sunrise_dt - sunset_dt).total_seconds() / 60

        morning_df = pd.DataFrame(
            build_ghadi_rows(
                sunrise_dt,
                minutes_to_seconds_per_ghadi(day_minutes),
                "Morning Ghadiyas"
            )
        )

        sunset_weekday = sunset_dt.strftime("%A")

        evening_df = pd.DataFrame(
            build_ghadi_rows(
                sunset_dt,
                minutes_to_seconds_per_ghadi(night_minutes),
                "Evening Ghadiyas",
                fixed_weekday=sunset_weekday
            )
        )

        now = datetime.now(ist)

        st.markdown("<div class='section-header'>🌅 Morning Ghadiyas</div>", unsafe_allow_html=True)
        st.dataframe(
            highlight_current_ghadi(morning_df, now),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<div class='section-header'>🌙 Evening Ghadiyas</div>", unsafe_allow_html=True)
        st.dataframe(
            highlight_current_ghadi(evening_df, now),
            use_container_width=True,
            hide_index=True
        )

        pdf_buf = generate_pdf(
            morning_df,
            evening_df,
            calc_date,
            sunrise_str,
            sunset_str
        )

        st.download_button(
            "⬇ Download PDF",
            data=pdf_buf.getvalue(),
            file_name="ghadiyalu.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
