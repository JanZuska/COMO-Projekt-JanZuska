#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
__author__ = "Jan Zuska"
__date__ = "2023/4/17"
__copyright__ = "Copyright 2023, Jan Zuska"
__credits__ = []
__license__ = "GPLv3"
__version__ = "1.0.1"
__maintainer__ = "Jan Zuska"
__email__ = "zuskan@post.cz"
__status__ = "Production"
# ----------------------------------------------------------------------------
# standard library
import asyncio
import time
import threading as th
import bs4 as bs
# ----------------------------------------------------------------------------
# 3rd party packeges
from streamlit.runtime.scriptrunner import add_script_run_ctx
import streamlit as st
import pandas as pd
import aiohttp
# ----------------------------------------------------------------------------
# custom packeges
from lokality import Lokality
from api import SearchForQueryValues, SearchQuery
# ----------------------------------------------------------------------------

# Seznam session_states
session_states_list = [
    {"kraj" : "Hlavní město Praha"},
    {"x" : 0},
    {"kill_progress_bar" : False} ]

# Definování session_states, pokud neexistují
for item in session_states_list:
    for key, value in item.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Funkce
def ProgressStatus(increment: float) -> None:
    st.session_state.x += increment
    print(f"{st.session_state.x}%")
    return

async def FormatHTML(html: str) -> bs.BeautifulSoup:
    soup = bs.BeautifulSoup(html, "html.parser")
    return soup

async def send_request(url, increment) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            ProgressStatus(increment)
            return await response.text()
        
async def process_data(response, n) -> dict:
    html = await FormatHTML(response)
    output = {"Adresa" : None, "Cena" : None }

    tag_futures = []
    for tag, attribute, key in [["a", {"href": "#mapa"}, "Adresa"], ["strong", {"class": "h4"}, "Cena"]]:
        html_tag = html.find_all(tag, attribute)
        tag_future = asyncio.ensure_future(loop.run_in_executor(None, html_tag[0].get_text)) if html_tag else None
        tag_futures.append(tag_future)

    ProgressStatus(n)

    tag_texts = await asyncio.gather(*tag_futures)
    for key, text in zip(["Adresa", "Cena"], tag_texts):
        if text:
            output[key] = text

    nemovitost_parametry = html.select("div.paramsTable")
    for table in nemovitost_parametry:
        for element in table.find_all("tr"):
            th = element.find("th").text
            td = element.find("td").text
            output.update({th : td})
            
    return output

def split_list(input_list: list, max_list_size: int = 200) -> list:
    output_list = []
    for i in range(0, len(input_list), max_list_size):
        output_list.append(input_list[i:i + max_list_size])
    return output_list

def ProgressBar(my_bar: st.progress, text: str) -> None:
    progress_bar_thread = th.Thread(target = UpdateProgressBar, args=(my_bar, text))
    add_script_run_ctx(progress_bar_thread)
    progress_bar_thread.start()

def UpdateProgressBar(progress_bar: st.progress, text: str) -> None:
        while True:
            progress_bar.progress(int(st.session_state.x), text=text)
            if st.session_state.kill_progress_bar:
                progress_bar.progress(100, text=text)
                time.sleep(0.2)
                progress_bar.empty()
                st.session_state.x = 0
                st.session_state.kill_progress_bar = False
                return

def main(location: str):
    progress_bar_1 = st.progress(0, text="Zpracování požadavku...")
    ProgressBar(progress_bar_1, "Zpracování požadavku...")
    
    time_start = time.time()
    query_values = SearchForQueryValues(location).GetQueryValues()
    print(time.time() - time_start)

    search_query = SearchQuery.BuildSearchQuery(st.session_state.chci, query_values)
    print(time.time() - time_start)

    ProgressStatus(5)

    number_of_pages = SearchQuery(search_query).NumberOfPages()
    print(time.time() - time_start)

    article_list = []
    search_queries = []

    for page in range(1, number_of_pages + 1):
        search_queries.append(f"{search_query}&page={page}")
    print(time.time() - time_start)

    ProgressStatus(20)
    increment = 70 / len(search_queries)

    tasks = [send_request(url, increment) for url in search_queries]
    responses_1 = loop.run_until_complete(asyncio.gather(*tasks))
    print(time.time() - time_start)

    for response in responses_1:
        html = bs.BeautifulSoup(response, features="html.parser")
        html_article_list = html.find_all("article")
        for link in html_article_list:
            article_list.append(link.find("a").get("href"))
    print(time.time() - time_start)

    ProgressStatus(5)
    st.session_state.kill_progress_bar = True

    time.sleep(0.3)

    progress_bar_2 = st.progress(0, text="Vyhledávání...")
    ProgressBar(progress_bar_2, "Vyhledávání...")
    increment = 100 / (len(article_list) * 2)
    
    if len(article_list) > 200:
        article_lists = split_list(article_list)
        responses = []
        for articles in article_lists:
            tasks = [send_request(url, increment) for url in articles]
            responses_2 = loop.run_until_complete(asyncio.gather(*tasks))
            responses.extend(responses_2)
            print(time.time() - time_start)

        tasks = [process_data(resp, increment) for resp in responses]
        results = loop.run_until_complete(asyncio.gather(*tasks))
            
        print(time.time() - time_start)

        df = pd.DataFrame()
        for item in results:
            df = pd.concat([df, pd.DataFrame.from_dict([item])])

        st.session_state.kill_progress_bar = True

        return df
    else:
        tasks = [send_request(url, increment) for url in article_list]
        responses_2 = loop.run_until_complete(asyncio.gather(*tasks))
        print(time.time() - time_start)

        tasks = [process_data(resp, increment) for resp in responses_2]
        results = loop.run_until_complete(asyncio.gather(*tasks))
            
        print(time.time() - time_start)

        df = pd.DataFrame()
        for item in results:
            df = pd.concat([df, pd.DataFrame.from_dict([item])])

        st.session_state.kill_progress_bar = True

        return df
    
def search():
    if st.session_state.okres == []:
        df = main(st.session_state.kraj)
        st.dataframe(df)
    else:
        for okres in st.session_state.okres:
            df = main(okres)
            st.dataframe(df)

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

button_style = """
        <style>
        .stButton > button {
            width: 100%;
        }
        </style>
        """
st.markdown(button_style, unsafe_allow_html=True)

if vyhledat_button:
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

    st.session_state.kill_progress_bar = False
    st.session_state.x = 0

    search()
    loop.close()

            








