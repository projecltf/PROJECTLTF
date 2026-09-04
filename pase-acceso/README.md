# 🎫 Sistema de Pase de Acceso (Servidor Privado)

Réplica exacta y personalizable de la página de pase de acceso (`https://projectsamel.duckdns.org/acceso`), diseñada para gestionar el acceso a servidores privados de juegos (Free Fire, Minecraft, GTA RP, etc.) con enlace de cuenta de Discord y cupos limitados.

---

## 🌟 Características

- **Diseño Idéntico y Elegante**: Paleta oscura sólida (`#0e0e13`, `#17171f`), tipografía de sistema moderna y animaciones escalonadas de entrada.
- **Barra de Progreso y Estados**:
  1. **Inicio**: Logo, título, badge dinámico de plazas libres y botón oficial de Discord con logo vectorial SVG.
  2. **Verificando**: Tarjeta de identidad del usuario con avatar y nombre, pasos animados `(1) — (2) — (3)`.
  3. **Pase Otorgado**: Checkmark animado dibujándose en SVG (`.tic`), token de acceso con formato único, botón interactivo para copiar con 1 clic y fecha de caducidad.
- **Totalmente Personalizable**: Cambia el nombre del proyecto, el juego, las plazas y el prefijo de los códigos fácilmente.
- **Soporte Doble**:
  - Funciona de forma **estática inmediata** (abriendo `public/index.html` en cualquier navegador).
  - Incluye servidor backend en **Python 3** (sin dependencias externas) y en **Node.js/Express**.

---

## 🚀 Inicio Rápido (3 Formas de Usarlo)

### Opción 1: Abrir directamente en el navegador (Sin servidor)
1. Ve a la carpeta `public/`.
2. Haz doble clic en [`index.html`](file:///C:/Users/Admin/.gemini/antigravity/scratch/pase-acceso/public/index.html).
3. Usa la barra superior para alternar entre el estado **1. Inicio**, **2. Verificando** y **3. Pase Otorgado**.

### Opción 2: Ejecutar con Python (Recomendado, no requiere instalar librerías)
Tu sistema ya cuenta con Python 3.13 listo:
```bash
cd "C:\Users\Admin\.gemini\antigravity\scratch\pase-acceso"
python server.py
```
Abre en tu navegador: [http://localhost:3000/acceso](http://localhost:3000/acceso)

### Opción 3: Ejecutar con Node.js
Si instalas Node.js en el futuro:
```bash
npm install
npm start
```

---

## ⚙️ Conectar tu Aplicación Real de Discord (OAuth2)

Para que los usuarios inicien sesión real con su cuenta de Discord:

1. Ingresa a [Discord Developer Portal](https://discord.com/developers/applications).
2. Haz clic en **New Application** y ponle el nombre de tu proyecto.
3. Ve a la pestaña **OAuth2**:
   - Copia tu **Client ID**.
   - Genera y copia tu **Client Secret**.
   - En la sección **Redirects**, haz clic en **Add Redirect** y agrega:
     ```
     http://localhost:3000/oauth/discord/callback
     ```
     *(O la URL de tu dominio en producción, por ejemplo: `https://tudominio.duckdns.org/oauth/discord/callback`)*.
4. Abre el archivo `.env` en este proyecto y pega tus datos:
   ```env
   DISCORD_CLIENT_ID=tu_client_id_aqui
   DISCORD_CLIENT_SECRET=tu_client_secret_aqui
   DISCORD_REDIRECT_URI=http://localhost:3000/oauth/discord/callback
   ```
5. ¡Listo! Al hacer clic en **Entrar con Discord**, el sistema autenticará al usuario, registrará su ID en `pases.json` y le entregará su pase único.

---

## 🎨 Personalización

Puedes editar la configuración básica tanto en `.env` como dentro de `public/index.html`:

```javascript
const CONFIG = {
  nombreProyecto: "Mi Servidor Privado",
  subtitulo: "Free Fire 2022 · servidor privado",
  plazasTotales: 10000,
  plazasLibres: 3500,
  diasValidez: 30,
  logoUrl: "logo.png"
};
```

Para cambiar el logo, simplemente reemplaza el archivo `public/logo.png` por tu propia imagen cuadrada (512x512 o 256x256 px).

---

## 📁 Estructura del Proyecto

```
pase-acceso/
├── public/
│   ├── index.html        # Página principal de acceso (con los 3 estados integrados)
│   ├── terms.html        # Términos del servicio
│   ├── privacy.html      # Política de privacidad
│   └── logo.png          # Logo de la marca
├── server.py             # Servidor Python 3 (autocontenido, sin dependencias)
├── server.js             # Servidor Node.js (Express)
├── .env                  # Variables de entorno y credenciales
├── .env.example          # Ejemplo de configuración
├── pases.json            # Base de datos local donde se guardan los pases emitidos
└── README.md             # Documentación
```
