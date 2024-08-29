"""Horse management decision functions"""

import numpy as np
import pandas as pd

from src.utilities import flag_pareto_optimal, compute_centrality

# the columns we care about for stats, in order of importance
COLS_PRIMARY = ['speed', 'jump']

# cols to use for tiebreaks
COLS_SECONDARY = ['health']

# how many horses are in each of the zones
N1 = 16
N2 = 8

def get_ranks(df: pd.DataFrame) -> pd.Series:
    """Given a dataframe of points, return the rankings from 1 to len(df)
    Rank according to:
        1. Pareto optimality
        2. Level of "centrality"
        3. Primary attributes (in order)
        4. Secondary attributes (in order)
    """
    # FIXME added these to avoid pandas setting slice warnings but there must be a better way
    df = df.copy() 

    # flag Pareto optimal points
    df['pareto_optimal'] = flag_pareto_optimal(df[COLS_PRIMARY])

    # compute centrality scores
    df['centrality'] = df[COLS_PRIMARY].apply(compute_centrality, axis=1)

    # rank (higher values are better)
    cols_ranking = ['pareto_optimal', 'centrality'] + COLS_PRIMARY + COLS_SECONDARY
    df['rank'] = df[cols_ranking].apply(tuple, axis=1).rank(method='first', ascending=False).astype(int)

    return df['rank']

def get_keep_recs(df: pd.DataFrame)-> pd.Series:
    """Given a dataframe of points, return bools for whether we should keep points
    Flags 16 points as True, the rest as False
    Return the top 16 most preferred points
    Note: returning duplicate points is OK
    """
    df = df.copy()

    # rank points
    df['rank'] = get_ranks(df)

    # flag which to keep
    df['keep_rec'] = df['rank'] <= N1

    return df['keep_rec']

def propose_merge(df1: pd.DataFrame, df2: pd.DataFrame) -> str:
    """Recommend the rearrangements we should do for a horse merge"""
    # prep
    df1 = df1.copy()
    df2 = df2.copy()
    assert len(df1) == N1
    assert len(df2) == N2
    df1['zone'] = 1
    df2['zone'] = 2
    df = pd.concat([df1, df2])

    # recommend which horses to keep
    df['keep_rec'] = get_keep_recs(df)

    # propose how to move them
    names_kill = list(df.query('zone == 1 and ~keep_rec')['name'])
    names_move = list(df.query('zone == 2 and keep_rec')['name'])
    assert len(names_kill) == len(names_move)

    merges = []
    for name_kill, name_move in zip(names_kill, names_move):
        merge = f'Kill {name_kill} and replace it with {name_move}'
        merges.append(merge)

    if len(merges) == 0:
        return 'No merges recommended'
    else:
        return '\n'.join(merges)

def propose_reorg(df1: pd.DataFrame) -> str:
    """Recommend the rearrangements we should do for a horse reorg
    FIXME improvement: list moves in digraph cycle order (for each connected component) to streamline execution
    """
    df1 = df1.copy()

    assert len(df1) == N1
    df1['rank'] = get_ranks(df1)
    
    names_old = list(df1['name'])
    names_new = list(df1.sort_values('rank', ascending=False)['name'])

    moves = []
    for name_old, name_new in zip(names_old, names_new):
        move = f'Move {name_new} to {name_old}'
        moves.append(move)

    if len(moves) == 0:
        return 'No moves recommended'
    else:
        return '\n'.join(moves)
