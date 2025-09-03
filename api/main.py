from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel,HttpUrl
import sqlite3
import asyncio
from datetime import datetime, timezone
from uuid import UUID, uuid4
from furl import furl
from enum import Enum


app = FastAPI()

#Create sqllite database
conn = sqlite3.connect('copilot.db')
cursor = conn.cursor()

#Status enum
class Status(Enum):
    PENDING = "pending"
    PARSED = "parsed"
    ERROR = "error"
    FETCHING = "fetching"
    QUEUED = "queued"

#create a link model with HttpUrl for validation
class LinkIn(BaseModel):
    url: str

#Link out goes into database, carries the analysis status with it
class LinkOut(BaseModel):
    url: str
    id: UUID
    status: str
    created_at: datetime

#Retuyrns health of the app
@app.get("/health")
def health():
    return {"ok":True}

#Root welcome
@app.get("/")
def root():
    return {"message":"Welcome to Apartment Copilot!"}

def canonicalize_url(url):
    f = furl(url)

    #Enforce https for every link
    f.scheme = 'https'
    #lowercase to standardize
    f.host = f.host.lower()

    #Remove the #section parts of url to normalize
    f.fragment = None

    #Remove tracking params
    f.remove(['utm_source', 'utm_medium', 'utm_campaign', 'fbclid'])

    #Remove trailing /
    path_strip = str(f.path).rstrip('/')
    f.path = path_strip

    return f

#user can POST url (make sure valid)
#url gets added to db

@app.post("/link", status_code=201)
async def create_link(payload: LinkIn):
    #await asyncio.sleep(5) :: used to test submit buton disable
    #Checks set for if url is there, BE CAREFUL ths wont persist. Need to find better way with db
    url_string = str(payload.url)
    
    curr_time = datetime.now(timezone.utc)
    rfc_time = curr_time.isoformat(timespec='milliseconds').replace('+00.00','Z')

    curr_uuid = str(uuid4())
    #normalizes url
    normalUrl = str(canonicalize_url(url_string))

    #gets status from status enum
    stat = Status.PENDING
    #db.append(LinkOut(url=str(payload.url), id = uuid4(), status="pending", created_at =rfc_time ))
    #Insert data into sqllite table
    try:
        cursor.execute('''
            INSERT INTO linksubmissions (uuid, url,canon_url, status, created_at)
            VALUES (?, ?, ?, ?, ?) 
            ''', (curr_uuid, url_string, normalUrl,stat.value, rfc_time))
        conn.commit()
    except sqlite3.IntegrityError:  #raise error if there is a unique constrain breach (duplicate link)
        raise HTTPException(status_code= 409, detail="Link Already Submitted!")

    return {"ok":True}

@app.get("/queue")
async def getDb():
    # Sort by most recent time (revrse to display shortest tie first)
    #db.sort(key = lambda x: x.created_at, reverse=True)

    #Query data from sqllite with sorting for display
    cursor.execute('''
        SELECT * FROM linksubmissions ORDER BY created_at DESC
    ''')
    results = cursor.fetchall()

    return {"database": results}


#User gets results
@app.get("/analysis")
async def analyze():
    #Set all items in db to queued
    cursor.execute('''
        UPDATE linksubmissions SET status = ? WHERE status = ?
''', (Status.QUEUED.value, Status.PENDING.value))
    #Mark count of rows updated
    count = cursor.rowcount
    conn.commit()
    
    return {"status":"queued", "count":count}




