"use client"; //import use client to ensure client side (api route is server side which helsp prevent CORS error of direct API route from here)
import React, {useState, useEffect} from 'react';
import {useRouter} from 'next/router';

// Set up API route for board anlysis
const A_TARGET = "/api/analysis"

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


async function apiAnalysis(){
    //Set all links to fetching
        //fill in
    const response = await fetch(A_TARGET)
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
    
    //Next router to return Home
    const router = useRouter();
   //useEffect to load board data whens ite is opebed
    useEffect(()=>{loadBoardData(TARGET)},[]);

    const loadBoardData = async() =>{
        //Set board laoding so it displays a loading sign
        setBoardLoading(true);
        const response = await fetchAPI(TARGET);   //Gather data from api
        setServTime(response.headers.get("X-Server-Time"));  //Set tine from header
        const data = await response.json();  // turn response to json
        setUrlArray(data.database); // Set url array to database in data
        setBoardLoading(false);  //loading false to take away loading sign
    };

    //Is loading for analysis button
    const [isFetching, setIsFetching] = useState(false);
    //function calls outside function while keeping re4act features
    const handleAnalysis = async() => {
        //Change is fetching to true to disable the analysis buton
        setIsFetching(true)

        //Call analysis function which sets all pending -> queued
        const result = await apiAnalysis()

        //Create poll interval to keep refreshing board while we analyze
        const pollInterval = setInterval(async() => {
            //Get new data by loading board again
            await loadBoardData();
            //Extract datarows from respose

            //Check if work is still being done by seeing if any of the db items are in queue or fetching (ie not parsed already)
            const stillProcessing = urlArray.some(
                urlArray => urlArray[4] === 'queued' || urlArray[4] === 'fetching'
            );

            //Stop refreshibg if that is the case
            if(!stillProcessing){
                clearInterval(pollInterval)
                setIsFetching(false)
            }
        }, 2000);
        
    }




    return (<div>
        <button onClick={loadBoardData}>Refresh</button>
        <button onClick ={() => router.back()}>Go Back</button>
        <button disabled = {isFetching} onClick = {handleAnalysis}>Analysis</button>
        <h1>Board</h1>
        {boardLoading ? (
            <h2>Loading...</h2>
        ) :
        urlArray.length == 0 ? (
            <h2>Empty</h2>
        )  : (urlArray.map((entry) => (
        <div key ={entry[0]}>
         <h2>{entry[3]} : {entry[4]} : {timeMath(servTime,entry[5])}</h2>
         </div>
        )))}

    </div>);
}