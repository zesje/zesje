let express = require('express')
let url = require('url')
let bodyParser = require('body-parser')
let app = express()

app.get('/authorize', function (req, res) {
  console.log('GET ' + req.url)
  let query = url.parse(req.url, true).query
  res.redirect('http://127.0.0.1:5000/api/oauth/callback?code=test&state=' + query.state)
})

app.get('/user', function (req, res) {
  console.log('GET ' + req.url)
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify({email: 'mock', name: 'mock_name'}, null, 3))
})

app.use(bodyParser.json())

app.post('/token', function (req, res) {
  console.log('POST ' + req.url)
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify({access_token: 'mock', token_type: 'bearer'}, null, 3))
})

let server = app.listen(8080, function () {
  let host = server.address().address
  let port = server.address().port
  console.log('Mock OAuth2 server listening at http://%s:%s', host, port)
})
