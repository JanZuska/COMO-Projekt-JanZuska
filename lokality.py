import requests as req
import bs4 as bs
import json

class Lokality():
    def __init__(self):
        url = "https://www.statnisprava.cz/rstsp/redakce.nsf/i/kraje_okresy_obce"
        response = req.get(url)
        html = bs.BeautifulSoup(response.text, features="html.parser")
        div = html.find("div", {"class" : "clanek"})
        lokality = div.findAll("li")

        self.seznam_lokalit = []
        for lokalita in lokality:
            self.seznam_lokalit.append(lokalita.get_text())
            
    def Kraje(self):
        kraje = self.seznam_lokalit[0:14]
        with open("kraje.txt", "wb") as file:
            data = str(kraje).encode("windows-1250")
            file.write(data)
            file.close()

    def Okresy(self):
        okresy_1 = self.seznam_lokalit[14:]
        okresy_1.remove("Praha (Hlavní město Praha)")

        okresy = {}
        for okres in okresy_1:
            okres = okres.split("(")
            okresy.update({okres[0] : okres[1][:-1]})

        with open("okresy.txt", "wb") as file:
            data = str(okresy).encode("windows-1250")
            file.write(data)
            file.close()

if __name__ == "__main__":
    Lokality().Kraje()
    Lokality().Okresy()

    

