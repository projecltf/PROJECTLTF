/**
 * Servidor de Pase de Acceso (Project Samel Clone)
 * Compatible con Node.js 18+ (usa fetch nativo)
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Configuración personalizable
const CONFIG = {
  projectName: process.env.PROJECT_NAME || 'Project Samel',
  subtitle: process.env.SUBTITLE || 'Free Fire 2022 · servidor privado',
  totalSlots: parseInt(process.env.TOTAL_SLOTS || '17100', 10),
  freeSlots: parseInt(process.env.FREE_SLOTS || '5272', 10),
  discordClientId: process.env.DISCORD_CLIENT_ID || '',
  discordClientSecret: process.env.DISCORD_CLIENT_SECRET || '',
  discordRedirectUri: process.env.DISCORD_REDIRECT_URI || `http://localhost:${PORT}/oauth/discord/callback`,
  tokenPrefix: process.env.TOKEN_PREFIX || 'SAMEL'
};

// Almacén simple en memoria de pases otorgados (o puedes persistir en un archivo json / sqlite)
const DB_FILE = path.join(__dirname, 'data_pases.json');
let pasesData = { otorgados: {} };

if (fs.existsSync(DB_FILE)) {
  try {
    pasesData = JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
  } catch (e) {
    console.error('Error al cargar base de datos local:', e);
  }
}

function guardarPases() {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(pasesData, null, 2));
  } catch (e) {
    console.error('Error al guardar datos:', e);
  }
}

// Servir archivos estáticos de la carpeta /public
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Redirección directa de /acceso a index.html
app.get('/acceso', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API para consultar plazas libres e información del proyecto
app.get('/api/estado', (req, res) => {
  const ocupadas = Object.keys(pasesData.otorgados).length;
  const libres = Math.max(0, CONFIG.freeSlots - ocupadas);
  res.json({
    projectName: CONFIG.projectName,
    subtitle: CONFIG.subtitle,
    totalSlots: CONFIG.totalSlots,
    freeSlots: libres,
    occupiedSlots: ocupadas
  });
});

// Ruta 1: Iniciar inicio de sesión con Discord OAuth2
app.get('/oauth/discord', (req, res) => {
  if (!CONFIG.discordClientId) {
    return res.status(400).send(`
      <body style="background:#0e0e13;color:#fff;font-family:sans-serif;padding:30px;text-align:center;">
        <h2>Falta configurar Discord Client ID</h2>
        <p style="color:#888">Edita el archivo <code>.env</code> con tu <code>DISCORD_CLIENT_ID</code> y <code>DISCORD_CLIENT_SECRET</code>.</p>
        <a href="/acceso" style="color:#8b5cf6;">&larr; Volver al modo demostración</a>
      </body>
    `);
  }

  const state = crypto.randomBytes(16).toString('hex');
  const params = new URLSearchParams({
    client_id: CONFIG.discordClientId,
    response_type: 'code',
    redirect_uri: CONFIG.discordRedirectUri,
    scope: 'identify email',
    state: state
  });

  res.redirect(`https://discord.com/oauth2/authorize?${params.toString()}`);
});

// Ruta 2: Callback de Discord OAuth2
app.get('/oauth/discord/callback', async (req, res) => {
  const code = req.query.code;
  if (!code) {
    return res.status(400).send('No se recibió código de autorización.');
  }

  try {
    // 1. Intercambiar código por token de acceso en Discord
    const tokenResponse = await fetch('https://discord.com/api/oauth2/token', {
      method: 'POST',
      body: new URLSearchParams({
        client_id: CONFIG.discordClientId,
        client_secret: CONFIG.discordClientSecret,
        grant_type: 'authorization_code',
        code: code,
        redirect_uri: CONFIG.discordRedirectUri
      }),
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    const tokenData = await tokenResponse.json();
    if (tokenData.error) {
      return res.status(400).send(`Error de Discord: ${tokenData.error_description || tokenData.error}`);
    }

    // 2. Obtener datos del usuario de Discord (@me)
    const userResponse = await fetch('https://discord.com/api/users/@me', {
      headers: { Authorization: `Bearer ${tokenData.access_token}` }
    });
    const userData = await userResponse.json();

    // 3. Generar o recuperar pase del usuario
    let tokenPase = pasesData.otorgados[userData.id]?.token;
    if (!tokenPase) {
      const parteHex = crypto.randomBytes(4).toString('hex').toUpperCase();
      const parteRand = Math.random().toString(36).substring(2, 6).toUpperCase();
      tokenPase = `${CONFIG.tokenPrefix}-${parteHex}-${parteRand}-${new Date().getFullYear()}`;
      
      pasesData.otorgados[userData.id] = {
        discordId: userData.id,
        username: userData.username,
        email: userData.email,
        token: tokenPase,
        fecha: new Date().toISOString()
      };
      guardarPases();
    }

    // 4. Renderizar la página con el pase concedido
    const avatarUrl = userData.avatar
      ? `https://cdn.discordapp.com/avatars/${userData.id}/${userData.avatar}.png`
      : 'https://cdn.discordapp.com/embed/avatars/0.png';

    res.send(`
      <!doctype html>
      <html lang="es">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Pase de acceso - Concedido</title>
        <link rel="stylesheet" href="/index.html">
        <script>
          // Inyectar datos en la interfaz
          window.addEventListener('DOMContentLoaded', () => {
            window.usuarioDiscord = {
              nombre: "${userData.username}",
              avatar: "${avatarUrl}"
            };
            window.tokenGenerado = "${tokenPase}";
            if (typeof cambiarEstado === 'function') {
              cambiarEstado('concedido');
            }
          });
        </script>
      </head>
      <body style="margin:0;">
        <script>
          // Cargar index y cambiar a estado concedido
          fetch('/index.html')
            .then(r => r.text())
            .then(html => {
              document.open();
              // Inyectar estado inicial concedido
              html = html.replace("let estadoActual = 'login';", "let estadoActual = 'concedido';");
              html = html.replace('let tokenGenerado = "SAMEL-9F82-K49X-2026";', 'let tokenGenerado = "${tokenPase}";');
              html = html.replace('JugadorPro', '${userData.username}');
              html = html.replace('https://cdn.discordapp.com/embed/avatars/0.png', '${avatarUrl}');
              document.write(html);
              document.close();
            });
        </script>
      </body>
      </html>
    `);

  } catch (err) {
    console.error('Error en callback:', err);
    res.status(500).send('Error interno procesando autenticación con Discord.');
  }
});

app.listen(PORT, () => {
  console.log(`=========================================`);
  console.log(` Servidor de Pase de Acceso iniciado!`);
  console.log(` URL: http://localhost:${PORT}/acceso`);
  console.log(`=========================================`);
});
