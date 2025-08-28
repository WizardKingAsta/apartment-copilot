import {Form} from 'next/form'
import { useState} from "react"

export default function Home(){
    //Holds current input
    const [value, setValue] = useState("");
    //Keep track of loading value to grey out submit button
    const [isLoading, setIsLoading] = useState(false);

    //Keep track of if message is being used
    const [message, setMessage] = useState(null);
    const [messageInfo, setMessageInfo] = useState('');

    //send url to back end for storage
    async function sendSubmission(url){
        //Run the back end on its own and enter the right url + endpoint
        setIsLoading(true)
        try{
        const response = await fetch("/api/link", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url})
        });
        setMessage("Success: Link has been posted!")
        setMessageInfo("success")
        const issue = await response.json()

        if(!response.ok){
            setMessage(issue.detail)
            setMessageInfo("error")
        }
    }catch(error){
        setMessage(error)
            setMessageInfo("error")
    }finally{
        setIsLoading(false)
    }
   
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
            {message && (
                <div className={`popup ${messageInfo === 'success' ? 'Success!' : 'Error!'}`}>
                    {message}
                    <button onClick= {() => setMessage(null)}>x</button>
                    </div>
            )}
            <form onSubmit = {handleSubmit}>
                <input 
                    name = "url"
                    value={value}
                    onChange={(e)=> setValue(e.target.value)}
                />
                <button type="submit" disabled = {isLoading}>Submit</button>
            </form>
        </div>
    )
}
