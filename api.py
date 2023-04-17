import requests as req
import json
import bs4 as bs

class SearchForQueryValues():
    def __init__(self, search_key: str) -> None:
        url = f"https://autocomplete.bezrealitky.cz/autocomplete?q=%20{search_key}&size=1&address=0&preferredCountry=cz&from=0"
        self.respone = req.get(url)
        self.data = {}

    def GetQueryValues(self) -> dict:
        json_data = json.loads(self.respone.text)
        data = json_data["features"][0]["properties"]
        display_name = data["display_name"].replace(" ", "+").replace(",", "%2C")
        osm_id = data["osm_id"]
        self.data.update({"display_name" : display_name})
        self.data.update({"osm_id" : osm_id})
        return self.data
    
class SearchQuery():
    def __init__(self, search_query: str) -> None:
        url = search_query
        response = req.get(url)
        self.html = bs.BeautifulSoup(response.text, features="html.parser")
    
    def NumberOfPages(self) -> int:
        number_of_pages = self.html.find_all("a", {"class": "page-link"})
        pages = [1]
        for page in number_of_pages:
            try:
                pages.append(int(page.get_text()))
            except:
                pass
        self.pages = int(max(pages))
        return self.pages

    @staticmethod
    def BuildSearchQuery(chci: str, query_values: dict) -> str:
        query_offer_type = str(chci).upper().replace('Á', 'A')
        query_region_osm_id = query_values['osm_id']
        query_osm_value = query_values['display_name']
        search_query = f"https://www.bezrealitky.cz/vyhledat?offerType={query_offer_type}&estateType=BYT&regionOsmIds=R{query_region_osm_id}&osm_value={query_osm_value}"
        return search_query
    
    @staticmethod
    async def GetArticles(page: int, search_querry: str, output_list: list) -> None:
        url = f"{search_querry}&page={page}"
        response = req.get(url)
        print(response)
        html = bs.BeautifulSoup(response.text, features="html.parser")
        html_article_list = html.find_all("article")
        for link in html_article_list:
            output_list.append(link.find("a").get("href"))

if __name__ == "__main__":
    pass
