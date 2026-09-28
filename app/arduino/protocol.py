import json

def parse_weight_message(message):
    data=json.loads(message)
    return data.get("cells", [])
