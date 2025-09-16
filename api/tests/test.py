from adapters.schema import FloorPlan, Unit, ParserResult
from adapters.apartments_dot_com import parse_apartments_items
import json
import os

json_folder_path = '/Users/emperormaanav/apartment-copilot/api/tests/test_jsons'

tests = {}

for json_name in os.listdir(json_folder_path):
    path = os.path.join(json_folder_path,json_name)

    with open(path, 'r') as file:
        data = json.load(file)
        tests[json_name] = data

for key, value in tests.items():
    print(f"Test for for {key}:\n")
    objects = tests[key]["objects"][0]
    items = objects["items"]
    units = []
    #if key == "garrison.json":
    plans, units, rep = parse_apartments_items(items)
   
    for el in units:
        #if el.plan_name_ref == 'A1':
        print(el)