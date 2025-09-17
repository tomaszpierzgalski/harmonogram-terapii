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
    st.error(f"❌ Błąd przy wczytywaniu plików: {e}")
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

# Generowanie harmonogramu z kolizjami i dostępnością
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

            # Sprawdź obecność dziecka
            if not czy_dziecko_obecne(dziecko["Obecność"], slot):
                continue

            # Sprawdź kolizje
            if klucz_dziecko in zajete_sloty or klucz_specjalista in zajete_sloty:
                continue

            # Przypisz terapię
            harmonogram.append({
                "Dzień": dzien,
                "Godzina": slot_str,
                "Terapia": dziecko["Terapia"],
                "Specjalista": dziecko["Specjalista"],
                "Dziecko": dziecko["Imię i nazwisko"]
            })

            # Zarezerwuj slot
            zajete_sloty.add(klucz_dziecko)
            zajete_sloty.add(klucz_specjalista)
            zaplanowane += 1
        if zaplanowane >= dziecko["Częstotliwość w tygodniu"]:
            break


# Widok dzienny z zakładkami
st.subheader("📅 Wybierz dzień tygodnia")
wybrany_dzien = st.selectbox("Dzień", dni)

dzien_df = harmonogram_df[harmonogram_df["Dzień"] == wybrany_dzien]

st.markdown(f"### 🗓️ Harmonogram na {wybrany_dzien}")

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
