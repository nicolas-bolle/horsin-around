"""Flask app assigning url requests to functions"""

from ast import literal_eval
from flask import Flask, render_template, request, redirect, url_for

from src.utilities import parse_float, parse_list, parse_dataframe
from src.decisions import get_ranks, propose_merge, propose_reorg

app = Flask(__name__)

def get_inputs():
    """Get the dictionary of inputs from the request
    Janky but good enough for now
    """
    return literal_eval(next(iter(request.values.keys())))

@app.route('/hello_world', methods=['POST'])
def hello_world():
    return 'Hello, World!'

@app.route('/get_ranks', methods=['POST'])
def get_ranks_app():
    """Compute ranks for some horses

    Parameters:
        data_primary (2D list): primary metric values
        cols_primary (list): column names for data_primary
        data_secondary (2D list): secondary metric values
        cols_secondary (list): column names for data_secondary

    Output:
        ranks (str): integer ranks for the horses, from 1 to len(ranks)
            Comma separated
    """
    inputs = get_inputs()
    df_primary = parse_dataframe(inputs['data_primary'], inputs['cols_primary'])
    df_secondary = parse_dataframe(inputs['data_secondary'], inputs['cols_secondary'])

    s_ranks = get_ranks(df_primary, df_secondary)
    s = ','.join(s_ranks.values())

    return s

@app.route('/propose_merge', methods=['POST'])
def propose_merge_app():
    """Spell out the moves we should do for a horse merge
    Recommends moves that put the top N horses in Zone 1, where N is the size of Zone 1

    Parameters:
        names (list): names of the horses
        ranks (list): ranks of the horses
        zones (list): zones (either 1 or 2) of the horses
            Zone 1 is horses in the main population
            Zone 2 is horses in a secondary population

    Output:
        moves (str): description of moves to make
            Comma separated
    """
    inputs = get_inputs()
    names = parse_list(inputs['names'])
    ranks = parse_list(inputs['ranks'])
    zones = parse_list(inputs['zones'])

    moves = propose_merge(names, ranks, zones)
    s = ','.join(moves)

    return s

@app.route('/propose_reorg', methods=['POST'])
def propose_reorg_app():
    """Spell out the moves we should do for a horse reorg
    Recommends moves that give the highest ranked horses the earliest names

    Parameters:
        names (list): names of the horses
        ranks (list): ranks of the horses
    
    Returns:
        moves (str): description of moves to make
            Comma separated
    """
    inputs = get_inputs()
    names = parse_list(inputs['names'])
    ranks = parse_list(inputs['ranks'])

    moves = propose_reorg(names, ranks)
    s = ','.join(moves)

    return s

if __name__ == '__main__':
    app.run(debug=True)
