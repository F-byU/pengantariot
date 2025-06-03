import streamlit as st
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from io import BytesIO
import time

# Firebase URL
FIREBASE_URL = "https://piot-c14e2-default-rtdb.firebaseio.com/pzemData.json"

st.set_page_config(page_title="PZEM004T Monitoring", page_icon="⚡️", layout="wide")

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
            biaya = round((power / 1000) * 1400, 2)
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

# Fungsi reset energy di Firebase
def reset_energy():
    try:
        response = requests.patch(FIREBASE_URL, json={"energy": 0})
        if response.status_code in [200, 204]:
            st.success("✅ History dan energy berhasil di-reset!")
        else:
            st.error(f"❌ Gagal reset. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Gagal reset: {e}")

# Header
st.markdown(
    """
    <div style='text-align: center; color: #2c3e50;'>
        <h1>⚡️ Monitoring PZEM004T v3 - ESP32 ⚡️</h1>
        <h4 style='color: #2980b9;'>Realtime Monitoring Listrik, Biaya, & Insight</h4>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# Tombol Reset
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    if st.button("🔄 Reset Data"):
        st.session_state.history = []
        st.session_state.just_reset = True
        with st.spinner("Resetting..."):
            time.sleep(1)
            reset_energy()

# Data Terbaru
data = get_sensor_data()

if data["power"] != "--" and not st.session_state.just_reset:
    if not st.session_state.history or st.session_state.history[-1]["timestamp"] != data["timestamp"]:
        st.session_state.history.append(data)
else:
    if st.session_state.just_reset:
        st.session_state.just_reset = False

# DATA SAAT INI
with st.container():
    st.markdown("### 📊 **Data Sensor Saat Ini**")
    col_v1, col_v2, col_v3 = st.columns(3)
    col_v1.metric("🔌 Voltage (V)", data["voltage"])
    col_v2.metric("💡 Current (A)", data["current"])
    col_v3.metric("⚡ Power (W)", data["power"])

    col_v4, col_v5, col_v6 = st.columns(3)
    col_v4.metric("🔋 Energy (kWh)", data["energy"])
    col_v5.metric("🎵 Frequency (Hz)", data["frequency"])
    col_v6.metric("⚙️ Power Factor", data["pf"])

    biaya_format = f"{data['biaya']:.2f}" if data["biaya"] != "--" else "--"
    st.markdown(f"**💰 Biaya saat ini: <span style='color:#e67e22;'>Rp {biaya_format}</span>**", unsafe_allow_html=True)

    if isinstance(data["power"], float):
        progress = min(data["power"] / 200, 1.0)
        st.progress(progress, text="Power usage progress")

# TIPS HEMAT ENERGI
with st.expander("💡 Tips Hemat Energi"):
    st.markdown(
        """
        - Gunakan peralatan elektronik dengan standar SNI.
        - Matikan lampu & alat listrik saat tidak digunakan.
        - Gunakan lampu LED hemat energi.
        - Optimalkan penggunaan peralatan (contoh: set suhu kulkas pada 4°C).
        """
    )

# FAKTA MENARIK
with st.expander("⚡ Fakta Menarik Tentang Listrik"):
    st.markdown(
        """
        - **Kilatan petir** mengandung energi 5 miliar Joule!
        - **Voltase standar** di rumah Indonesia adalah 220 Volt.
        - **1 kWh** setara dengan 3,6 juta Joule energi.
        """
    )

# History
st.markdown("---")
st.markdown("### 📜 **History Penggunaan (Full)**")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    for col in ["voltage", "current", "power", "energy", "frequency", "pf", "biaya"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(2)
    st.dataframe(df, use_container_width=True, height=400)

    with st.expander("📈 Grafik Power (W)"):
        st.line_chart(df.set_index("timestamp")["power"])

    total_biaya = df["biaya"].sum()
    st.markdown(f"<h4 style='color:#16a085;'>💵 Total Biaya: Rp {total_biaya:.2f}</h4>", unsafe_allow_html=True)

    def convert_to_excel(dataframe):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="History")
        return output.getvalue()

    excel_data = convert_to_excel(df)
    st.download_button(
        label="📥 Download Excel",
        data=excel_data,
        file_name="history_penggunaan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("🚫 Belum ada data history...")

# TESTIMONI PENGGUNA
st.markdown("---")
st.markdown("### 🗣️ **Apa kata mereka?**")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.info("💬 *“Aplikasi ini sangat membantu saya memantau konsumsi listrik rumah!”* — **Rusdi, Jakarta**")
with col_b:
    st.success("💬 *“Saya bisa hemat biaya listrik hingga 15%! Keren banget!”* — **Azril, Bandung**")
with col_c:
    st.warning("💬 *“Sekarang saya paham data voltase & frekuensi di rumah saya.”* — **Andriana, Surabaya**")
# AUTHOR INFO
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #95a5a6;'>
        <em>🛠️ by Fby.U — 2025</em>  
        <br>
        📧 Kontak: <a href='mailto:youremail@example.com'>fikribayuaji.2022@student.uny.ac.id</a>
    </div>
    """,
    unsafe_allow_html=True
)
