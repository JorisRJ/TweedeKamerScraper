import DataTypes

# Kamerlid --> lid_van --> Partij
# Kamerlid --> onderdeel_van --> commissies
# Kamerlid --> dient_in --> Motie
# Kamerlis --> medeindiener_van --> Motie

# Collection namen:
# kamerleden/<id>
# partijen/<id>
# commissies/<id>
# moties/<id>

# Verschilt weinig, _key vervangt id en staat nu vooraan
def kamerlidArangoJSON(k: DataTypes.Kamerlid):
    s = "{\"_key\":\"" + str(k.id) + "\",\"naam\":\"" + k.naam + "\",\"partij\":\"" + k.partij + "\",\"woonplaats\":\"" + k.woonplaats + "\",\"leeftijd\":" + k.leeftijd.split(" ")[0] + ",\"anc\":" + k.anc.split(" ")[0] + ",\"img\":\"" + k.img  + "\"}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# _key is de afkorting, den Haan en van Haga even handmatig doen
def partijArangoJSON(p: DataTypes.Partij):
    s = "{\"_key\":\"" + p.afkorting.replace(" ", "") + "\",\"naam\":\"" + p.naam + "\",\"zetels\":" + p.zetels + ",\"voorzitter\":\"" + p.voorzitter + "\","
    s += "\"voorzitterId\":" + p.voorzitterId + "}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))
    
# Deze maakt geen gebruik van commissies maar van een naam en id, omdat commissies uit elkaar getrokken worden
def commissieArangoJSON(naam: str, x: int):
    s = "{\"_key\":\"" + str(x) + "\",\"naam\":\"" + naam + "\"}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# _key is id
def motieArangoJSON(m: DataTypes.Motie):
    s = "{\"_key\":\"" + str(m.id) + "\",\"indiener\":\""+ m.indiener + "\""
    s = s +",\"info\":\"" + m.info + "\",\"datum\":\"" + m.datum.replace(" ","").replace("\n","") + "\"}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# Linkt kamerleden aan de partij, van kamerlid naar partij
def linkKamerlidPartijJSON(x: int, k: DataTypes.Kamerlid, isVz: bool):
    s = "{\"_key\":\"" + str(x) + "\", \"_from\":\"kamerleden/" + str(k.id) + "\","
    s += "\"_to\":\"partijen/" + k.partij.replace(" ", "") + "\", \"isVoorzitter\": " + str(isVz).lower() + "}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# Linkt kamerleden aan de commissies, van kamerlid naar commissie
def linkKamerlidCommissie(x: int, k: int, c: int):
    s = "{\"_key\":\"" + str(x) + "\", \"_from\":\"kamerleden/" + str(k) + "\","
    s += "\"_to\":\"commissies/" + str(c) + "\"}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# Linkt kamerleden aan de moties, van kamerlid naar motie
def linkKamerlidMotie(x: int, k: int, m: int):
    s = "{\"_key\":\"" + str(x) + "\", \"_from\":\"kamerleden/" + str(k) + "\","
    s += "\"_to\":\"moties/" + str(m) + "\"}\n"
    return (s.encode('utf-8').decode('ascii', 'ignore'))

# Zet de partijen, kamerleden en de linkjes ertussen om naar JSON
def handleKamerledenAndPartijen(kamerleden: list, partijen: list):
    #init lijsten
    kamerledenJSON = []
    partijenJSON = []
    lid_van = []
    x = 0

    #eerst de kamerleden aan de partijen linken
    for k in kamerleden:
        kamerledenJSON.append(kamerlidArangoJSON(k))

        #kijk of het kamerlid voorzitter is
        isVz = False
        for p in partijen:
            if int(k.id) == int(p.voorzitterId):
                isVz = True
                break
        lid_van.append(linkKamerlidPartijJSON(x, k, isVz))
        x += 1

    #zet de partijen om naar json
    for p in partijen:
        partijenJSON.append(partijArangoJSON(p))

    f = open("Arango/kamerleden.json", "w+")
    for kj in kamerledenJSON:
        f.write(kj)
    f.close()
    
    f = open("Arango/partijen.json", "w+")
    for pj in partijenJSON:
        f.write(pj)
    f.close()

    f = open("Arango/lid_van.json", "w+")
    for lj in lid_van:
        f.write(lj)
    f.close()

# Parse de commissies en link ze aan kamerleden
def handleKamerledenToCommissies(commissies: list):
    #init lijsten
    commissieJSON = []
    onderdeel_van = []
    x = 0
    y = 0

    #voor iedere commissie, parse de commissie en link de leden
    for c in commissies:
        commissieJSON.append(commissieArangoJSON(c.naam, x))

        for l in c.leden:
            onderdeel_van.append(linkKamerlidCommissie(y, l, x))
            y += 1

        x += 1

    #zet ze in aparte files
    f = open("Arango/Commissies.json", "w+")
    for cj in commissieJSON:
        f.write(cj)
    f.close()
    
    f = open("Arango/onderdeel_van.json", "w+")
    for oj in onderdeel_van:
        f.write(oj)
    f.close()

# Parse de Moties en link ze aan kamerleden
def handleKamerledenToMoties(moties: list):
    #init lijsten
    motiesJSON = []
    dient_in = []
    x = 0

    #parse iedere motie en link alle steuners/mede-indieners
    for m in moties:
        motiesJSON.append(motieArangoJSON(m))

        for l in m.steuners:
            dient_in.append(linkKamerlidMotie(x, l, m.id))
            x += 1

    #zet ze in aparte files
    f = open("Arango/Moties.json", "w+")
    for mj in motiesJSON:
        f.write(mj)
    f.close()
    
    f = open("Arango/dient_in.json", "w+")
    for dj in dient_in:
        f.write(dj)
    f.close()

    