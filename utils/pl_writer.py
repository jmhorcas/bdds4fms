import re
import itertools
from enum import Enum

from flamapy.core.models.ast import ASTOperation
from flamapy.core.transformations import ModelToText
from flamapy.metamodels.fm_metamodel.models import FeatureModel, Feature, Relation, Constraint


class PLWriter(ModelToText):
    """Propositional logic writer for feature models.
    
    It transforms the feature tree of the feature model into a propositional logic formula,
    while maintaining the original constraints that are already in propositional logic.

    Typed features and multi-features are considered as simple (boolean) features.
    Arithmetic, and other complex constraints are ommited, and thus, eliminated from the output.
    """

    class LogicConnective(Enum):
        NOT = 'not'
        OR = 'or'
        AND = 'and'
        IMPLIES = '->'
        EQUIVALENCE = '<->'
        XOR = 'XOR'
        MUX = 'MUX'

    @staticmethod
    def get_destination_extension() -> str:
        return 'exp'

    def __init__(self, path: str, source_model: FeatureModel):
        self.path: str = path
        self.source_model: FeatureModel = source_model

    def transform(self) -> str:
        expressions = to_exp(self.source_model)
        expressions_str = '\n'.join(expressions) + '\n'
        if self.path is not None:
            with open(self.path, 'w', encoding='utf8') as file:
                file.write(expressions_str)
        return expressions_str


def to_exp(feature_model: FeatureModel) -> list[str]:
    """Traverse the feature tree and constraints and return a list of propositional formulas."""
    if feature_model is None or feature_model.root is None:
        return []
    
    formulas: list[str] = []
    formulas.append(feature_model.root.name)  # The root is always present
    features: list[Feature] = []
    features.append(feature_model.root)
    while features:
        feature = features.pop()
        for relation in feature.get_relations():
            formulas.append(get_relation_formula(relation))
            features.extend(relation.children)
    for constraint in feature_model.get_constraints():
        formulas.append(get_constraint_formula(constraint))
    return formulas


def get_relation_formula(relation: Relation) -> str:
    result = ''
    if relation.is_mandatory():
        result = get_mandatory_formula(relation)
    elif relation.is_optional():
        result = get_optional_formula(relation)
    elif relation.is_or():
        result = get_or_formula(relation)
    elif relation.is_alternative():
        result = get_alternative_formula(relation)
    elif relation.is_mutex():
        result = get_mutex_formula(relation)
    elif relation.is_cardinal():
        result = get_cardinality_formula(relation)
    return result


def get_mandatory_formula(relation: Relation) -> str:
    parent = relation.parent.name
    child = relation.children[0].name
    return f'{parent} {PLWriter.LogicConnective.EQUIVALENCE.value} {child}'


def get_optional_formula(relation: Relation) -> str:
    parent = relation.parent.name
    child = relation.children[0].name
    return f'{child} {PLWriter.LogicConnective.IMPLIES.value} {parent}'


def get_or_formula(relation: Relation) -> str:
    parent = relation.parent.name
    children = f" {PLWriter.LogicConnective.OR.value} ".join(child.name for child in relation.children)
    return f'{parent} {PLWriter.LogicConnective.EQUIVALENCE.value} ({children})'


def get_alternative_formula(relation: Relation) -> str:
    formula = []
    parent = relation.parent.name
    children = {child.name for child in relation.children}
    for child in children:
        children_negatives = children - {child}
        formula.append(f'{child} {PLWriter.LogicConnective.EQUIVALENCE.value} '
                       f'({f" {PLWriter.LogicConnective.AND.value} ".join(f"{PLWriter.LogicConnective.NOT.value} " + ch for ch in children_negatives)} '
                           f'{PLWriter.LogicConnective.AND.value} {parent})')
    return f" {PLWriter.LogicConnective.AND.value} ".join(f'({f})' for f in formula)


def get_mutex_formula(relation: Relation) -> str:
    formula = []
    parent = relation.parent.name
    children = {child.name for child in relation.children}
    for child in children:
        children_negatives = children - {child}
        formula.append(f'{child} {PLWriter.LogicConnective.EQUIVALENCE.value} '
                       f'({f" {PLWriter.LogicConnective.AND.value} ".join(f"{PLWriter.LogicConnective.NOT.value} " + cn for cn in children_negatives)} '
                           f'{PLWriter.LogicConnective.AND.value} {parent})')
    formula_str = f" {PLWriter.LogicConnective.AND.value} ".join(f'({f})' for f in formula)
    return f'({parent} {PLWriter.LogicConnective.EQUIVALENCE.value} ' \
        f'{PLWriter.LogicConnective.NOT.value} ({f" {PLWriter.LogicConnective.OR.value} ".join(child for child in children)})) {PLWriter.LogicConnective.OR.value} ({formula_str})'


def get_cardinality_formula(relation: Relation) -> str:
    parent = relation.parent.name
    children = {child.name for child in relation.children}
    or_ctc = []
    for k in range(relation.card_min, relation.card_max + 1):
        combi_k = list(itertools.combinations(children, k))
        for positives in combi_k:
            negatives = children - set(positives)
            positives_and_ctc = f'{f" {PLWriter.LogicConnective.AND.value} ".join(positives)}'
            negatives_and_ctc = f'{f" {PLWriter.LogicConnective.AND.value} ".join(f"{PLWriter.LogicConnective.NOT.value} " + f for f in negatives)}'
            if positives_and_ctc and negatives_and_ctc:
                and_ctc = f'{positives_and_ctc} {PLWriter.LogicConnective.AND.value} {negatives_and_ctc}'
            else:
                and_ctc = f'{positives_and_ctc}{negatives_and_ctc}'
            or_ctc.append(and_ctc) 
    formula_or_ctc = f'{f" {PLWriter.LogicConnective.OR.value} ".join(or_ctc)}'
    return f'{parent} {PLWriter.LogicConnective.EQUIVALENCE.value} {formula_or_ctc}'


def get_constraint_formula(ctc: Constraint) -> str:
    constraint_str = ctc.ast.pretty_str()
    constraint_str = re.sub(rf"\b{ASTOperation.XOR.value}\b", 
                            PLWriter.LogicConnective.XOR.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.NOT.value}\b", 
                            PLWriter.LogicConnective.NOT.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.AND.value}\b", 
                            PLWriter.LogicConnective.AND.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.OR.value}\b", 
                            PLWriter.LogicConnective.OR.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.IMPLIES.value}\b", 
                            PLWriter.LogicConnective.IMPLIES.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.EQUIVALENCE.value}\b", 
                            PLWriter.LogicConnective.EQUIVALENCE.value, constraint_str)
    constraint_str = re.sub(rf"\b{ASTOperation.REQUIRES.value}\b", 
                            PLWriter.LogicConnective.IMPLIES.value, constraint_str)
    constraint_str = re.sub(
        rf"\b{ASTOperation.EXCLUDES.value}\b",
        f'{PLWriter.LogicConnective.IMPLIES.value} {PLWriter.LogicConnective.NOT.value}',
        constraint_str
    )
    return constraint_str
