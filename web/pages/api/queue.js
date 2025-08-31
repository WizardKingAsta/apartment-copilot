//Async function for await
export default async function getUrls(request, res){
    //Ensure the correct method for request
    if (request.method == 'GET'){
        //Try to fetch from api
    try{
    const API_BASE = "http://127.0.0.1:8000";
    const TARGET = API_BASE + "/queue";

    //Turn data into jason for return
    const response = await fetch(TARGET);
    const data = await response.json();


    //Get current time for 'time since posted' metric on client frontend
    const now = new Date();
    const iso = now.toISOString();

    //Return json data
    res.setHeader("X-Server-Time", iso).status(200).json(data);
    // Catch error
    }catch(error){
        console.error(error);
        res.status(500).json({error: "Could not fetch url"});
    }
    }else{
        res.setHeader('Allow', ['GET']);
        res.status(405).json({ error: "Invalid operation (/api/queue)"});
    }
}