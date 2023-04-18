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
from typing import Union
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
    {"progress" : 0},
    {"kill_progress_bar" : False},
    {"execute" : False},
    {"disabled" : False} ]

# Definování session_states, pokud neexistují
for item in session_states_list:
    for key, value in item.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ----------------------------------------------------------------------------

# Funkce a třídy
class Progress():
    def __init__(self, text) -> None:
        self.text = text
        with st.sidebar:
            self.bar = st.progress(0, text=self.text)
        self.thread = th.Thread(target = self.WhileRunning)

    def Run(self) -> None:
        self.running = True
        add_script_run_ctx(self.thread)
        self.thread.start()
        return

    def WhileRunning(self) -> None:
        while self.running:
            self.bar.progress(int(st.session_state.progress), text=self.text)
        return
    
    def Kill(self) -> None:
        self.running = False
        self.bar.progress(100, text=self.text)
        time.sleep(0.2)
        self.bar.empty()
        st.session_state.progress = 0
        return

    @staticmethod
    def AddProgress(increment: Union[float, int]) -> None:
        st.session_state.progress += increment
        print(f"{st.session_state.progress}%")
        return

class Functions():
    @staticmethod
    def split_list(input_list: list, max_list_size: int = 200) -> list:
        output_list = []
        for i in range(0, len(input_list), max_list_size):
            output_list.append(input_list[i:i + max_list_size])
        return output_list

class AsynchronousFunctions():
    @staticmethod
    async def FormatHTML(html: str) -> bs.BeautifulSoup:
        soup = bs.BeautifulSoup(html, "html.parser")
        return soup

    @staticmethod
    async def send_request(url, increment) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                Progress.AddProgress(increment)
                return await response.text()
        
    @staticmethod   
    async def process_data(response, increment) -> dict:
        html = await AsynchronousFunctions.FormatHTML(response)
        output = {"Adresa" : None, "Cena" : None }
        tag_futures = []
        for tag, attribute, key in [["a", {"href": "#mapa"}, "Adresa"], ["strong", {"class": "h4"}, "Cena"]]:
            html_tag = html.find_all(tag, attribute)
            tag_future = asyncio.ensure_future(loop.run_in_executor(None, html_tag[0].get_text)) if html_tag else None
            tag_futures.append(tag_future)
        Progress.AddProgress(increment)
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

class MainFunctions():
    @staticmethod
    def main(location: str):
        progress_bar_1 = Progress("Zpracování požadavku...")
        progress_bar_1.Run()
        
        time_start = time.time()
        query_values = SearchForQueryValues(location).GetQueryValues()
        print(time.time() - time_start)

        search_query = SearchQuery.BuildSearchQuery(st.session_state.chci, query_values)
        print(time.time() - time_start)

        Progress.AddProgress(5)

        number_of_pages = SearchQuery(search_query).NumberOfPages()
        print(time.time() - time_start)

        article_list = []
        search_queries = []

        for page in range(1, number_of_pages + 1):
            search_queries.append(f"{search_query}&page={page}")
        print(time.time() - time_start)

        Progress.AddProgress(20)
        increment = 70 / len(search_queries)

        tasks = [AsynchronousFunctions.send_request(url, increment) for url in search_queries]
        responses_1 = loop.run_until_complete(asyncio.gather(*tasks))
        print(time.time() - time_start)

        for response in responses_1:
            html = bs.BeautifulSoup(response, features="html.parser")
            html_article_list = html.find_all("article")
            for link in html_article_list:
                article_list.append(link.find("a").get("href"))
        print(time.time() - time_start)

        Progress.AddProgress(5)
        progress_bar_1.Kill()
        time.sleep(0.3)

        progress_bar_2 = Progress("Vyhledávání...")
        progress_bar_2.Run()
        increment = 100 / (len(article_list) * 2)
        
        if len(article_list) > 200:
            article_lists = Functions.split_list(article_list)
            responses = []
            for articles in article_lists:
                tasks = [AsynchronousFunctions.send_request(url, increment) for url in articles]
                responses_2 = loop.run_until_complete(asyncio.gather(*tasks))
                responses.extend(responses_2)
                print(time.time() - time_start)

            tasks = [AsynchronousFunctions.process_data(resp, increment) for resp in responses]
            results = loop.run_until_complete(asyncio.gather(*tasks))
                
            print(time.time() - time_start)

            df = pd.DataFrame()
            for item in results:
                df = pd.concat([df, pd.DataFrame.from_dict([item])])

            progress_bar_2.Kill()

            return df
        else:
            tasks = [AsynchronousFunctions.send_request(url, increment) for url in article_list]
            responses_2 = loop.run_until_complete(asyncio.gather(*tasks))
            print(time.time() - time_start)

            tasks = [AsynchronousFunctions.process_data(resp, increment) for resp in responses_2]
            results = loop.run_until_complete(asyncio.gather(*tasks))
                
            print(time.time() - time_start)

            df = pd.DataFrame()
            for item in results:
                df = pd.concat([df, pd.DataFrame.from_dict([item])])

            progress_bar_2.Kill()
            
            return df
    @staticmethod  
    def search():
        if st.session_state.okres == []:
            st.session_state.df = MainFunctions.main(st.session_state.kraj)

        else:
            dataframes = []
            for okres in st.session_state.okres:
                dataframes.append(MainFunctions.main(okres))
            df = pd.DataFrame()
            for dataframe in dataframes:
                df = pd.concat([df, dataframe])
            st.session_state.df = df


# ----------------------------------------------------------------------------

# session_state Kraje a Okresy
lokality = Lokality()
st.session_state.kraje = lokality.Kraje()
st.session_state.okresy = lokality.Okresy()

seznam_okresu = []
for key, value in sorted(st.session_state.okresy.items()):
    if value == st.session_state.kraj:
        seznam_okresu.append(key)

# ----------------------------------------------------------------------------

# Stránka
with st.sidebar:
    st.write(st.session_state.kraj)
    chci_selectbox = st.selectbox(label="CHCI", options=["Prodej", "Pronájem"], key="chci", disabled=st.session_state.disabled)
    kraj_selectbox = st.selectbox(label="KRAJ", options=st.session_state.kraje, key="kraj", disabled=st.session_state.disabled)
    okres_multiselect = st.multiselect(label="OKRES", options=seznam_okresu, key="okres", disabled=st.session_state.disabled)
    vyhledat_button = st.button(label="VYHLEDAT", key="vyhledat", disabled=st.session_state.disabled)

button_style = """
        <style>
        .stButton > button {
            width: 100%;
        }
        </style>
        """
st.markdown(button_style, unsafe_allow_html=True)

if vyhledat_button:
    st.session_state.disabled = True
    st.session_state.execute = True
    st.experimental_rerun()

if st.session_state.execute:  
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    MainFunctions.search()
    loop.close()
    st.session_state.disabled = False
    st.session_state.execute = False
    st.experimental_rerun()

if "df" in st.session_state:
    st.dataframe(st.session_state.df)






