import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Harmonogram terapii", layout="wide")
st.title("🧠 Harmonogram terapii dzieci")

# 📂 Menu boczne
zakladka = st.sidebar.radio("📂 Menu", ["📅 Harmonogram", "👶 Dzieci", "👩‍⚕️ Specjaliści"])

# 📥 Wczytaj dane
try:
    dzieci = pd.read_excel("dzieci.xlsx", sheet_name="dzieci")
    specjalisci = pd.read_excel("specjalisci.xlsx", sheet_name="Specjaliści")
except Exception as e:
    st.error(f"❌ Błąd przy wczytywaniu plików Excel: {e}")
    st.stop()

# 🕒 Sloty czasowe
sloty = [datetime.strptime("08:00", "%H:%M") + timedelta(minutes=30*i) for i in range(12)]
dni = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]

# ✅ Funkcja: obecność dziecka
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

# ✅ Funkcja: dostępność specjalisty
def czy_specjalista_dostepny(specjalista, dzien, godzina):
    try:
        rekord = specjalisci[specjalisci["Imię i nazwisko"] == specjalista].iloc[0]
        zakres = rekord["Dostępność (dni/godziny)"].replace("–", "-")
        if dzien[:3] not in zakres:
            return False
        godziny = [x.strip() for x in zakres.split() if ":" in x]
        if len(godziny) != 2:
            return True
        start = datetime.strptime(godziny[0], "%H:%M").time()
        end = datetime.strptime(godziny[1], "%H:%M").time()
        return start <= godzina.time() < end
    except:
        return True

# 👶 Zakładka: edycja dzieci
if zakladka == "👶 Dzieci":
    st.subheader("👶 Edycja danych dzieci")
    for i, row in dzieci.iterrows():
        with st.expander(f"{row['Imię i nazwisko']}"):
            dzieci.at[i, "Imię i nazwisko"] = st.text_input("Imię i nazwisko", value=row["Imię i nazwisko"], key=f"imie_{i}")
            dzieci.at[i, "Terapia"] = st.text_input("Terapia", value=row["Terapia"], key=f"terapia_{i}")
            dzieci.at[i, "Obecność"] = st.text_input("Obecność (np. 08:00–12:00)", value=row["Obecność"], key=f"obecnosc_{i}")
            dzieci.at[i, "Częstotliwość w tygodniu"] = st.number_input("Częstotliwość w tygodniu", value=int(row["Częstotliwość w tygodniu"]), min_value=1, max_value=10, key=f"czestotliwosc_{i}")
    st.success("✅ Zmiany zapisane tymczasowo")

# 👩‍⚕️ Zakładka: edycja specjalistów
elif zakladka == "👩‍⚕️ Specjaliści":
    st.subheader("👩‍⚕️ Edycja dostępności specjalistów")
    for i, row in specjalisci.iterrows():
        with st.expander(f"{row['Imię i nazwisko']}"):
            specjalisci.at[i, "Imię i nazwisko"] = st.text_input("Imię i nazwisko", value=row["Imię i nazwisko"], key=f"spec_imie_{i}")
            specjalisci.at[i, "Dostępność (dni/godziny)"] = st.text_input("Dostępność (np. Pon–Pt 08:00–14:00)", value=row["Dostępność (dni/godziny)"], key=f"dostepnosc_{i}")
            specjalisci.at[i, "Typy terapii"] = st.text_input("Typy terapii", value=row["Typy terapii"], key=f"typy_{i}")
    st.success("✅ Zmiany zapisane tymczasowo")

# 📅 Zakładka: harmonogram
elif zakladka == "📅 Harmonogram":
    # 🔧 Silnik planowania
    harmonogram = []
    zajete_sloty = set()

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
                if not czy_specjalista_dostepny(dziecko["Specjalista"], dzien, slot):
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

    # 📅 Widok kalendarza
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
            st.markdown("<div style='color:#999; font-style:italic;'>Brak terapii</div>", unsafe_allow_html=True)
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

    # 📥 Eksport do Excela
    excel_buffer = io.BytesIO()
    harmonogram_df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    st.download_button(
        label="📥 Pobierz harmonogram jako Excel",
        data=excel_buffer,
        file_name="harmonogram.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
