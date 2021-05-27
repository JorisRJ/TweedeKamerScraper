import ArangoDBParser
from typing import ByteString, Iterable
from bs4 import BeautifulSoup
import time
from selenium import webdriver
import DataTypes

#Global vars
drv = webdriver.Firefox()

#Houd zowel link -> naam als naam -> id en id -> naam
kamerlidMap = {}

#Houd de moties bij op basis van id
motieMap = {}

#Houd de partij afkortingen bij als naam kamerlid -> afkorting partij
partijMap = {}

#De functies om de dataclasses om te zetten
def kamerLidToJSON(k: DataTypes.Kamerlid):
    s = "{\n\t\"naam\":\"" + k.naam + "\",\n\t\"partij\":\"" + k.partij + "\",\n\t\"woonplaats\":\"" + k.woonplaats + "\",\n\t\"leeftijd\":" + k.leeftijd.split(" ")[0] + ",\n\t\"anc\":" + k.anc.split(" ")[0] + ",\n\t\"id\":" + str(k.id) + ",\n\t\"img\":\"" + k.img  + "\"\n}"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

def commissieToJSON(com: DataTypes.Commissie):
    s = "{\n\t\"commissie\":\"" + str(com.naam) + "\",\n\t\"leden\": ["
    notFirst = False
    for lid in com.leden:
        if (notFirst):
            s = s + ","
        notFirst = True
        s = s + str(lid)
    s = s +"]\n}"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

def partijToJSON(p: DataTypes.Partij):
    s = "{\n\t\"naam\":\"" + p.naam + "\",\n\t\"zetels\":" + p.zetels + ",\n\t\"voorzitter\":\"" + p.voorzitter + "\",\n"
    s += "\t\"voorzitterId\":" + p.voorzitterId + ",\n\t\"afkorting\":\"" + p.afkorting + "\"\n}"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

def motieToJSON(m: DataTypes.Motie):
    s = "{\n\t\"id\":\"" + m.id + "\",\n\t\"indiener\":\""+ m.indiener + "\",\n\t\"steuners\": ["
    notFirst = False
    for lid in m.steuners:
        if (notFirst):
            s = s + ","
        notFirst = True
        s = s + str(lid)
    s = s +"],\n\t\"info\":\"" + m.info + "\",\n\t\"datum\":\"" + m.datum.replace(" ","").replace("\n","") + "\"\n}"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

