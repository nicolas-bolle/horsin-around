"""Horse management decision functions"""

import numpy as np
import pandas as pd

from src.utilities import (
    flag_pareto_optimal,
    compute_energy,
    compute_centrality,
    permutation_cycle_decomp,
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


def propose_merge(names: list[str], keeps: list[bool], main_zones: list[bool]) -> str:
    """Spell out the moves we should do for a horse merge
    Recommends moves that put the top N horses in Zone 1, where N is the size of Zone 1

    Parameters:
        names (list): names of the horses
        keeps (list): flags for which horses to keep
        main_zones (list): flags of which horses are in the "main" zone

    Returns:
        moves (list): descriptions of actions to take
    """
    assert len(names) == len(
        keeps
    ), f"Lengths {len(names)} and {len(keeps)} don't match"
    assert len(names) == len(
        main_zones
    ), f"Lengths {len(names)} and {len(main_zones)} don't match"
    assert all(
        [isinstance(x, str) for x in names]
    ), f"Names flags must be booleans, instead seeing {names}"
    assert all(
        [isinstance(x, bool) for x in keeps]
    ), f"Keep flags must be booleans, instead seeing {keeps}"
    assert all(
        [isinstance(x, bool) for x in main_zones]
    ), f"Main zone flags must be booleans, instead seeing {main_zones}"

    # check that we can fit all the keepers in the main zone
    assert sum(keeps) <= sum(
        main_zones
    ), f"Unable to fit the {sum(keeps)} in the {sum(main_zones)} main zone slots"

    # pre for making instructions
    df = pd.DataFrame({"name": names, "keep": keeps, "main_zone": main_zones})
    df["instruction_type"] = None
    df["instruction"] = None

    # main zone keepers
    idx = df["main_zone"] & df["keep"]
    df.loc[idx, "instruction_type"] = "keep"

    # main zone killers
    idx = df["main_zone"] & ~df["keep"]
    df.loc[idx, "instruction_type"] = "kill_primary"

    # secondary zone keepers
    idx = ~df["main_zone"] & df["keep"]
    df.loc[idx, "instruction_type"] = "move"

    # secondary zone killers
    idx = ~df["main_zone"] & ~df["keep"]
    df.loc[idx, "instruction_type"] = "kill_secondary"

    # sanity check
    assert df["instruction_type"].isna().sum() == 0

    # add detail to the "move" ones
    idx_to_move = df.query('instruction_type == "move"').index
    idx_to_move_into = df.query('instruction_type == "kill_primary"').index
    assert len(idx_to_move) <= len(
        idx_to_move_into
    ), "If this assert fails, something weird is afoot"
    idx_to_move_into = idx_to_move_into[: len(idx_to_move)]
    for i, j in zip(idx_to_move, idx_to_move_into):
        name_old = df.loc[i, "name"]
        name_new = df.loc[j, "name"]
        df.loc[i, "instruction"] = f"{name_old}: move to {name_new}"

    # add detail to the keeps
    idx = df.query('instruction_type == "keep"').index
    df.loc[idx, "instruction"] = df["name"] + ": keep"

    # add detail to the kills
    idx = df.query('instruction_type in ("kill_primary", "kill_secondary")').index
    df.loc[idx, "instruction"] = df["name"] + ": kill"

    # sanity check
    assert df["instruction"].isna().sum() == 0

    # return the moves
    moves = list(df["instruction"])
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
    # this means the highest rank old name is moved into the highest spot (the highest new name)
    df = pd.DataFrame({"name": names, "rank": ranks})
    names_new = list(df["name"])
    names_old = list(df.sort_values("rank", ascending=True)["name"])
    names_perm_dict = {
        name_old: name_new for name_old, name_new in zip(names_old, names_new)
    }

    # cycle decomp for easier to follow instructions
    names_perm_dicts = permutation_cycle_decomp(names_perm_dict)

    # forming instructions
    moves = []
    for names_perm_dict in names_perm_dicts:
        # ignore horses that don't move
        if len(names_perm_dict) == 1:
            continue

        # special instruction for swaps
        if len(names_perm_dict) == 2:
            name1, name2 = next(iter(names_perm_dict.items()))
            name1, name2 = tuple(sorted([name1, name2]))
            move = f"Swap {name1} and {name2}"
            moves.append(move)
            continue

        # a list of tuples (name_old, name_new)
        # we should stash away the last name_new and then do the moves in reverse order
        cycle = list(names_perm_dict.items())

        name_stash = cycle[-1][1]
        move = f"Stash {name_stash}"
        moves.append(move)

        for name_old, name_new in reversed(cycle):
            if name_old == name_new:
                continue
            move = f"Move {name_old} to {name_new}"
            moves.append(move)

        # rewrite that last instruction
        moves.pop()
        move = f"Move the stashed horse to {name_new}"
        moves.append(move)

    # a bit janky, but just making sure the output definitely looks like a list
    if len(moves) == 0:
        moves = ["No moves recommended"]
    if len(moves) < 2:
        moves.append("")
    return moves
