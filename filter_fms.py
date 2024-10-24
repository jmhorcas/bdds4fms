import os
import argparse
import pathlib
import logging
from collections import defaultdict

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter


OUTPUT_PATH = pathlib.Path('uvl')


def get_filepaths(dir: str, extensions_filter: list[str] = []) -> list[str]:
    """Get all filepaths of files with the given extensions from the given directory."""
    filepaths = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not extensions_filter or any(file.endswith(ext) for ext in extensions_filter):
                filepath = os.path.join(root, file)
                filepaths.append(filepath)
    return filepaths


def filter_models(dirpath: str) -> None:
    total_models = 0
    models_with_errors = []
    for i, fm_filepath in enumerate(get_filepaths(dirpath, ['uvl'])):
        print(f'{i}: {fm_filepath}', end='', flush=True)
        path = pathlib.Path(fm_filepath)
        filename = path.stem
        try:
            fm = UVLReader(fm_filepath).transform()
            new_filepath = str(OUTPUT_PATH / f'{filename}.uvl')
            UVLWriter(new_filepath, fm).transform()
            print()
            total_models += 1
        except FlamaException:
            print('...syntax error.')
            models_with_errors.append(fm_filepath)
    print(f'{total_models} total models.')
    print(f'{len(models_with_errors)} models with errors:')
    for i, fm_filepath in enumerate(models_with_errors):
        print(f'|-{i}: {fm_filepath}')
    

if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    
    parser = argparse.ArgumentParser(description=f'Filter feature models of a dir by coping it to {OUTPUT_PATH} folder and avoiding duplicates.')
    parser.add_argument(metavar='path', dest='path', type=str, help='Input directory with models.')
    args = parser.parse_args()

    filter_models(args.path)