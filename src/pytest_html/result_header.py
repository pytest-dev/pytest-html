from dataclasses import dataclass


@dataclass
class ResultHeader:
    label: str
    class_html: str
    col: str
