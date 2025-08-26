import {Form} from 'next/form'
import { useState} from "react"

export default function Home(){
    //Holds current input
    const [value, setValue] = useState("");

    //send url to back end for storage
    async function sendSubmission(url){
        //Run the back end on its own and enter the right url + endpoint
       
        const response = await fetch("/api/link", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url})
        });
    }

    //Function to handle event on submit button
    function handleSubmit(e){

        e.preventDefault(); 
        
        //properly export url from event
        const fd = new FormData(e.currentTarget);   
        const url = fd.get("url");

        sendSubmission(url)
        //add url to setItems
        //Reset value for next url
        //setValue("");

    }


    return (
        <div>
            <form onSubmit = {handleSubmit}>
                <input 
                    name = "url"
                    value={value}
                    onChange={(e)=> setValue(e.target.value)}
                />
                <button type="submit">Submit</button>
            </form>
        </div>
    )
}
