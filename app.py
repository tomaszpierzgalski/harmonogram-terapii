import streamlit as st
import pandas as pd

st.title("Harmonogram terapii dzieci 👶🧠")

dzieci = pd.read_excel("dzieci.xlsx", sheet_name="dzieci")
specjalisci = pd.read_excel("specjalisci.xlsx", sheet_name="Specjaliści")

st.subheader("Dane dzieci")
st.dataframe(dzieci)

st.subheader("Dane specjalistów")
st.dataframe(specjalisci)

# Tu dodamy logikę planowania i wyświetlania harmonogramu
