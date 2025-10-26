import streamlit as st
import socket
import requests
import pandas as pd
import time
from datetime import datetime
import os
import json

# --- instellingen ---
DATA_DIR = "data"
LOG_PATH = os.path.join(DATA_DIR, "log.csv")
HOSTS_PATH = os.path.join(DATA_DIR, "hosts.json")
os.makedirs(DATA_DIR, exist_ok=True)

# --- standaard hostlijst ---
default_hosts = ["srge.dyndns.org"]

# --- hosts laden of aanmaken ---
if os.path.exists(HOSTS_PATH):
    with open(HOSTS_PATH, "r") as f:
        saved_hosts = json.load(f)
else:
    saved_hosts = default_hosts
    with open(HOSTS_PATH, "w") as f:
        json.dump(saved_hosts, f)

# --- paginaconfiguratie ---
st.set_page_config(
    page_title="DynDNS Realtime Checker",
    page_icon="favicon.png"
)
st.title("🌐 DynDNS Realtime Verbinding Checker")

st.markdown("Kies een DynDNS-host uit de lijst of voeg een nieuwe toe.")

# --- host selectie ---
selected_host = st.selectbox("Selecteer host", saved_hosts)

# --- nieuwe host toevoegen ---
new_host = st.text_input("➕ Nieuwe host toevoegen (optioneel):", "")

if st.button("Host toevoegen"):
    if new_host.strip() and new_host not in saved_hosts:
        saved_hosts.append(new_host.strip())
        with open(HOSTS_PATH, "w") as f:
            json.dump(saved_hosts, f)
        st.success(f"✅ Host '{new_host.strip()}' toegevoegd!")
        st.rerun()
    elif new_host in saved_hosts:
        st.warning("Deze host staat al in de lijst.")
    else:
        st.warning("Voer een geldige hostnaam in.")

# --- controle uitvoeren ---
if st.button("Verbinding nu controleren"):
    host = selected_host
    if not host.strip():
        st.warning("Geen geldige host geselecteerd.")
    else:
        with st.spinner(f"Bezig met controleren van {host}..."):
            try:
                ip = socket.gethostbyname(host)
                st.info(f"**Gevonden IP-adres:** {ip}")

                start = time.time()
                response = requests.get(f"http://{host}", timeout=5)
                duration = round(time.time() - start, 3)

                if response.ok:
                    st.success(f"✅ Verbinding OK ({duration}s, status {response.status_code})")
                else:
                    st.warning(f"⚠️ Host bereikbaar, maar status: {response.status_code}")

                # log opslaan
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

# --- datastroom / grafiekweergave ---
if os.path.exists(LOG_PATH):
    df = pd.read_csv(LOG_PATH)

    st.subheader("📡 Laatste metingen")
    stream_text = "\n".join(
        [
            f"{row.timestamp} | {row.host} | IP: {row.ip} | Status: {row.status} | Tijd: {row.response_time}s"
            for row in df.tail(15).itertuples()
        ][::-1]
    )
    st.text(stream_text)

    st.subheader("📊 Responstijd (seconden)")
    st.line_chart(df.tail(30).set_index("timestamp")["response_time"])
