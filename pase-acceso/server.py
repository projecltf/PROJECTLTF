#!/usr/bin/env python3
"""
Servidor local para Pase de Acceso (Project Samel Clone)
Ejecutable sin dependencias externas (usa librería estándar de Python 3).
"""

import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import os
import secrets
from datetime import datetime, timedelta

PORT = int(os.environ.get('PORT', 3000))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, 'public')
DATA_FILE = os.path.join(BASE_DIR, 'pases.json')

# Configuración por defecto (puede sobreescribirse con variables de entorno o editando aquí)
CONFIG = {
    "PROJECT_NAME": os.environ.get("PROJECT_NAME", "Project Samel"),
    "SUBTITLE": os.environ.get("SUBTITLE", "Free Fire 2022 · servidor privado"),
    "TOTAL_SLOTS": int(os.environ.get("TOTAL_SLOTS", 17100)),
    "FREE_SLOTS": int(os.environ.get("FREE_SLOTS", 5272)),
    "DISCORD_CLIENT_ID": os.environ.get("DISCORD_CLIENT_ID", ""),
    "DISCORD_CLIENT_SECRET": os.environ.get("DISCORD_CLIENT_SECRET", ""),
    "DISCORD_REDIRECT_URI": os.environ.get("DISCORD_REDIRECT_URI", f"http://localhost:{PORT}/oauth/discord/callback"),
    "TOKEN_PREFIX": os.environ.get("TOKEN_PREFIX", "SAMEL")
}

# Cargar base de datos local de pases
pases_db = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            pases_db = json.load(f)
    except Exception as e:
        print(f"[!] Error leyendo {DATA_FILE}: {e}")

def guardar_db():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(pases_db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Error guardando {DATA_FILE}: {e}")

class PaseHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_HEAD(self):
        # Mismo tratamiento para verificar disponibilidad
        self.do_GET()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Servir index.html en la raíz y en /acceso
        if path in ('/', '/acceso', '/acceso/'):
            index_path = os.path.join(PUBLIC_DIR, 'index.html')
            if os.path.exists(index_path):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(index_path, 'rb') as f:
                    self.wfile.write(f.read())
                return

        # API de estado de plazas
        if path == '/api/estado':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            ocupadas = len(pases_db)
            libres = max(0, CONFIG["FREE_SLOTS"] - ocupadas)
            resp = {
                "projectName": CONFIG["PROJECT_NAME"],
                "subtitle": CONFIG["SUBTITLE"],
                "totalSlots": CONFIG["TOTAL_SLOTS"],
                "freeSlots": libres,
                "occupiedSlots": ocupadas
            }
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode('utf-8'))
            return

        # Iniciar login con Discord
        if path == '/oauth/discord':
            client_id = CONFIG["DISCORD_CLIENT_ID"]
            if not client_id:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                html = f"""
                <!doctype html>
                <html>
                <body style="background:#0e0e13;color:#eceaf2;font-family:system-ui;padding:40px;text-align:center;">
                  <h2 style="color:#fbbf24;">Discord Client ID no configurado</h2>
                  <p style="color:#8d8a9c;max-width:500px;margin:0 auto 20px;">
                    Para usar el login real de Discord, agrega tus credenciales en el archivo <code>.env</code> o directamente en <code>server.py</code>.
                  </p>
                  <a href="/index.html" style="color:#8b5cf6;text-decoration:none;font-weight:bold;">&larr; Volver a la página interactiva</a>
                </body>
                </html>
                """
                self.wfile.write(html.encode('utf-8'))
                return

            params = urllib.parse.urlencode({
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": CONFIG["DISCORD_REDIRECT_URI"],
                "scope": "identify email"
            })
            discord_url = f"https://discord.com/oauth2/authorize?{params}"
            self.send_response(302)
            self.send_header('Location', discord_url)
            self.end_headers()
            return

        # Callback de Discord
        if path == '/oauth/discord/callback':
            codes = query.get('code')
            if not codes:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Codigo de autorizacion faltante.")
                return
            
            code = codes[0]
            try:
                # 1. Intercambiar code por token en Discord
                token_data = urllib.parse.urlencode({
                    "client_id": CONFIG["DISCORD_CLIENT_ID"],
                    "client_secret": CONFIG["DISCORD_CLIENT_SECRET"],
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": CONFIG["DISCORD_REDIRECT_URI"]
                }).encode('utf-8')

                req = urllib.request.Request(
                    "https://discord.com/api/oauth2/token",
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                with urllib.request.urlopen(req) as resp:
                    tokens = json.loads(resp.read().decode('utf-8'))

                # 2. Consultar usuario
                user_req = urllib.request.Request(
                    "https://discord.com/api/users/@me",
                    headers={"Authorization": f"Bearer {tokens['access_token']}"}
                )
                with urllib.request.urlopen(user_req) as resp:
                    user_info = json.loads(resp.read().decode('utf-8'))

                # 3. Generar token
                user_id = user_info["id"]
                username = user_info.get("username", "Jugador")
                avatar = user_info.get("avatar")
                avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.png" if avatar else "https://cdn.discordapp.com/embed/avatars/0.png"

                if user_id in pases_db:
                    token_pase = pases_db[user_id]["token"]
                else:
                    parte_hex = secrets.token_hex(2).upper()
                    parte_rand = secrets.token_hex(2).upper()
                    token_pase = f"{CONFIG['TOKEN_PREFIX']}-{parte_hex}-{parte_rand}-{datetime.now().year}"
                    pases_db[user_id] = {
                        "username": username,
                        "token": token_pase,
                        "email": user_info.get("email"),
                        "fecha": datetime.now().isoformat()
                    }
                    guardar_db()

                # 4. Inyectar en index.html
                index_path = os.path.join(PUBLIC_DIR, 'index.html')
                with open(index_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                content = content.replace("let estadoActual = 'login';", "let estadoActual = 'concedido';")
                content = content.replace('let tokenGenerado = "SAMEL-9F82-K49X-2026";', f'let tokenGenerado = "{token_pase}";')
                content = content.replace('nombre: "JugadorPro"', f'nombre: "{username}"')
                content = content.replace('https://cdn.discordapp.com/embed/avatars/0.png', avatar_url)

                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                return

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(f"<h2>Error autenticando con Discord</h2><p>{e}</p>".encode('utf-8'))
                return

        return super().do_GET()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), PaseHandler) as httpd:
        print(f"==================================================")
        print(f" Servidor Pase de Acceso ejecutándose!")
        print(f" URL: http://localhost:{PORT}/acceso")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDeteniendo servidor...")
