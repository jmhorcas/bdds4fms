import csv
from typing import Any


class CSVWriter():

    def __init__(self, filepath: str, header: list[str]) -> None:
        self._filepath = filepath
        self._header = header
        self._file = open(self._filepath, 'w', newline='')
        self._writer = csv.DictWriter(self._file, fieldnames=self._header)
        self._writer.writeheader()
        
    def write_row(self, row: dict[str, Any], autocomplete: bool = True) -> None:
        # if autocomplete:
        #     for header in self._header:
        #         if header not in row:
        #             row[header] = '-'
        self._writer.writerow(row)
    
    def close(self) -> None:
        self._file.close()
