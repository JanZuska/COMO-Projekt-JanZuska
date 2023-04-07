import streamlit as st
from lokality import Lokality

# Kontrola, zda existuje soubor kraje.txt
try:
    with open("kraje.txt", "rb") as file:
        # Formátování krajů z byte stringu zpátky na seznam
        kraje = file.read().decode("windows-1250")[1:-1].replace("'", "").split(", ")
except:
    Lokality().Kraje()
    with open("kraje.txt", "rb") as file:
        kraje = file.read().decode("windows-1250")[1:-1].replace("'", "").split(", ")

# Kontrola, zda existuje soubor okres.txt
try:
    with open("okresy.txt", "rb") as file:
        # Formátování krajů z byte stringu zpátky na slovník
        okresy_1 = file.read().decode("windows-1250")[1:-1].replace("'", "").split(", ")
        
except:
    Lokality().Okresy()
    with open("okresy.txt", "rb") as file:
        okresy = file.read().decode("windows-1250")[1:-1].replace("'", "").split(", ")

okresy = {}
for okres in okresy_1:
    okres = okres.split(" : ")
    okresy.update({okres[0] : okres[1]})

seznam_okresu = []
for key, value in sorted(okresy.items()):
    if value == st.session_state.kraj:
        seznam_okresu.append(key)

if "zvoleny_okres" not in st.session_state:
    st.session_state["zvoleny_okres"] = 0


with st.sidebar:
    st.write(st.session_state.kraj)
    st.selectbox(label="CHCI", options=["Prodej", "Pronájem"], key="chci")
    st.selectbox(label="KRAJ", options=kraje, key="kraj")
    x = st.selectbox(label="OKRES", options=seznam_okresu, key="okres")