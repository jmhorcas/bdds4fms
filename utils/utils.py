import os
import subprocess


def get_filepaths(dir: str, extensions_filter: list[str] = []) -> list[str]:
    """Get all filepaths of files with the given extensions from the given directory."""
    filepaths = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not extensions_filter or any(file.endswith(ext) for ext in extensions_filter):
                filepath = os.path.join(root, file)
                filepaths.append(filepath)
    return filepaths


def int2sci(n: int, precision: int = 2) -> str:
    """Convert a large int into scientific notation."""
    if n == 0:
        return '0e0'
    exp = len(str(abs(n))) - 1
    mantissa = n / (10 ** exp)
    return f'{mantissa:.{precision}f}e{exp}'


def float2exp(n: float, precision: int = 2) -> str:
    """Rounds a float to the specified number of decimal places. 
    If the result is 0.0, it returns the number in exponential format.
    """
    rounded = round(n, precision)
    if rounded == 0.0:
        return f"{n:.{precision}e}"
    return f"{rounded}"


def count_configurations(bdd_filepath: str) -> int:
    command = ['../bdds/bin/counter', bdd_filepath]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return int(stdout.strip())
