from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()

#Pydantic item model
class Item(BaseModel):
    text: str = None
    is_done: bool = False
#Model cannot accept params in request, it expects it in JSON payload of the request
#Send in JSON load with -d '{"param":"val"}'
items = []


@app.get("/")
# HTTP get method, inside is the path .
# Essentially when someone visits path, the function below is called.
def root():
    return {"HELLO":"GANG"}
#Call uvicorn main:app --reload to refresh every time you save a change

#Routes are the /user or /maanav that specify where to go
@app.post("/items")
#HTTP post request, data sent to serve to create or update info
def create(item: Item):
    items.append(item)
    return items
# Call curl -X POST -H "Content-Type: application/json" 'link(path)?item=value' -> 'http://127.0.0.1:8000/items?item=apple' (SEPERATE TERMINAL)

@app.get("/items/{item_id}", response_model = Item) #Response tells server to expect Item model from this API end point

def get_item(item_id: int)->Item:
    if item_id<len(items):
        return items[item_id]
    else:
        raise HTTPException(status_code = 404, detail=f"Item {item_id} not found")
        #If the item is not vaid raise exception. Use raise HTTP exception and the universal codes for any possible error points
    
#Call curl -X GET http://127.0.0.1:8000/items/0 to access

@app.get("/items")

def item_list(limit: int=10):
    return items[0:limit]

#for functino params use '?param=val'


#Gather url 

# add it to database
