"""Horse management decision functions"""

import numpy as np
import pandas as pd

from src.utilities import (
    flag_pareto_optimal,
    compute_energy,
    compute_centrality,
    cycle_reorder_perm_dict,
)


def get_ranks(df_primary: pd.DataFrame, df_secondary: pd.DataFrame) -> pd.Series:
    """Given dataframes of primary and secondary criteria, return the rankings from 1 to len(df)
    Rank according to:
        1. Pareto optimality
        2. Energy (l1 norm)
        3. Level of "centrality"
        4. Primary attributes (in order)
        5. Secondary attributes (in order)
    """
    assert (
        df_primary.index == df_secondary.index
    ).all(), f"Indexes {df_primary.index} and {df_secondary.index} not equal"
    assert (
        len(set(df_primary.columns) & set(df_secondary.columns)) == 0
    ), f"Cols {df_primary.columns} and {df_secondary.columns} overlap"

    df = df_primary.join(df_secondary)

    # flag Pareto optimal points
    df["pareto_optimal"] = flag_pareto_optimal(df_primary)

    # compute energies
    df["energy"] = df_primary.apply(compute_energy, axis=1)

    # compute centrality scores
    df["centrality"] = df_primary.apply(compute_centrality, axis=1)

    # rank (higher values are better)
    cols_ranking = (
        ["pareto_optimal", "energy", "centrality"]
        + list(df_primary.columns)
        + list(df_secondary.columns)
    )
    df["rank"] = (
        df[cols_ranking]
        .apply(tuple, axis=1)
        .rank(method="first", ascending=False)
        .astype(int)
    )

    return df["rank"]


def propose_merge(names: list, ranks: list, zones: list) -> str:
    """Spell out the moves we should do for a horse merge
    Recommends moves that put the top N horses in Zone 1, where N is the size of Zone 1

    Parameters:
        names (list): names of the horses
        ranks (list): ranks of the horses
        zones (list): zones (either 1 or 2) of the horses
            Zone 1 is horses in the main population
            Zone 2 is horses in a secondary population

    Returns:
        moves (list): descriptions of moves to make
    """
    assert len(names) == len(
        ranks
    ), f"Lengths {len(names)} and {len(ranks)} don't match"
    assert len(names) == len(
        zones
    ), f"Lengths {len(names)} and {len(zones)} don't match"
    assert (
        len(set(zones) - {1, 2}) == 0
    ), f"Zones must be either 1 or 2, seeing {set(zones)}"
    assert set(ranks) == set(
        range(1, len(ranks) + 1)
    ), f"Ranks must be the numbers 1 to len(ranks), instead seeing {ranks}"

    # decide which horses to keep
    df = pd.DataFrame({"name": names, "rank": ranks, "zone": zones})
    N = (df["zone"] == 1).sum()
    df["keep"] = df["rank"] <= N

    # figure out which horses to move
    names_kill = list(df.query("zone == 1 and ~keep")["name"])
    names_move = list(df.query("zone == 2 and keep")["name"])
    assert (
        len(names_kill) == len(names_move)
    ), f"Sanity check failed, this is a weird error, {len(names_kill)}, {len(names_move)}"

    # write out the moves
    moves = []
    for name_kill, name_move in zip(names_kill, names_move):
        move = f"Kill {name_kill} and replace it with {name_move}"
        moves.append(move)

    if len(moves) == 0:
        return ["No moves recommended"]
    else:
        return moves


def propose_reorg(names: list, ranks: list) -> str:
    """Spell out the moves we should do for a horse reorg
    Recommends moves that give the highest ranked horses the earliest names

    Parameters:
        names (list): names of the horses
        ranks (list): ranks of the horses

    Returns:
        moves (list): descriptions of moves to make
    """
    assert len(names) == len(
        ranks
    ), f"Lengths {len(names)} and {len(ranks)} don't match"
    assert set(ranks) == set(
        range(1, len(ranks) + 1)
    ), f"Ranks must be the numbers 1 to len(ranks), instead seeing {ranks}"

    # get the name reordering
    # "new" names are the names as-is, presuming the 1st spot is intended for the best horse
    # "old" names are the names in ascending rank
    # this means the 1st old name is moved into the highest spot (the 1st new name)
    df = pd.DataFrame({"name": names, "rank": ranks})
    names_new = list(df["name"])
    names_old = list(df.sort_values("rank", ascending=True)["name"])
    names_perm_dict = {
        name_old: name_new for name_old, name_new in zip(names_old, names_new)
    }
    names_perm_dict = cycle_reorder_perm_dict(names_perm_dict)

    moves = []
    for name_old, name_new in names_perm_dict.items():
        if name_old == name_new:
            continue
        move = f"Move {name_old} to {name_new}"
        moves.append(move)

    if len(moves) == 0:
        return ["No moves recommended"]
    else:
        return moves
