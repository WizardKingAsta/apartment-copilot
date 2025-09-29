// set up api connect
const API_BASE = "http://127.0.0.1:8000";
const TARGET = API_BASE + "/analysis";

//Functino to hand api communication
export default async function handler(request, res){
    if (request.method == 'POST'){
    try{
        console.log(request.body.data)
        const response = await fetch(TARGET,{
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({preferences: request.body.data})
        });
        const message = await response.json();
        console.log("in api/route")
        
        res.status(200).json(message)
    }catch(error){
        console.error(error)
        res.status(500).json({error:"Could not analyze"})
    }
}else{
    res.status(500).json({error: "Wrong Method ("+request.method+") Request"})
}
}