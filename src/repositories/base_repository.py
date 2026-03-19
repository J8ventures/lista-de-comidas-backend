from abc import ABC
from utils.dynamodb import get_table


class BaseRepository(ABC):
    def __init__(self):
        self._table = None

    @property
    def table(self):
        if self._table is None:
            self._table = get_table()
        return self._table
