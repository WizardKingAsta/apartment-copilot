//Async function for await
export default async function getRes(request, res){
    console.log("in RESULTS")
    //Ensure the correct method for request
    if (request.method == 'GET'){
        //Try to fetch from api
    try{
    const API_BASE = "http://127.0.0.1:8000";
    const TARGET = API_BASE + "/results";

    //Turn data into jason for return
    const response = await fetch(TARGET);
    const data = await response.json();
    console.log(data)
    res.status(200).json(data)
    // Catch error
    }catch(error){
        console.error(error);
        res.status(500).json({error: "Could not fetch results"});
    }
    }else{
        res.setHeader('Allow', ['GET']);
        res.status(405).json({ error: "Invalid operation (/api/results)"});
    }
}