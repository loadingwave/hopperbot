class Pronoun:
    def __init__(
        self,
        object_pronoun: str,
        subject: str,
        reflexive: str,
        possesive_pronoun: str,
        possessive_determiner: str,
    ) -> None:
        self.object = object_pronoun
        self.subject = subject
        self.reflexive = reflexive
        self.possesive_pronoun = possesive_pronoun
        self.possesive_determiner = possessive_determiner

    def em(self) -> str:
        return self.subject

    def ey(self) -> str:
        return self.subject

    def emself(self) -> str:
        return self.reflexive

    def eir(self) -> str:
        return self.possesive_pronoun

    def eirs(self) -> str:
        return self.possesive_determiner


HE = Pronoun("he", "him", "his", "his", "himself")
SHE = Pronoun("she", "her", "her", "hers", "herself")
THEY = Pronoun("they", "them", "their", "theirs", "themselves")
XEY = Pronoun("xey", "xem", "xyr", "xyrs", "xemself")
STAR = Pronoun("star", "star", "stars", "stars", "starself")
IT = Pronoun("it", "it", "its", "its", "itself")
