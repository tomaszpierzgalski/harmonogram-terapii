import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Harmonogram terapii", layout="wide")
st.title("🧠 Harmonogram terapii dzieci")

# Wczytaj dane
dzieci = pd.read_excel("dzieci.xlsx", sheet_name="dzieci")
specjalisci = pd.read_excel("specjalisci.xlsx", sheet_name="Specjaliści")

# Sloty co 30 minut od 08:00 do 14:00
sloty = [datetime.strptime("08:00", "%H:%M") + timedelta(minutes=30*i) for i in range(12)]
dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]

# Funkcja sprawdzająca obecność dziecka
def czy_dziecko_obecne(obecnosc_str, godzina):
    try:
        zakresy = [x.strip().replace("–", "-") for x in obecnosc_str.split(",")]
        for zakres in zakresy:
            start, end = zakres.split("-")
            start_time = datetime.strptime(start.strip(), "%H:%M").time()
            end_time = datetime.strptime(end.strip(), "%H:%M").time()
            if start_time <= godzina.time() < end_time:
                return True
    except:
        return False
    return False

# Generowanie harmonogramu
harmonogram = []

for _, dziecko in dzieci.iterrows():
    zaplanowane = 0
    for dzien in dni:
        for slot in sloty:
            if zaplanowane >= dziecko["Częstotliwość w tygodniu"]:
                break
            if not czy_dziecko_obecne(dziecko["Obecność"], slot):
                continue
            harmonogram.append({
                "Dzień": dzien,
                "Godzina": slot.strftime("%H:%M"),
                "Terapia": dziecko["Terapia"],
                "Specjalista": dziecko["Specjalista"],
                "Dziecko": dziecko["Imię i nazwisko"]
            })
            zaplanowane += 1
        if zaplanowane >= dziecko["Częstotliwość w tygodniu"]:
            break

harmonogram_df = pd.DataFrame(harmonogram)

# Widok kalendarzowy
st.subheader("📅 Widok tygodniowy")

cols = st.columns(len(dni))
for i, dzien in enumerate(dni):
    with cols[i]:
        st.markdown(f"### {dzien}")
        dzien_df = harmonogram_df[harmonogram_df["Dzień"] == dzien]
        for _, row in dzien_df.iterrows():
            st.markdown(
                f"""
                <div style='background-color:#f0f8ff;padding:8px;margin-bottom:6px;border-left:5px solid #4682b4'>
                    <strong>{row["Godzina"]}</strong><br>
                    👶 <em>{row["Dziecko"]}</em><br>
                    🧠 <strong>{row["Terapia"]}</strong><br>
                    👩‍⚕️ {row["Specjalista"]}
                </div>
                """,
                unsafe_allow_html=True
            )
