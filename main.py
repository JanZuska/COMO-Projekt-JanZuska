import streamlit as st
from lokality import Lokality
from search import SearchQueryValuesRequest

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

# Session states
session_states_list = [
    {"kraj" : "Hlavní město Praha"}
]

for item in session_states_list:
    for key, value in item.items():
        if key not in st.session_state:
            st.session_state[key] = value

okresy = {}
for okres in okresy_1:
    okres = okres.split(" : ")
    okresy.update({okres[0] : okres[1]})

seznam_okresu = []
for key, value in sorted(okresy.items()):
    if value == st.session_state.kraj:
        seznam_okresu.append(key)
        st.session_state.okres_selectbox_active = False

if (st.session_state.kraj == "Hlavní město Praha") or (st.session_state.kraj == None):
    st.session_state.okres_selectbox_active = True
    seznam_okresu = ["Žádné okresy"]

with st.sidebar:
    st.write(st.session_state.kraj)
    chci_selectbox = st.selectbox(label="CHCI", options=["Prodej", "Pronájem"], key="chci")
    kraj_selectbox = st.selectbox(label="KRAJ", options=kraje, key="kraj")
    okres_multiselect = st.multiselect(label="OKRES", options=seznam_okresu, key="okres", disabled=st.session_state.okres_selectbox_active)
    vyhledat_button = st.button(label="VYHLEDAT", key="vyhledat")
    #cena_slider = st.slider(label="CENA", min_value=0, max_value=100, value=(0,100), key="cena")

if vyhledat_button:
    if st.session_state.okres == []:
        st.write("Nic")
    else:
        for okres in st.session_state.okres:
            query_values = SearchQueryValuesRequest(okres).GetQueryValues()
            search_query = f"https://www.bezrealitky.cz/vyhledat?offerType=PRONAJEM&estateType=BYT&regionOsmIds=R{query_values['osm_id']}&osm_value={query_values['display_name']}"
