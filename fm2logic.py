import pathlib

from flamapy.metamodels.fm_metamodel.models import FeatureModel

from utils.fm_secure_features_names import FMSecureFeaturesNames
from utils.pl_writer import PLWriter


def create_mapping_variables_file(mapping_names: dict[str, str], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf8') as f:
        for k, v in mapping_names.items():
            f.write(f'{k},{v}\n')


def create_variables_file(variables: list[str], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf8') as f:
        f.write(' '.join(var for var in variables))


def create_expressions_file(fm: FeatureModel, filepath: str) -> None:
    PLWriter(filepath, fm).transform()


def fm2logic(fm_filepath: str, fm: FeatureModel) -> tuple[str, str, str]:
    """Transform a FM into logic.
    
    Return the var and exp files, and optionally the securevars file.
    """
    path = pathlib.Path(fm_filepath)
    filename = path.stem
    dir = path.parent

    fmsfn = FMSecureFeaturesNames(fm)
    secure_fm = fmsfn.transform()
    mapping_names = fmsfn.mapping_names
    securevars_filepath = None
    
    if set(mapping_names.keys()) != set(mapping_names.values()):
        securevars_filepath = str(dir.parent / f'logic/{filename}.securevars')
        create_mapping_variables_file(mapping_names, securevars_filepath)
        
    var_filepath = str(dir.parent / f'logic/{filename}.var')
    exp_filepath = str(dir.parent / f'logic/{filename}.exp')
    create_variables_file(list(mapping_names.values()), var_filepath)
    create_expressions_file(secure_fm, exp_filepath)
    return (var_filepath, exp_filepath, securevars_filepath)
