from dataclasses import dataclass

#dataclasses voor overzicht van de info
@dataclass
class Kamerlid:
    naam: str
    partij: str
    woonplaats: str
    leeftijd: str
    anc: str
    link: str
    img: str
    id: int

@dataclass
class Partij:
    naam: str
    zetels: str
    voorzitter: str
    voorzitterId: int
    afkorting: str

@dataclass
class Motie:
    id: int
    indiener: str
    steuners: list 
    info: str
    datum: str

@dataclass
class Commissie:
    naam: str
    leden: list 