#Pakt van de overzichtspagina de kamerleden-tegels
def getAllKamerleden():
    tkLink = "https://www.tweedekamer.nl/kamerleden_en_commissies/alle_kamerleden"
    drv.get(tkLink)
    html = drv.execute_script("return document.documentElement.outerHTML")
    time.sleep(1)
    sel_soup = BeautifulSoup(html, "html.parser")

    #row = sel_soup.find("noscript")
    allcards = sel_soup.find_all("div", class_="member filter-member")
    
    #deze exception moest toegevoegd worden omdat Omtzicht zijn functie elders kreeg
    #en er dus nog maar 149 kamerleden waren
    cards = allcards[(len(allcards) // 2):]
    
    # Stop de kamerleden in een file
    kamerleden = []
    x = 0
    for c in cards:
        k = getKamerlid(c, x)
        kamerleden.append(k)
        putKamerlidInMap(k)
        x += 1

    return kamerleden

def getKamerlid(soup: BeautifulSoup, x: int):
    img = soup.find("img")["src"]
    link = soup.find("a", class_="member__name")["href"]
    naam = soup.find("a", class_="member__name").get_text()
    naam = str(naam).replace("  ", " ")
    partij = soup.find("span", class_="member__tag").get_text()
    tab = soup.find("table", class_="member__info-table").find_all("td")

    # Geert wordt bedreigd dus zn woonplaats staat er niet op
    if (str(naam) == "Geert Wilders"):
        woonplaats = ""
        leeftijd = tab[1].get_text()
        anc = tab[3].get_text()
    else:
        woonplaats = tab[1].get_text()
        leeftijd = tab[3].get_text()
        anc = tab[5].get_text()

    k = DataTypes.Kamerlid(naam, partij, woonplaats, leeftijd, anc, link, img, x)
    return k

#Pakt per kamerlid de container met de commissies
def getAllCommissies(kamerleden):
    commissies = {}

    for k in kamerleden:
        link = "https://www.tweedekamer.nl" + k.link
        drv.get(link)
        site = drv.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(site, "html.parser")
        getCommissies(soup, k.id, commissies)
        print(".", end = "", flush = True)


    return commissies

def getCommissies(soup: BeautifulSoup, x: int, commissies: dict):
    comsTab = soup.find("ul", class_="list-commissies")
    if (not comsTab):
        return

    coms = comsTab.select("li a")

    #check of de commissie bestaat, zo ja voeg het kamerlid toe aan de leden
    for com in coms:
        naam = com.get_text()
        if not (naam in commissies):
            commissies[naam] = DataTypes.Commissie(naam, [x])
        else:
            commissies[naam].leden.append(x) 

#Pakt van de overzichtspagina de partij-tegels
def getAllPartijen():
    tkLink = "https://www.tweedekamer.nl/kamerleden_en_commissies/fracties"
    drv.get(tkLink)
    html = drv.execute_script("return document.documentElement.outerHTML")
    time.sleep(1)
    sel_soup = BeautifulSoup(html, "html.parser")

    cards = sel_soup.find_all("div", class_="card highlight gov-party")
    partijen = []
    for card in cards:
        partijen.append(getPartij(card))

    return partijen

def getPartij(soup: BeautifulSoup):
    naam = soup.find("a", class_="gov-party__party-name").get_text() 
    zetels = soup.find("span", class_="gov-party__seats-indication").get_text()
    voorz = soup.find("span", class_="gov-party__member-name").get_text()
    voorzId = str(kamerlidMap[voorz])
    afkrt = partijMap[voorz]

    p = DataTypes.Partij(naam, zetels, voorz, voorzId, afkrt)
    return p

#Gaat per kamerlid naar de "Alle moties" pagina en pakt vervolgens alle moties van de eerste pagina
#Zou in principe makkelijk schaalbaar moeten zijn over alle pagina's heen, moet je gewoon de
#"read more next"-link pakken
def getAllMoties(kamerleden, getAllPages: bool = False):
    for k in kamerleden:
        link = "https://www.tweedekamer.nl" + k.link
        drv.get(link)
        site = drv.execute_script("return document.documentElement.outerHTML")
        soup = BeautifulSoup(site, "html.parser")

        subpages = soup.find_all("div", class_="subpage")

        #voor als ze letterlijk niks hebbe gedaan
        if (not subpages):
            continue

        for sub in subpages:
            if (sub["data-subpage"] == "#moties"):
                subpage = sub
        
        #voor als ze geen moties hebben
        if (not subpage):
            continue
        
        nLink = "https://www.tweedekamer.nl" + subpage.find("a", class_="read-more")["href"]
        if getAllPages:
            nLink = str(nLink).replace("&dpp=15", "&dpp=1000")

        drv.get(nLink)
        nsite = drv.execute_script("return document.documentElement.outerHTML")
        nsoup = BeautifulSoup(nsite, "html.parser")
        
        getMoties(nsoup, k.naam)
        print(".", end = "", flush = True)
        
def getMoties(soup: BeautifulSoup, knaam: str):
    cards = soup.find_all("article", class_="card ___icon-right")
    
    for card in cards:
        id = card.find("span", class_="code-nummer").get_text()
        side = card.find_all("div", class_="card__side")[1]
        indiener = side.find("a")
        #Als het kamerlid niet meer in de kamer zit, heeft ie geen linkje meer
        if (not indiener):
            indiener = side.find("strong").parent.get_text().replace("\nIndiener ", "").replace(" Tweede Kamerlid", "")
            indiener = indiener[:len(indiener) - 1] #Laatste spatie weg
        else:
            indiener = indiener.get_text()

        if id in motieMap:
            # Als de motie al bestaat, voeg dit kamerlid toe aan de steuners
            # Check wel of het een huidig kamerlid is, anders niks doen
            if indiener in kamerlidMap:
                motieMap[id].steuners.append(kamerlidMap[knaam])
            continue

        #Voeg de indiener toe aan de steuners, helpt met parsen voor arangoDB data
        steuners = []
        if indiener in kamerlidMap:
                steuners.append(kamerlidMap[knaam])

        datum = card.find("div", class_="card__pretitle").get_text()
        info = card.find("p").get_text().replace("\"","'")
        motie = DataTypes.Motie(id, indiener, steuners, info, datum)
        motieMap[id] = motie   

#Korte functie die alle verwijzingen man
def putKamerlidInMap(k: DataTypes.Kamerlid):
    kamerlidMap[k.link] = k.naam
    kamerlidMap[k.naam] = k.id
    kamerlidMap[k.id] = k.naam
    partijMap[k.naam] = k.partij

#Neemt een lijst, naam v/d file en een parser functie. Parsed de lijst en stopt het in de file
def writeToFile(iter, naam: str, parser):
    f = open(naam + ".json", "w+")
    f.write("[\n")
    notFirst = False
    for i in iter:
        if (notFirst):
            f.write(",\n")
        notFirst = True
        s = parser(i)
        f.write(s)
    f.write("\n]")
    f.close()


#Zowel de getAllMoties als de getAllCommissies gaat naar ieder kamerlid en pakt daar te bijnodigde tegels.
#Je zou dit ook in één keer kunnen doen, dat is sneller, maar op deze manier kunnen ze onafhankelijk worden
#aangeroepen, voor als je er eentje overnieuw wilt doen.
def Main():
    km = getAllKamerleden()
    writeToFile(km, "kamerleden", kamerLidToJSON)
    print("Kamerleden gescraped: ", str(len(km)))

    coms = getAllCommissies(km)
    writeToFile(coms.values(), "commissies", commissieToJSON)
    print("\nCommissies gescraped")

    ptn = getAllPartijen()
    writeToFile(ptn, "partijen", partijToJSON)
    print("Partijen gescraped")

    getAllMoties(km, True)
    writeToFile(motieMap.values(), "moties", motieToJSON)
    print("\nMoties gescraped")

    # Parse naar arangodb format
    ArangoDBParser.handleKamerledenAndPartijen(km, ptn)
    ArangoDBParser.handleKamerledenToCommissies(coms.values())
    ArangoDBParser.handleKamerledenToMoties(motieMap.values())
    print("ArangoDB JSON files written")
    

Main()
