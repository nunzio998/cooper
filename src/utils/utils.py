import json


# Funzione per leggere la configurazione dal file JSON
def read_json(path) -> dict:
    with open(path, 'r') as file:
        return json.load(file)