import csv
import pathlib
from typing import Any


class CSVWriter():

    def __init__(self, filepath: str, header: list[str]) -> None:
        self._filepath = filepath
        self._header = header
        if not pathlib.Path(filepath).exists():
            with open(self._filepath, 'a+', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self._header)
                writer.writeheader()
        # self._file = open(self._filepath, 'a+', newline='')
        # self._writer = csv.DictWriter(self._file, fieldnames=self._header)
        # self._writer.writeheader()
        
    def write_row(self, row: dict[str, Any], autocomplete: bool = True) -> None:
        with open(self._filepath, 'a+', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self._header)
            writer.writerow(row)
        # if autocomplete:
        #     for header in self._header:
        #         if header not in row:
        #             row[header] = '-'
        #self._writer.writerow(row)
    
    def close(self) -> None:
        self._file.close()
