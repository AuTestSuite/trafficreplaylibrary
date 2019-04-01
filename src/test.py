

from trlib import load_json
import json

data = json.load(open("replay-sample.json"))
#print(data)
#dom = DOM_1_0_1.FromJson(data)
dom = load_json(data)

print(dom.sessions)
