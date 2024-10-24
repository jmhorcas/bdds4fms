import os
import argparse
import pathlib
import logging

from flamapy.core.exceptions import FlamaException
from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import UVLReader

from utils.fm_secure_features_names import FMSecureFeaturesNames
from utils.pl_writer import PLWriter


def get_filepaths(dir: str, extensions_filter: list[str] = []) -> list[str]:
    """Get all filepaths of files with the given extensions from the given directory."""
    filepaths = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not extensions_filter or any(file.endswith(ext) for ext in extensions_filter):
                filepath = os.path.join(root, file)
                filepaths.append(filepath)
    return filepaths


def create_mapping_variables_file(mapping_names: dict[str, str], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf8') as f:
        for k, v in mapping_names.items():
            f.write(f'{k},{v}\n')


def create_variables_file(variables: list[str], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf8') as f:
        f.write(' '.join(var for var in variables))


def create_expressions_file(fm: FeatureModel, filepath: str) -> None:
    PLWriter(filepath, fm).transform()


def transform_models(dirpath: str) -> None:
    total_models = 0
    models_with_errors = []
    for fm_filepath in get_filepaths(dirpath, ['uvl']):
        try:
            transform_model(fm_filepath)
            total_models += 1
        except FlamaException:
            print('...syntax error.')
            models_with_errors.append(fm_filepath)

    print(f'{total_models} total models.')
    print(f'{len(models_with_errors)} models with errors:')
    for i, fm_filepath in enumerate(models_with_errors):
        print(f'|-{i}: {fm_filepath}')


def transform_model(fm_filepath: str) -> None:
    path = pathlib.Path(fm_filepath)
    filename = path.stem
    dir = path.parent

    fm = UVLReader(fm_filepath).transform()

    fmsfn = FMSecureFeaturesNames(fm)
    secure_fm = fmsfn.transform()
    mapping_names = fmsfn.mapping_names

    if set(mapping_names.keys()) != set(mapping_names.values()):
        securevars_filepath = str(dir / f'{filename}.securevars')
        create_mapping_variables_file(mapping_names, securevars_filepath)
        
    var_filepath = str(dir / f'{filename}.var')
    exp_filepath = str(dir / f'{filename}.exp')
    create_variables_file(list(mapping_names.values()), var_filepath)
    create_expressions_file(secure_fm, exp_filepath)


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    
    parser = argparse.ArgumentParser(description='UVL2Logic: Transform feature models in UVL format to Logic format accepted by the Logic2BDD tool.')
    parser.add_argument(metavar='path', dest='path', type=str, help='Input feature model (.uvl) or directory with models.')
    args = parser.parse_args()

    if os.path.isdir(args.path):
        transform_models(args.path)
    else:
        transform_model(args.path)