"use client"; //import use client to ensure client side (api route is server side which helsp prevent CORS error of direct API route from here)
import React, {useState, useEffect} from 'react';


export default function Board(){
    // Set up API route path
    const TARGET =  "/api/queue"

    //Create array to hold urls that are pending
    const [urlArray, setUrlArray] = useState([]);
    
    //fetch data from api
    useEffect(() => {fetch(TARGET).then(response => response.json())
        .then(urlArray => {setUrlArray(urlArray.database);})
        .catch(error => console.error(error));
    },[])
    console.log(urlArray)
    return (<div>
        <h1>Board</h1>
        {urlArray.map((entry,index) => (
        <div key ={index}>
         <h2>{entry.url} : {entry.status}</h2>
         </div>
        ))}

    </div>);
}