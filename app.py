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

for godzina in sloty:
    slot_str = godzina.strftime("%H:%M")
    slot_df = dzien_df[dzien_df["Godzina"] == slot_str]

    st.markdown(
        f"<div style='margin-top:20px; font-size:18px; font-weight:bold; color:#333;'>🕒 {slot_str}</div>",
        unsafe_allow_html=True
    )

    if slot_df.empty:
        st.markdown(
            "<div style='color:#fff; font-style:italic;'>Brak terapii</div>",
            unsafe_allow_html=True
        )
    else:
        for _, row in slot_df.iterrows():
            st.markdown(
                f"""
                <div style='
                    background-color: #e3f2fd;
                    padding: 12px;
                    margin-top: 8px;
                    border-left: 6px solid #2196f3;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    font-size: 15px;
                '>
                    <div><strong>{row["Terapia"]}</strong></div>
                    <div>👶 <strong>Dziecko:</strong> {row["Dziecko"]}</div>
                    <div>👩‍⚕️ <strong>Specjalista:</strong> {row["Specjalista"]}</div>
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
