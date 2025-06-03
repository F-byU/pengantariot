import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from io import BytesIO

# Firebase URL (ambil semua data PZEM, bukan cuma arus)
FIREBASE_URL = "https://piot-c14e2-default-rtdb.firebaseio.com/pzemData.json"

# Auto-refresh setiap 5 detik
st_autorefresh(interval=5000, key="datarefresh")

# Inisialisasi session state
if "history" not in st.session_state:
    st.session_state.history = []

if "just_reset" not in st.session_state:
    st.session_state.just_reset = False

# Fungsi ambil data dari Firebase
def get_sensor_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            raw_data = response.json()
        else:
            raw_data = {}
    except:
        raw_data = {}

    try:
        voltage = round(float(raw_data.get("voltage", 0)), 2)
        current = round(float(raw_data.get("current", 0)), 2)
        power = round(float(raw_data.get("power", 0)), 2)
        energy = round(float(raw_data.get("energy", 0)), 3)
        frequency = round(float(raw_data.get("frequency", 0)), 2)
        pf = round(float(raw_data.get("pf", 0)), 2)
    except:
        voltage = current = power = energy = frequency = pf = "--"

    try:
        if power != "--":
            biaya = round((power / 1000) * 1500, 2)
        else:
            biaya = "--"
    except:
        biaya = "--"

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "voltage": voltage,
        "current": current,
        "power": power,
        "energy": energy,
        "frequency": frequency,
        "pf": pf,
        "biaya": biaya
    }

# Judul Aplikasi
st.title("🔌 MONITORING SENSOR PZEM004T v3 - ESP32")

# Tombol Reset History
if st.button("🔄 Reset History"):
    st.session_state.history = []
    st.session_state.just_reset = True

# Ambil data terbaru
data = get_sensor_data()

# Tambahkan data ke history jika bukan hasil reset
if data["power"] != "--" and not st.session_state.just_reset:
    if not st.session_state.history or st.session_state.history[-1]["timestamp"] != data["timestamp"]:
        st.session_state.history.append(data)
else:
    if st.session_state.just_reset:
        st.session_state.just_reset = False

# Tampilkan Data Sensor Saat Ini
st.subheader("📟 Data Sensor Saat Ini")
col1, col2, col3 = st.columns(3)
col1.metric("Voltage (V)", data["voltage"])
col2.metric("Frequency (Hz)", data["frequency"])
col3.metric("Power Factor", data["pf"])

col1.metric("Current (A)", data["current"])
col2.metric("Power (W)", data["power"])
col3.metric("Energy (kWh)", data["energy"])

# Format biaya
biaya_format = f"{data['biaya']:.2f}" if data["biaya"] != "--" else "--"
st.markdown(f"**💰 Biaya: Rp {biaya_format}**")

# Tampilkan History
st.subheader("🕒 History Penggunaan")
if st.session_state.history:
    formatted_history = []
    for item in st.session_state.history:
        formatted_item = {}
        for key, value in item.items():
            if isinstance(value, float):
                formatted_item[key] = f"{value:.2f}"
            else:
                formatted_item[key] = value
        formatted_history.append(formatted_item)

    st.table(formatted_history)

    total_biaya = sum(float(item["biaya"]) for item in st.session_state.history if item["biaya"] != "--")
    st.markdown(f"### 🧾 Total Biaya: Rp {total_biaya:.2f}")

    # Export to Excel
    df_export = pd.DataFrame(formatted_history)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='History Sensor')
        writer.save()
        processed_data = output.getvalue()

    st.download_button(
        label="📥 Export ke Excel",
        data=processed_data,
        file_name="data_history_sensor.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.write("Belum ada data history...")
