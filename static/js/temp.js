function onGet()
{
    // const url = "https://59so7ea35l.execute-api.us-east-1.amazonaws.com/dev";
    var headers = {}

    fetch('https://6iskkgsygl.execute-api.us-east-1.amazonaws.com/dev', {
        method: "GET",
        mode: 'cors'

    })

        .then((response) =>
        {
            if (!response.ok)
            {
                throw new Error(response.error)
            }
            return response.text();
        })
        .then(text =>
        {
            text = text.slice(1, -1);
            text = text.split(",");
            document.getElementById("hum").innerHTML = text[1].slice(1, -1);
            document.getElementById("temp").innerHTML = text[0].slice(1, -1);
        })
        .catch(function (error)
        {
            console.log(error);
        });
}

onGet();