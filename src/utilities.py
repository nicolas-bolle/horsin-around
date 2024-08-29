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
    If a point appears twice, both are flagged as Pareto optimal
    FIXME return a Series (really, avoid a list comp)
    """
    return [check_pareto_optimal(df.iloc[i], df) for i in range(len(df))]


def check_pareto_optimal(row: pd.Series, df: pd.DataFrame) -> bool:
    """Given a row of df and the full df, return True if this row is Pareto optimal and False otherwise"""
    # if the point appears at least twice, it's Pareto efficient
    num_appearances = (row == df).all(axis=1).sum()
    if num_appearances > 1:
        return True

    # if the point is weakly dominated by at least 2 rows (itself and at least one other row), it's not Pareto efficient
    num_weak_dominating = (row <= df).all(axis=1).sum()
    if num_weak_dominating > 1:
        return False

    # otherwise it's Pareto efficient
    return True


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
