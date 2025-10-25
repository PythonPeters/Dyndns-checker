import streamlit as st
import socket
import requests
import pandas as pd
import time
from datetime import datetime

LOG_PATH = "data/log.csv"

# Zorg dat logmap bestaat
import os
os.makedirs("data", exist_ok=True)

st.set_page_config(page_title="DynDNS Checker", page_icon="🌐", layout="centered")

st.title("🌐 DynDNS Verbinding Checker")

st.markdown("Controleer snel de status en het IP-adres van je DynDNS-host.")

# Invoer veld
host = st.text_input("DynDNS-hostnaam", "mijnserver.dyndns.org")

# Interval voor automatische hercontrole
auto_refresh = st.checkbox("Automatisch hercontroleren (elke 60 sec)")

# Knop
if st.button("Verbinding controleren") or auto_refresh:
    if not host.strip():
        st.warning("Voer een geldige hostnaam in.")
    else:
        with st.spinner("Bezig met controleren..."):
            try:
                ip = socket.gethostbyname(host)
                st.info(f"**Gevonden IP-adres:** {ip}")

                # Probeer HTTP-request
                start = time.time()
                response = requests.get(f"http://{host}", timeout=5)
                duration = round(time.time() - start, 2)

                if response.ok:
                    st.success(f"✅ Verbinding OK ({duration}s, status {response.status_code})")
                else:
                    st.warning(f"⚠️ Host bereikbaar, maar status: {response.status_code}")

                # Log opslaan
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

# Toon logboek
if os.path.exists(LOG_PATH):
    st.subheader("📜 Logboek")
    df = pd.read_csv(LOG_PATH)
    st.dataframe(df.tail(10), use_container_width=True)

# Automatisch refresh (client side)
if auto_refresh:
    st.experimental_rerun()
