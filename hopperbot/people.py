from random import choice
from typing import List


class Pronoun:
    def __init__(
        self,
        object: str,
        subject: str,
        possessive_determiner: str,
        possesive_pronoun: str,
        reflexive: str,
    ) -> None:
        self.object = object
        self.subject = subject
        self.reflexive = reflexive
        self.possesive_pronoun = possesive_pronoun
        self.possesive_determiner = possessive_determiner

    def __repr__(self) -> str:
        return self.object.upper()

    def __str__(self) -> str:
        return self.object


HE = Pronoun("he", "him", "his", "his", "himself")
IT = Pronoun("it", "it", "its", "its", "itself")
SHE = Pronoun("she", "her", "her", "hers", "herself")
STAR = Pronoun("star", "star", "stars", "stars", "starself")
THEY = Pronoun("they", "them", "their", "theirs", "themselves")
XEY = Pronoun("xey", "xem", "xyr", "xyrs", "xemself")
NONE = Pronoun("error", "error", "error", "error", "error")


def convert_pronoun(b: str) -> Pronoun:
    if b == "HE":
        return HE
    elif b == "IT":
        return IT
    elif b == "SHE":
        return SHE
    elif b == "STAR":
        return STAR
    elif b == "THEY":
        return THEY
    elif b == "XEY":
        return XEY
    else:
        return NONE


class Person:
    def __init__(self, name: str, pronouns: List[Pronoun]) -> None:
        self.name = name
        self.pronouns = pronouns

    def em(self) -> str:
        return choice(self.pronouns).object

    def ey(self) -> str:
        return choice(self.pronouns).subject

    def emself(self) -> str:
        return choice(self.pronouns).reflexive

    def eir(self) -> str:
        return choice(self.pronouns).possesive_pronoun

    def eirs(self) -> str:
        return choice(self.pronouns).possesive_determiner

    def __str__(self) -> str:
        return f"{self.name} ({'/'.join(map(str, self.pronouns))})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Person):
            if not (self.name == other.name and len(self.pronouns) == len(other.pronouns)):
                return False
            else:
                return sorted(self.pronouns, key=repr) == sorted(other.pronouns, key=repr)

        else:
            return False


def adapt_person(person: Person) -> bytes:
    pronouns = map(lambda p: repr(p), person.pronouns)
    return f"{person.name};{','.join(pronouns)}".encode("utf-8")


def convert_person(b: bytes) -> Person:
    (byte_name, byte_pronouns) = b.split(";".encode("utf-8"))
    name = byte_name.decode("utf-8")
    str_pronouns = byte_pronouns.decode("utf-8")
    pronouns = list(map(convert_pronoun, str_pronouns.split(",")))
    return Person(name, pronouns)
