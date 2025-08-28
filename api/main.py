from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,HttpUrl
import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4

app = FastAPI()

#create a link model with HttpUrl for validation
class LinkIn(BaseModel):
    url: str

#Link out goes into database, carries the analysis status with it
class LinkOut(BaseModel):
    url: str
    id: UUID
    status: str
    created_at: datetime
submittedLinks = set()
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
async def create_link(payload: LinkIn):
    #await asyncio.sleep(5) :: used to test submit buton disable
    if str(payload.url) in submittedLinks:
        raise HTTPException(status_code=409, detail="Link Already Submitted!")
    curr_time = datetime.now(timezone.utc)
    rfc_time = curr_time.isoformat(timespec='milliseconds').replace('+00.00','Z')
    db.append(LinkOut(url=str(payload.url), id = uuid4(), status="pending", created_at =rfc_time ))
    submittedLinks.add(str(payload.url))
    return {"ok":True}

@app.get("/queue")
async def getDb():
    # Sort by most recent time
    db.sort(key = lambda x: x.created_at, reverse=True)
    return {"database": list(db)}


#User gets results
@app.get("/analysis")
def analyze():
    #Fill in future with chat gpt or calude wrapper
    res = {}
    for item in db:
        res[item["url"]]="GOOD"
    return res




