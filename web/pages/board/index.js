"use client"; //import use client to ensure client side (api route is server side which helsp prevent CORS error of direct API route from here)
import React, {useState, useEffect, useRef} from 'react';
//import Modal from 'react-modal'
import {useRouter} from 'next/router';

// Set up API route for board anlysis
const A_TARGET = "/api/analysis"

let globalPollingInfo = {
    isFetching: false
};



function timeMath(serverTime, createTime){
    if(!serverTime){
        return "Could Not locate Server Time"
    } else if(!createTime){
        return "Could Not locate Submission Time"
    }
    // Turn iso Strings into dte objects
    createTime = new Date(createTime);
    serverTime = new Date(serverTime);

    //compute diff with built in Date feature (returns in milliseconds)
    const diff= serverTime-createTime

    let seconds = Math.floor(diff/1000);
    let minutes = Math.floor(seconds/60);
    let hours = Math.floor(minutes/60);

    seconds = seconds - (minutes*60)
    minutes = minutes - (hours*60)

    let return_time = ""

    if(hours>0){
        return_time += hours + " hours, ";
    }
    if(minutes>0 || hours>0){
        return_time+= minutes + " minutes and ";
    }
    return_time += seconds + " seconds since submission";

    return return_time

}

async function fetchAPI(TARGET){
    const response = await fetch(TARGET);
    return response;
}


async function apiAnalysis(prefData){
    //Set all links to fetching
        //Changed method to post to carry user prefs in with it
    const response = await fetch(A_TARGET, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({'data': prefData})
    })
    //reload board
    return response
}   



export default function Board(){
    // Set up API route path for board loading
    const TARGET =  "/api/queue"
    //fetchAPI();

    //keep track of if we are wairting for board info from api
    const [boardLoading, setBoardLoading] = useState(false);

    //Create array to hold urls that are pending
    const [urlArray, setUrlArray] = useState([]);

    //Set loaded time to do math for "time since upload" later
    const [servTime, setServTime] = useState(null);

    //Is loading for analysis button
    const [isFetching, setIsFetching] = useState(false);
    // create poll interval with useRef so it can be accessed across areas and is mutable
    const pollInterval = useRef(null)

    // arr for the results from the analysis
    const [resultsArray, setResultsArray] = useState([]);

    //Set up boolean to know whether or not to show modal
    const [showModal, setShowModal] = useState(false);
    
    //Next router to return Home
    const router = useRouter();

    useEffect(() => {
        console.log("resultsArray updated:", resultsArray);
      }, [resultsArray]);
   //useEffect to load board data whens ite is opebed
    useEffect(()=>{
      
        
        if(globalPollingInfo.isFetching){
            //set is fetching to true in case we have come back to page and it lost value
            setIsFetching(true)
            createPoll()
        }else{
        loadBoardData(TARGET)
        }
        return () =>{
            clearInterval(pollInterval.current) //use reference to poll interval to end pollig when we leave the page to save api time
        }
    },[]);

    const loadBoardData = async() =>{
        //Set board laoding so it displays a loading sign
        setBoardLoading(true);
        const response = await fetchAPI(TARGET);   //Gather data from api
        setServTime(response.headers.get("X-Server-Time"));  //Set tine from header
        const data = await response.json();  // turn response to json
        setUrlArray(data.database); // Set url array to database in data
        setBoardLoading(false);  //loading false to take away loading sign
        return data.database
    };

    //Timouts and interval for polling
    const INTERVAL = 2000; //2 second polling for submissions
    const TIMEOUT = 3 * 60 * 1000 ;// 3 minite timeout for link analysis
    const start = Date.now();

async function createPoll(){
    return new Promise((resolve) => {
    //Clear existing iterval to ensure successful unmount later
    clearInterval(pollInterval.current)
    //Create poll interval to keep refreshing board while we analyze
    pollInterval.current = setInterval(async() => {
        //Get new data by loading board again (functino automatically replaces global array values)
        // Assign to array so we have the freshest valyes for polling termination condiions
        const freshData = await loadBoardData();

        //Check if work is still being done by seeing if any of the db items are in queue or fetching (ie not parsed already)
        const stillProcessing = freshData.some(
            listing => listing[4] === 'queued' || listing[4] === 'fetching' || listing[4] === 'pending'
        );

        //Stop refreshibg if that is the case
        if(!stillProcessing || Date.now()-start > TIMEOUT){
            clearInterval(pollInterval.current)
            setIsFetching(false)
            globalPollingInfo.isFetching = false
            resolve()
        }   
    }, INTERVAL);
    }); // close promise
    }
    //function calls outside function while keeping re4act features
    const handleAnalysis = async() => {
        //Change is fetching to true to disable the analysis buton
        setIsFetching(true)
        globalPollingInfo.isFetching = true;

        //Call analysis function which sets all pending -> queued
        const result = await apiAnalysis("Price: 100")
        // uses funcinon to create a poll every INTERVAL var seconds
        await createPoll();

        const response = await fetchAPI("/api/results")
        const info = await response.json()

        if('data' in info){
            console.log("here")
            setResultsArray(info.data)
            

        }else{
            setResultsArray([])
        }
        setShowModal(true)

        
    }




    return (<div>
        <button onClick={loadBoardData}>Refresh</button>
        <button onClick ={() => router.back()}>Go Back</button>
        <button disabled = {globalPollingInfo.isFetching} onClick = {handleAnalysis}>Analysis</button>
        <div style = {{display:'flex', top:'0'}}>
           <div style= {{width: '300px', overflow:'hidden', marginLeft: 'auto', border: '1px solid black'}}>
            {
                <div>
                <div><label>Min Price: <input type="number"/></label> </div>
                <div><label>Max Price: <input type="number"/></label> </div>
                <div><label>Min Sqft: <input type="number"/></label> </div>
                <div><label>Max Sqft: <input type="number"/></label> </div>
                <div><label>Beds: <input type="number"/></label> </div>
                <div><label>Baths: <input type="number"/></label> </div>
                </div>
            }
            </div>
            
        </div>
        {showModal && (
            <div onClick={()=> setShowModal(false)}
            style= {{position: 'fixed', top: 0, left: 0, right:0, bottom: 0, background: 'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center'}}>
            <div onClick={(e) => e.stopPropagation()}
                style = {{background: 'white', padding:'2rem', borderRadius:'8px', maxWidth: '800px', maxHeight: '80vh', overflow:'auto'}}>
            <h2>Top 5 Results</h2>
            {resultsArray.length >0 ?(resultsArray.map((rating) => (
                <div key = {rating[0]}>
                    <h2>Complex:{rating[0]} | Unit Number:{rating[1]} | Floor Plan: {rating[2]} | Rent:{rating[3]} | SqFt:{rating[4]} | Beds:{rating[5]} | Bath:{rating[6]} | Available:{rating[7]} | Score:{rating[8]}</h2>
                </div>
            ))): <h2> No Results To Show</h2>}
            <button onClick={() => setShowModal(false)}>Close</button>
            </div>
        </div>
        )
        }
        <h1>Board</h1>
        {boardLoading ? (
            <h2>Loading...</h2>
        ) :
        urlArray.length == 0 ? (
            <h2>Empty</h2>
        )  : (urlArray.map((entry) => (
        <div key ={entry[0]}>
         <h2>{entry[3]} : {entry[4]} : {entry[18]}: {timeMath(servTime,entry[5])}</h2>
         </div>
        )))}

    </div>);
}