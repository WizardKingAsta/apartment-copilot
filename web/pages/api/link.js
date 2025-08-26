
// This page acts as a go between for the ui http submission and api

const API_BASE = "http://127.0.0.1:8000"
const TARGET = API_BASE + "/link"
  
//Submission comes in as an OPTIONS header, with the request, method, and allows in it.
export default async function handler(request, response){
    //Check if the request is aking to post to server
    if(request.method !== "POST"){
        response.setHeader('Allow', 'POST');
        return response.status(405).json({message: "Method not allows (in api/link)"});
    }

    //make sure of reeuest is non empty
    let body = request.body;                                     
    if (!body || typeof body !== "object") {
        return response.status(400).json({ message: "Invalid JSON (api/link)" });
    }
    // check to ensure right type and presence of url
    const url = body.url;                                  
    if (!url || typeof url !== "string") {
        console.log(url)
        return response.status(400).json({ message: "Field 'url' is required (api/link)" }); 
    }

    //check if url is valid url

    if(!(url.startsWith("http://") || url.startsWith("https://"))){
        return response.status(400).json({message: "Not a valid http or https link (api/link"});
    }

    // Try sending to api

    try{
        const servRes = await fetch(TARGET, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({url})
    });

    if(!servRes.ok){
        return response.status(servRes.status).json({ message: servRes.statusText });
    }

}catch(error){
    console.error(error)
    return response.status(502).json({ message: "Upstream unavailable (api/link)" });

}

    //send to api
    return response.status(200).json({message: "Success"});
}