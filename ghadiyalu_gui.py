import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from io import BytesIO
from openpyxl.styles import Alignment
from astral import LocationInfo
from astral.sun import sun
from pytz import timezone

st.set_page_config(page_title="Ghadiyalu Calculator", layout="centered")

# Title
st.title("⏱️ Ghadiyalu Calculator")

# Cities
cities = {
    "Hyderabad": {"lat": 17.385044, "lon": 78.486671},
    "Mumbai": {"lat": 19.075983, "lon": 72.877655},
    "Delhi": {"lat": 28.613939, "lon": 77.209021},
    "Bengaluru": {"lat": 12.971599, "lon": 77.594566},
    "Chennai": {"lat": 13.082680, "lon": 80.270718},
    "Kolkata": {"lat": 22.572646, "lon": 88.363895},
    "Pune": {"lat": 18.520430, "lon": 73.856743},
    "Jaipur": {"lat": 26.912434, "lon": 75.787271},
    "Ahmedabad": {"lat": 23.022505, "lon": 72.571362},
    "Lucknow": {"lat": 26.846708, "lon": 80.946159},
    "Eluru": {"lat": 16.7100, "lon": 81.1000},
    "Rajahmundry": {"lat": 16.9902, "lon": 81.7893},
    "Vijayawada": {"lat": 16.5062, "lon": 80.6480},
    "Visakapatnam": {"lat": 17.6868, "lon": 83.2185},
}

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    city_input = st.selectbox("Select City", list(cities.keys()))
    calc_date = st.date_input("Select Date", value=date.today())

# Helpers
def min_to_sec_per_ghadi(minutes):
    return int(round((minutes * 60) / 30))

def ghadi_rows(start, sec_per_ghadi, batch):
    rows, cur = [], start
    for i in range(1, 31):
        nxt = cur + timedelta(seconds=sec_per_ghadi)
        rows.append({
            "Date": cur.strftime("%d:%m:%Y"),
            "Week": cur.strftime("%A"),
            "Batch": batch,
            "Ghadi No": i,
            "Start Time": cur.strftime("%H:%M:%S"),
            "End Time": nxt.strftime("%H:%M:%S"),
        })
        cur = nxt
    return rows

def highlight_running(df, now):
    def color_row(row):
        start = datetime.combine(now.date(), datetime.strptime(row["Start Time"], "%H:%M:%S").time())
        end   = datetime.combine(now.date(), datetime.strptime(row["End Time"], "%H:%M:%S").time())
        if end < start:
            end += timedelta(days=1)
        start = timezone("Asia/Kolkata").localize(start)
        end   = timezone("Asia/Kolkata").localize(end)
        return ['background-color: #FFF5A5'] * len(row) if start <= now <= end else [''] * len(row)
    return df.style.apply(color_row, axis=1)

# Button
if st.button("🔍 Calculate Ghadiyalu"):

    try:
        ist = timezone("Asia/Kolkata")
        loc = cities[city_input]
        city = LocationInfo(city_input, "India", "Asia/Kolkata", loc["lat"], loc["lon"])

        s = sun(city.observer, date=calc_date)
        sunrise = s["sunrise"].astimezone(ist)
        sunset  = s["sunset"].astimezone(ist)
        next_sunrise = sun(city.observer, date=calc_date + timedelta(days=1))["sunrise"].astimezone(ist)

        # Sunrise/Sunset Box (works in VS Code)
        with st.container():
            st.subheader("🌅 Sunrise / Sunset")
            st.info(f"Sunrise: **{sunrise.strftime('%H:%M')}**  |  Sunset: **{sunset.strftime('%H:%M')}**")

        # Morning
        day_minutes = (sunset - sunrise).total_seconds() / 60
        sec_day = min_to_sec_per_ghadi(day_minutes)
        morning_df = pd.DataFrame(ghadi_rows(sunrise, sec_day, "Morning Ghadiyas"))

        # Evening
        night_minutes = (next_sunrise - sunset).total_seconds() / 60
        sec_night = min_to_sec_per_ghadi(night_minutes)
        evening_df = pd.DataFrame(ghadi_rows(sunset, sec_night, "Evening Ghadiyas"))

        combined_df = pd.concat([morning_df, evening_df], ignore_index=True)
        now = datetime.now(ist)

        # Display Ghadi Tables with Natural Headers
        st.subheader("🌅 Morning Ghadiyas")
        st.dataframe(highlight_running(morning_df, now), use_container_width=True)

        st.subheader("🌙 Evening Ghadiyas")
        st.dataframe(highlight_running(evening_df, now), use_container_width=True)

        st.subheader("📘 Combined Ghadiyas")
        st.dataframe(highlight_running(combined_df, now), use_container_width=True)

        # Excel Export
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            morning_df.to_excel(writer, index=False, sheet_name="Morning Ghadiyas")
            evening_df.to_excel(writer, index=False, sheet_name="Evening Ghadiyas")
            combined_df.to_excel(writer, index=False, sheet_name="Combined")

            for ws in writer.sheets.values():
                for col in ws.iter_cols(1, ws.max_column):
                    for c in col:
                        c.alignment = Alignment(horizontal="center", vertical="center")

        buf.seek(0)
        st.download_button(
            "⬇ Download Excel",
            buf.getvalue(),
            "ghadiyalu.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error: {e}")
