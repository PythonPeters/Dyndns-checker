import streamlit as st
import socket
import requests
import pandas as pd
import time
from datetime import datetime
import os

LOG_PATH = "data/log.csv"
os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="DynDNS Checker", page_icon="DynDNS.png", layout="centered")

st.title("🌐 DynDNS Verbinding Checker")
st.markdown("Controleer automatisch de status en het IP-adres van je DynDNS-host.")

host = st.text_input("DynDNS-hostnaam", "srge.dyndns.org")
auto_refresh = st.checkbox("Automatisch vernieuwen elke 10 seconden")

# als auto-refresh aanstaat → herlaad de pagina elke 10 seconden
if auto_refresh:
    st.markdown(
        """
        <meta http-equiv="refresh" content="10">
        """,
        unsafe_allow_html=True,
    )

if st.button("Verbinding controleren") or auto_refresh:
    if not host.strip():
        st.warning("Voer een geldige hostnaam in.")
    else:
        with st.spinner("Bezig met controleren..."):
            try:
                ip = socket.gethostbyname(host)
                st.info(f"**Gevonden IP-adres:** {ip}")

                start = time.time()
                response = requests.get(f"http://{host}", timeout=5)
                duration = round(time.time() - start, 2)

                if response.ok:
                    st.success(f"✅ Verbinding OK ({duration}s, status {response.status_code})")
                else:
                    st.warning(f"⚠️ Host bereikbaar, maar status: {response.status_code}")

                new_row = pd.DataFrame([{
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "host": host,
                    "ip": ip,
                    "status": response.status_code,
                    "response_time": duration
                }])

                if os.path.exists(LOG_PATH):
                    df = pd.read_csv(LOG_PATH)
                    df = pd.concat([df, new_row], ignore_index=True)
                else:
                    df = new_row
                df.to_csv(LOG_PATH, index=False)

            except socket.gaierror:
                st.error("❌ Host niet gevonden (DNS-fout).")
            except requests.exceptions.RequestException:
                st.error("❌ Host niet bereikbaar.")

if os.path.exists(LOG_PATH):
    st.subheader("📜 Logboek (laatste 10 checks)")
    df = pd.read_csv(LOG_PATH)
    st.dataframe(df.tail(10), use_container_width=True)
