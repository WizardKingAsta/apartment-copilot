from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,HttpUrl
from uuid import uuid4

app = FastAPI()

#create a link model with HttpUrl for validation
class LinkIn(BaseModel):
    url: str

#Link out goes into database, carries the analysis status with it
class LinkOut(BaseModel):
    url: str
    status: str

db = []

#Retuyrns health of the app
@app.get("/health")
def health():
    return {"ok":True}

#Root welcome
@app.get("/")
def root():
    return {"message":"Welcome to Apartment Copilot!"}

#user can POST url (make sure valid)
#url gets added to db

@app.post("/link", status_code=201)
def create_link(payload: LinkIn):
    db.append(LinkOut(url=str(payload.url), status="pending"))
    return {"ok":True}

@app.get("/queue")
def itemizeDB():
    return {"database": db}


#User gets results
@app.get("/analysis")
def analyze():
    #Fill in future with chat gpt or calude wrapper
    res = {}
    for item in db:
        res[item["url"]]="GOOD"
    return res




