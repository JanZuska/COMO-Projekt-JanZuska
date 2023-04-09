import requests as req
import json

class SearchQueryValuesRequest():
    def __init__(self, search_key):
        url = f"https://autocomplete.bezrealitky.cz/autocomplete?q=%20{search_key}&size=1&address=0&preferredCountry=cz&from=0"
        self.respone = req.get(url)
        self.data = {}

    def GetQueryValues(self):
        json_data = json.loads(self.respone.text)
        data = json_data["features"][0]["properties"]
        display_name = data["display_name"].replace(" ", "+").replace(",", "%2C")
        osm_id = data["osm_id"]
        self.data.update({"display_name" : display_name})
        self.data.update({"osm_id" : osm_id})
        return self.data
    
if __name__ == "__main__":
    pass