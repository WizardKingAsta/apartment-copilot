from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel,HttpUrl
from collections import deque
import sqlite3
import asyncio
import json
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4
from furl import furl
from enum import Enum
import requests

from adapters.apartments_dot_com import parse_apartments_items
from adapters.schema import FloorPlan, Unit, ParserResult

#Class to keep track of calls made, diffBot tier allows MAX 5 per minute
class RateLimiter:
    def __init__(self, max_calls=5, time_window = 60):
        self.max_calls = max_calls
        self.time_window - time_window
        self.calls = deque()

    #Function to see how many calls are in the past min
    def can_call_diffBot(self):
        now = time.time()
        #Pop all calls that were more than a minute ago to see how many calls are in the minute
        while self.calls and self.calls[0] <= now-self.time_window:
            self.calls.popleft()
        #return true if the number of calls requested can work
        return len(self.calls)< self.max_calls
    def record_call(self):
        self.calls.append(time.time())



app = FastAPI()

TOKEN = '074c386a7d7b996bef0f1fa190f7f24b'
DIFF_BOT_API=f"https://api.diffbot.com/v3/list?token={TOKEN}"

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

class Popular_Sites(Enum):
    APARTMENTS_DOT_COM = "apartments.com"
    APARTMENT_LIST = "apartmentlist.com"

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

@app.on_event("startup")
async def startup():
    asyncio.create_task(parserLoop())

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

#Function to update status of rows
def update_status(id,status, reason):
    try:
        cursor.execute('''
            UPDATE linksubmissions
                SET status = ?, status_reason = ?
                WHERE id = ?
            ''', (status,reason,id))
        conn.commit()
    except sqlite3.IntegrityError:  #raise error if there is a unique constrain breach (duplicate link)
        raise HTTPException(status_code= 409, detail="Could Not Update Item Staus!") 


    

#RFunction to get all database items that have a status of qeuued
def get_queue():
    try:
        cursor.execute('''
            SELECT * FROM linksubmissions WHERE status= ?  ORDER BY created_at DESC
            ''', (Status.QUEUED.value,))
        conn.commit()
        results = cursor.fetchall()
        return results
    except sqlite3.IntegrityError:  #raise error if there is a unique constrain breach (duplicate link)
        raise HTTPException(status_code= 409, detail="Could Not Fetch Queued Items!") 
    return []

def extract_Apartments_Dot_Com_Json(json):
    #Separates out object and items array from json
    obj = json["objects"][0]
    items = obj["items"]

    parse_apartments_items(items)

    repPrice = None
    rep_beds = None
    rep_baths= None
    rep_sqft = None
    rep_availability = None
    rep_plan_code = None
    #plans = {plans:units}
    return "A.com"

def normalize_Apartment_List(raw):
    return "AList"

#Always working loop to turn queued items into parsed items
async def parserLoop():
    while True:
        #call func for list of db items who are queued
        queuedItems = get_queue()
        for i in range(min(5,len(queuedItems))):
            item = queuedItems[i]
            #update status to fetch
            update_status(item[0], Status.FETCHING.value,"")

            #TODO: fill in parser logic
            #call diff bot api for link style parse
            response = requests.get(f"{DIFF_BOT_API}&url={item[2]}")
            raw = response.json()

            if Popular_Sites.APARTMENTS_DOT_COM.value in item[2]:
                #print(extract_Apartments_Dot_Com_Json(raw))
                print(json.dumps(raw, indent=2))
                #Update status to parsed if no issues arised
                update_status(item[0],Status.PARSED.value, "")
            elif Popular_Sites.APARTMENT_LIST.value in item[2]:
                print(normalize_Apartment_List(raw))
                #Update status to parsed if no issues arised
                update_status(item[0],Status.PARSED.value, "")
            else:
                update_status(item[0],Status.ERROR.value, "Site Not Supported!")
            

        #sleep an wait for more work
        await asyncio.sleep(5)

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




