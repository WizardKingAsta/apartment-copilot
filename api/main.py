from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel,HttpUrl
from collections import deque
from typing import Dict, List
import sqlite3
import asyncio
import json
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4
from furl import furl
from enum import Enum
import numpy as np
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

APARTMENT_CONSTRAINTS={
    "min_sqft": 0,
    "max_sqft": 4000,
    "min_rent": 300,
    "max_rent": 7000,
    "min_beds": 0.0,
    "max_beds": 3,
    "min_baths": 0.5,
    "max_baths": 4.0,
    "move_in": datetime.strptime('2025-10-22', '%Y-%m-%d').date()
}

#Default weights
WEIGHTS={ 
    "w_price":0.5,
    "w_sqft": 0.3,
    "w_avail": 0.05,
    # TODO: go into apartments parser and add more unique feature (pets, pool etc) to be used in this part of the formula
    "w_flags":0.15
        
}

link_count = 0

PRICE_SCALE = max(0.2*APARTMENT_CONSTRAINTS["max_rent"],600)
SQFT_SCALE = max(0.2*APARTMENT_CONSTRAINTS["min_sqft"],150)
TAU_DAYS=14

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

def rank_units():

    return 5

#FUNCTION to applu simple scorig formula based on weight and current unit.
def score_unit(unit_price, unit_sqft, unit_avail):
    #Evaluate price number
    price_u = ((APARTMENT_CONSTRAINTS["max_rent"]-unit_price)/ PRICE_SCALE)
    #scale it between 0 and 1
    price_u = np.clip(price_u, 0,1)

    #evaluate sqft number
    sqft_u = ((unit_sqft-APARTMENT_CONSTRAINTS["min_sqft"])/SQFT_SCALE)
    #scale sqft between 0 and 1
    sqft_u = np.clip(sqft_u, 0,1)

    flags_u = 0.5

    #Calculate days after move in the apartment is available
    days_post_move_in = (unit_avail-APARTMENT_CONSTRAINTS["move_in"]).days
    #Cacluate decay based on how long we must wait until we can move that is AFTER move in day
    avail_u = (np.exp(-max(0, days_post_move_in))/TAU_DAYS)

    return WEIGHTS["w_price"]*price_u + WEIGHTS["w_sqft"]*sqft_u + WEIGHTS["w_flags"]*flags_u + WEIGHTS["w_avail"]*avail_u

#Function intakes all units list and dictionary of floor plans to minimze the units to ones that fit insde user constaints (ie. correct num beds, sq ft, price etc)
def filter_units(floor_plans: Dict[str, FloorPlan], units: List[Unit]):
    filtered_units_final = []

    for unit in units:
        plan = floor_plans[unit.plan_name_ref] if unit.plan_name_ref in floor_plans else None

        #checks if date is present, Turn date into usable datetime obj for math
        if (unit.availability_date is not None) and type(unit.availability_date) == str:
            unit.availability_date = datetime.strptime(unit.availability_date, '%Y-%m-%d').date()

        #Check if unit and plan are fully populated, and important factors fall within constraints
        if (plan and ((unit.price is not None) and APARTMENT_CONSTRAINTS["min_rent"]<=unit.price<=APARTMENT_CONSTRAINTS["max_rent"]) 
            and ((unit.sqft is not None) and APARTMENT_CONSTRAINTS["min_sqft"]<=unit.sqft<= APARTMENT_CONSTRAINTS["max_sqft"])
            and ((plan.beds is not None) and (APARTMENT_CONSTRAINTS["min_beds"]<=plan.beds<= APARTMENT_CONSTRAINTS["max_beds"]))
            and ((plan.baths is not None) and APARTMENT_CONSTRAINTS["min_baths"]<=plan.baths<= APARTMENT_CONSTRAINTS["max_baths"])
            and ((unit.availability_date is not None) and (APARTMENT_CONSTRAINTS["move_in"]>= unit.availability_date))):
            unit_score = score_unit(unit.price, unit.sqft, unit.availability_date)
            if unit_score<0 or unit_score>1:
                print("ERROR, invalid score")
            else:
                filtered_units_final.append((unit, plan, unit_score))
    #return all untis that fit in preference bounds with their score
    return filtered_units_final


def extract_Apartments_Dot_Com_Json(json):
    #Error check:
    if not json: 
        print("Error: No Json")
        return []
    if 'objects'not in json:
        print("Error: no Objects")
        print(json)
        return json
    #Separates out object and items array from json
    obj = json["objects"][0]
    items = obj["items"]

    #set to dedupe
    seen = set()

    #Dictionary
    floor_plans = {}

    #Use apartment.com parser to get lists of floor plans and units
    plans, units, report = parse_apartments_items(items)
    
    #Iterate through floor plans and add to dictionary 
    for plan in plans:
        if plan.plan_name and plan.plan_name not in floor_plans:
            floor_plans[plan.plan_name] = plan

    #print the title of the current apartment complex
    #print(obj["title"]+"\n\n")

    filtered_units = filter_units(floor_plans, units)

    return filtered_units
masterList = []
#keep track of links to process
total_link_count = 0

def normalize_Apartment_List(raw):
    return "AList"

#Always working loop to turn queued items into parsed items
async def parserLoop():
    global total_link_count, masterList
    while True:
        #call func for list of db items who are queued
        queuedItems = get_queue()
        for i in range(min(5,len(queuedItems))):
            item = queuedItems[i]
            #update status to fetch
            update_status(item[0], Status.FETCHING.value,"")


            #call diff bot api for link style parse
            response = requests.get(f"{DIFF_BOT_API}&url={item[2]}&fields=items(summary,mortar-wrapper,unitColumn,pricingColumn,sqftColumn,availableColumn,availableColumnInnerContainer,title,date)")
            raw = response.json()
            if not raw:
                update_status(item[0],Status.ERROR.value, "DIffBot did not Parse")

            if Popular_Sites.APARTMENTS_DOT_COM.value in item[2]:
                res = extract_Apartments_Dot_Com_Json(raw)
                #If result is an array append it
                #print(type(res)) USED TO TEST RETURN TYPE TO TRACK DOWN IF ERROR IS IN FILTER OR PARSER
                if res and type(res) == list:
                    masterList.append(res.copy())
                    total_link_count-=1

                        #Update status to parsed if no issues arised
                    update_status(item[0],Status.PARSED.value, "")
                elif res == []:
                    # TODO: Go into parser and handle jsons that return reviews, and sites that dont pick up single or double units
                    total_link_count-=1
                    update_status(item[0],Status.ERROR.value, "Link Did Not Return Any Open Listings")
                elif res and 'error' in res:
                    total_link_count-=1
                    update_status(item[0],Status.ERROR.value, res['error'])
                #IF all links parsed print the master list to view
                if total_link_count<1:
                    for i,l in enumerate(masterList):
                        print(f"{i}: {l}\n\n")
                
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
    global total_link_count, masterList
    #Set all items in db to queued
    cursor.execute('''
        UPDATE linksubmissions SET status = ? WHERE status = ?
''', (Status.QUEUED.value, Status.PENDING.value))
    #Mark count of rows updated
    count = cursor.rowcount
    conn.commit()
    total_link_count = count
    masterList = []
    return {"status":"queued", "count":count}

#Get the actial ranked list
@app.get("/results")
def return_results():
    global masterList
    if len(masterList)>0:
        sorted(masterList, key=lambda x: x[2], reverse=True)
        if len(masterList)<5:
            return  {"data":masterList}
        return {"data":masterList[0:5]}
    return {"Error":"No Results to show"}




