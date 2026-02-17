import asyncio
import websockets
import json
import pyautogui
import os

# --- CONFIGURATION ---
# Remplace par l'URL de ton application Render (sans le http://)
SERVER_URL = "ton-app.onrender.com" 
# Un identifiant unique pour ce PC (ex: Nom de l'utilisateur)
CLIENT_ID = os.getlogin() 

async def start_client():
    uri = f"wss://{SERVER_URL}/ws/client/{CLIENT_ID}"
    
    while True: # Boucle pour se reconnecter automatiquement si ça coupe
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connecté au serveur Leviathan sous l'ID : {CLIENT_ID}")
                
                while True:
                    # Attente d'un ordre venant du dashboard
                    message = await websocket.recv()
                    data = json.loads(message)
                    cmd = data.get("cmd")
                    val = data.get("val", "")

                    # --- LOGIQUE D'EXÉCUTION ---
                    if cmd == "click":
                        pyautogui.click()
                    
                    elif cmd == "move":
                        try:
                            x, y = map(int, val.split(','))
                            pyautogui.moveTo(x, y)
                        except:
                            pass
                            
                    elif cmd == "screen":
                        pyautogui.screenshot("temp_screen.png")
                        # Optionnel : envoyer le screen au serveur ici
        
        except Exception as e:
            print(f"Connexion perdue... Tentative de reconnexion dans 5s")
            await asyncio.sleep(5)

if __name__ == "__main__":
    start_client()