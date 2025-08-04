from typing import Mapping, Iterable

from pydantic import BaseModel
import pandas as pd


class AppData(BaseModel):
    name: str
    usage: int
    genre: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Mapping]) -> list["AppData"]:
        return [cls(name=name, **attrs) for name, attrs in data.items()]

    @staticmethod
    def to_df(items: Iterable["AppData"]) -> pd.DataFrame:
        return pd.DataFrame([it.model_dump() for it in items])

    @staticmethod
    def to_solver_dict(items: Iterable["AppData"]) -> dict[str, dict]:
        return {it.name: {"usage": it.usage, "genre": it.genre} for it in items}
