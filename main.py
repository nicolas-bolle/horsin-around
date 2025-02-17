"""Flask app assigning url requests to functions"""

from google.cloud import secretmanager

from ast import literal_eval
from flask import Flask, render_template, request, redirect, url_for

from src.utilities import parse_float, parse_int, parse_str, parse_list, parse_dataframe
from src.decisions import get_ranks, propose_merge, propose_reorg

app = Flask(__name__)

# retrieve password value from the secret
PASSWORD_SECRET_VERSION_NAME = "projects/121809867862/secrets/password/versions/latest"
client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(request={"name": PASSWORD_SECRET_VERSION_NAME})
PASSWORD = response.payload.data.decode("UTF-8")


def get_inputs():
    """Get the dictionary of inputs from the request
    Janky but good enough for now
    """
    s = next(iter(request.values.keys()))
    try:
        return literal_eval(s)
    except:
        assert False, f"Failed to eval {s}"


@app.route("/hello_world", methods=["POST"])
def hello_world():
    return "Hello, World!"


@app.route("/get_ranks", methods=["POST"])
def get_ranks_app():
    """Compute ranks for some horses

    Parameters:
        data_primary (2D list): primary metric values
        cols_primary (list): column names for data_primary
        data_secondary (2D list): secondary metric values
        cols_secondary (list): column names for data_secondary

    Output:
        ranks (str): integer ranks for the horses, from 1 to len(ranks)
            Semicolon delimited
    """
    inputs = get_inputs()
    password = parse_str(inputs["password"])
    if check_password(password):
        df_primary = parse_dataframe(
            inputs["data_primary"], inputs["cols_primary"], "float"
        )
        df_secondary = parse_dataframe(
            inputs["data_secondary"], inputs["cols_secondary"], "float"
        )

        s_ranks = get_ranks(df_primary, df_secondary)
        s = ";".join(s_ranks.astype(str))

        return s


@app.route("/propose_merge", methods=["POST"])
def propose_merge_app():
    """Spell out the moves we should do for a horse merge
    Recommends moves that put the top N horses in Zone 1, where N is the size of Zone 1

    Parameters:
        names (list): names of the horses
        keeps (list): flags for which horses to keep
        main_zones (list): flags of which horses are in the "main" zone

    Output:
        moves (str): description of actions to make
            Semicolon delimited
    """
    inputs = get_inputs()
    password = parse_str(inputs["password"])
    if check_password(password):
        names = parse_list(inputs["names"], "str")
        keeps = parse_list(inputs["keeps"], "bool")
        main_zones = parse_list(inputs["main_zones"], "bool")

        moves = propose_merge(names, keeps, main_zones)
        s = ";".join(moves)

        return s


@app.route("/propose_reorg", methods=["POST"])
def propose_reorg_app():
    """Spell out the moves we should do for a horse reorg
    Recommends moves that give the highest ranked horses the earliest names

    Parameters:
        names (list): names of the horses
        ranks (list): ranks of the horses

    Returns:
        moves (str): description of moves to make
            Semicolon delimited
    """
    inputs = get_inputs()
    password = parse_str(inputs["password"])
    if check_password(password):
        names = parse_list(inputs["names"], "str")
        ranks = parse_list(inputs["ranks"], "int")

        moves = propose_reorg(names, ranks)
        s = ";".join(moves)

        return s


def check_password(password):
    """Check the password is right"""
    return password == PASSWORD


if __name__ == "__main__":
    app.run(debug=True)
