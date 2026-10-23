#Defines what kind of tokens exist :
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __str__(self):
        return f"{self.type:<12} {self.value:<15} Line: {self.line:<3} Column: {self.column}"