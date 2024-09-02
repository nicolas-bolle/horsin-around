"""Utility functions"""

import numpy as np
import pandas as pd


def parse_float(x: float | str) -> float:
    """Parse an input as a float in [0, 1], whether it's a float or a string"""
    if isinstance(x, str):
        assert x.endswith("%"), f"Error parsing {x} as float"
        return float(x.replace("%", "")) / 100
    else:
        return float(x)


def parse_int(x: int | float | str) -> int:
    """Parse an input as an int"""
    return int(x)


def parse_str(x) -> str:
    """Parse an input as a str"""
    return str(x)


def parse_bool(x) -> bool:
    """Parse an input as a bool"""
    return bool(x)


def parse_list(x, _type: str) -> list:
    """Parse an input as a list, with the specified type
    Really just flattening the list if necessary
    """
    match _type:
        case "float":
            parser = parse_float
        case "int":
            parser = parse_int
        case "str":
            parser = parse_str
        case "bool":
            parser = parse_bool
        case _:
            assert False, f"Unknown type specification {_type}"
    return [parser(t) for t in np.array(x).flatten()]


def parse_dataframe(
    data: list[list], cols: list, types: None | str | dict = None
) -> pd.DataFrame:
    """Parse an input as a pd.DataFrame"""
    cols = parse_list(cols, "str")
    assert len(cols) == len(
        data[0]
    ), f"Lengths {len(cols)} and {len(data[0])} don't match"

    # types for columns
    if types is None:
        types = "float"
    if isinstance(types, str):
        types = {col: types for col in cols}

    df = pd.DataFrame(data=data, columns=cols)
    for col, _type in types.items():
        df[col] = parse_list(df[col].values, _type)

    return df


def flag_pareto_optimal(df: pd.DataFrame) -> list:
    """Given a dataframe with numeric columns, return a list of bools flagging Pareto optimality
    Not the fasteset implementation, but it's readable
    """
    _df = df.drop_duplicates()
    return df.apply(lambda row: _check_pareto_optimal(row, _df), axis=1)


def _check_pareto_optimal(row: pd.Series, df: pd.DataFrame) -> bool:
    """Given a row of df and the full df (with duplicates dropped), return True if this row is Pareto optimal and False otherwise
    So the row is not Pareto efficient iff it is (weakly) dominated by at least 2 rows (one of them being itself)
    """
    num_weak_dominating = (row <= df).all(axis=1).sum()
    return num_weak_dominating == 1


def compute_energy(x) -> float:
    """Compute an "energy" score for the input vector x
    It's just the l1 norm
    """
    x = np.array(x)
    return np.sum(x)


def compute_centrality(x) -> float:
    """Compute a "centrality" score in the range [-1, 1] for the input vector x
    1 for pointing in the [1, ..., 1] direction
    -1 for pointing in the [-1, ..., -1] direction
    """
    x = np.array(x)
    x0 = np.ones(len(x))

    x = x / np.linalg.norm(x)
    x0 = x0 / np.linalg.norm(x0)

    return float(np.dot(x, x0))


def permutation_cycle_decomp(perm_dict: dict) -> dict:
    """Given a permutation dictionary, convert it to a list of dictionaries where each one is in cycle order
    "Cycle order" is that the value of one is the key of the next, like {1: 3, 3: 2, 2: 1}
    Relies on the fact that python 3.6+ maintains insertion order
    """
    # confirm this actually represents a permutation
    assert set(perm_dict.keys()) == set(
        perm_dict.values()
    ), f"Keys {perm_dict.keys()} and values {perm_dict.values()} are not the same set"

    perm_dict = perm_dict.copy()
    perm_dicts_new = []
    perm_dict_new = {}
    perm_dicts_new.append(perm_dict_new)

    node = next(iter(perm_dict.keys()))

    # transfer mappings into perm_dict_new until perm_dict is depleted
    while perm_dict:
        if node in perm_dict:
            # we haven't transferred over this node's mapping, so transfer it
            node_new = perm_dict[node]
            perm_dict_new[node] = node_new
            del perm_dict[node]

            # move to the next node in the cycle
            node = node_new

        else:
            # we've already transferred it, meaning we just completed a cycle
            # so start a new cycle
            perm_dict_new = {}
            perm_dicts_new.append(perm_dict_new)

            # with a fresh node
            node = next(iter(perm_dict.keys()))

    return perm_dicts_new
