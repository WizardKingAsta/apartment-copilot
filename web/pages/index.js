import {Form} from 'next/form'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState, useEffect} from "react"
import { useNavigate } from "react-router-dom";
import { useRouter } from 'next/router';


export default function Home(){
    return(
            <HomeContent />
    )

}

function HomeContent(){
    //Holds current input
    const [value, setValue] = useState("");
    //Keep track of loading value to grey out submit button
    const [isLoading, setIsLoading] = useState(false);

    //Keep track of if message is being used
    const [message, setMessage] = useState(null);
    const [messageInfo, setMessageInfo] = useState('');

    //Function to navigate to a different page
    const router = useRouter()

    //Text for user submision
    const [text, setText] = useState('')

    //Speach for submission
    const [isListening, setIsListening] = useState(false);
    const [recognition, setRecognition] = useState(null);

    //Use Effect to use be activated when text to speacj is going
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.continuous = true; //keep listening to user
        recognitionInstance.interimResults = true;// show text results as user speacks
        recognitionInstance.lang = 'en-US';

        //Handle speach results
        recognitionInstance.onresult = (event) => {
            let finalTranscript = '';

            for(let i = 0; i< event.results.length; i++){
                const transcript = event.results[i][0].transcript;

                if(event.results[i].isFinal){
                    finalTranscript+= transcript+' ';
                }
            }
            
            setText(finalTranscript);
        };
        setRecognition(recognitionInstance)
    },[]);

    //function to toggle listening
    const toggleListening = () => {
        if(isListening){
            recognition.stop();
        }else{
            recognition.start();
        }
        setIsListening(!isListening)
    }

    //send url to back end for storage
    async function sendSubmission(url,input){
        //Run the back end on its own and enter the right url + endpoint
        setIsLoading(true)
        try{
        const response = await fetch("/api/link", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({"link":url,"text":input}),
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
    
        sendSubmission(url,text)
        //add url to setItems
        //Reset value for next url
        //setValue("");

    }

    

    return (
        <div style={{
        display: 'flex',
        justifyContent: 'center', // centers horizontally
        alignItems: 'center',     // centers vertically
        height: '100vh',          // take full screen height
        width: '100%', 
        transform: 'translateY(-10%)',   }}>
            <div style={{ width: '100%', maxWidth: 620 }}>
            {message && (
                <div className={`popup ${messageInfo === 'success' ? 'Success!' : 'Error!'}`}>
                    {message}
                    <button onClick= {() => setMessage(null)}>x</button>
                    </div>
            )}
            <form style={{ display: 'flex', gap: '10px' }}onSubmit = {handleSubmit}>
                <input className='input-large'
                    name = "url"
                    value={value}
                    onChange={(e)=> setValue(e.target.value)}
                />
                <button className="btn btn-accent" type="submit" disabled = {isLoading}>Submit</button>
                <button className="btn btn-accent" onClick = {() => router.push("/board/")}>Go To Board</button>
            </form>
           
            <div style={{display:'flex',
            flexDirection: 'column',
                    height: '20vh',         
                    width: '100%',
                    transform: 'translateY(50%)'}}>
                 <label htmlFor='userWrittenPrefs' style={{ fontSize: '18px' }}>Please tell us a little about what your looking for, feel free to type or text what make your dream apartment yours!</label>
                <textarea rows={10}id="userWrittenPrefs" value={text} onChange={(e) => setText(e.target.value)}/>
                <button className="btn btn-accent"onClick={toggleListening}>
                    {isListening ? 'Stop':'Start'} Mic
                </button>
            </div>
            
            </div>
            
        </div>
    )
}
