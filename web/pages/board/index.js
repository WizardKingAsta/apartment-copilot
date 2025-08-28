"use client"; //import use client to ensure client side (api route is server side which helsp prevent CORS error of direct API route from here)
import React, {useState, useEffect} from 'react';

function timeMath(serverTime, createTime){
    if(!serverTime){
        return "Could Not locate Server Time"
    } else if(!createTime){
        return "Could Not locate Submission Time"
    }


    return "seconds ago"

}


export default function Board(){
    // Set up API route path
    const TARGET =  "/api/queue"

    //keep track of if we are wairting for board info from api
    const [boardLoading, setBoardLoading] = useState(false);

    //Create array to hold urls that are pending
    const [urlArray, setUrlArray] = useState([]);

    //Set loaded time to do math for "time since upload" later
    const [servTime, setServTime] = useState(null);
    
    //fetch data from api
    //set board loading before fetch to true to dispay loading
    useEffect(() => {setBoardLoading(true); fetch(TARGET)
        .then(response => {servTime => setServTime(response.headers.get("X-Server-Time")); console.log(servTime); return response.json()})
        .then(urlArray => {setUrlArray(urlArray.database); setBoardLoading(false);}) //set board laoding to false bc we got info back
        .catch(error => console.error(error));
    },[]);

    console.log(servTime)

    return (<div>
        <h1>Board</h1>
        {boardLoading ? (
            <h2>Loading...</h2>
        ) :
        urlArray.length == 0 ? (
            <h2>Empty</h2>
        )  : (urlArray.map((entry,index) => (
        <div key ={index}>
         <h2>{entry.url} : {entry.status} : {timeMath(servTime,entry.created_at)}</h2>
         </div>
        )))}

    </div>);
}