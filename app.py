import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Harmonogram terapii", layout="wide")
st.title("🧠 Harmonogram terapii dzieci")

# Wczytaj dane
try:
    dzieci = pd.read_excel("dzieci.xlsx", sheet_name="dzieci")
    specjalisci = pd.read_excel("specjalisci.xlsx", sheet_name="Specjaliści")
except Exception as e:
    st.error(f"❌ Błąd przy wczytywaniu plików Excel: {e}")
    st.stop()

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

# Silnik planowania terapii
harmonogram = []
zajete_sloty = set()  # (dzien, godzina, dziecko/specjalista)

for _, dziecko in dzieci.iterrows():
    zaplanowane = 0
    for dzien in dni:
        for slot in sloty:
            if zaplanowane >= dziecko["Częstotliwość w tygodniu"]:
                break

            slot_str = slot.strftime("%H:%M")
            klucz_dziecko = (dzien, slot_str, dziecko["Imię i nazwisko"])
            klucz_specjalista = (dzien, slot_str, dziecko["Specjalista"])

            if not czy_dziecko_obecne(dziecko["Obecność"], slot):
                continue
            if klucz_dziecko in zajete_sloty or klucz_specjalista in zajete_sloty:
                continue

            harmonogram.append({
                "Dzień": dzien,
                "Godzina": slot_str,
                "Terapia": dziecko["Terapia"],
                "Specjalista": dziecko["Specjalista"],
                "Dziecko": dziecko["Imię i nazwisko"]
            })

            zajete_sloty.add(klucz_dziecko)
            zajete_sloty.add(klucz_specjalista)
            zaplanowane += 1
        if zaplanowane >= dziecko["Częstotliwość w tygodniu"]:
            break

harmonogram_df = pd.DataFrame(harmonogram)

# Widok siatki godzinowej
st.subheader("📅 Wybierz dzień tygodnia")
wybrany_dzien = st.selectbox("Dzień", dni)

dzien_df = harmonogram_df[harmonogram_df["Dzień"] == wybrany_dzien]

st.markdown(f"## 🗓️ Harmonogram na {wybrany_dzien}")

siatka = "<div style='display: grid; grid-template-columns: repeat(1, 1fr); gap: 12px;'>"

for godzina in sloty:
    slot_str = godzina.strftime("%H:%M")
    slot_df = dzien_df[dzien_df["Godzina"] == slot_str]

    siatka += f"<div style='padding: 6px; background-color: #f0f0f0; border-radius: 6px;'>"
    siatka += f"<div style='font-weight: bold; font-size: 16px; color: #333;'>🕒 {slot_str}</div>"

    if slot_df.empty:
        siatka += "<div style='color: #999;'>Brak terapii</div>"
    else:
        for _, row in slot_df.iterrows():
            siatka += f"""
            <div style='
                background-color: #d0e6ff;
                padding: 8px;
                margin-top: 6px;
                border-left: 6px solid #4a90e2;
                border-radius: 4px;
                font-size: 14px;
            '>
                <strong>{row["Terapia"]}</strong><br>
                👶 {row["Dziecko"]}<br>
                👩‍⚕️ {row["Specjalista"]}
            </div>
            """
    siatka += "</div>"

siatka += "</div>"
st.markdown(siatka, unsafe_allow_html=True)

# Eksport do Excela
excel_buffer = io.BytesIO()
harmonogram_df.to_excel(excel_buffer, index=False, engine='openpyxl')
excel_buffer.seek(0)

st.download_button(
    label="📥 Pobierz cały harmonogram jako Excel",
    data=excel_buffer,
    file_name="harmonogram.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
