import requests as req
import bs4 as bs

class Lokality():
    def __init__(self) -> None:
        url = "https://www.statnisprava.cz/rstsp/redakce.nsf/i/kraje_okresy_obce"
        response = req.get(url)
        html = bs.BeautifulSoup(response.text, features="html.parser")
        div = html.find("div", {"class" : "clanek"})
        lokality = div.findAll("li")

        self.seznam_lokalit = []
        for lokalita in lokality:
            self.seznam_lokalit.append(lokalita.get_text())
            
    def Kraje(self) -> list:
        kraje = self.seznam_lokalit[0:14]
        return kraje

    def Okresy(self):
        seznam_okresu = self.seznam_lokalit[14:]
        seznam_okresu.remove("Praha (Hlavní město Praha)")
        okresy = {}
        for okres in seznam_okresu:
            okres = okres.split("(")
            okresy.update({okres[0] : okres[1][:-1]})
        return okresy
        
if __name__ == "__main__":
    object = Lokality()
    kraje = object.Kraje()
    okresy = object.Okresy()
    print(kraje)
    print(okresy)

    

