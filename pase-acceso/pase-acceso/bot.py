"""
Bot de Discord Oficial para Project LTF
Gestiona los pases de acceso, consulta plazas y entrega tokens a los jugadores.
"""

import discord
from discord.ext import commands
import json
import os
import secrets
from datetime import datetime

# Token del bot (se carga desde variable de entorno o se coloca aquí)
BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "PEGA_AQUI_EL_TOKEN_DE_TU_BOT")
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pases.json')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def cargar_pases():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def guardar_pases(datos):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

@bot.event
async def on_ready():
    print(f"==================================================")
    print(f" Bot conectado como: {bot.user.name} ({bot.user.id})")
    print(f" Listo para gestionar pases de Project LTF")
    print(f"==================================================")
    try:
        synced = await bot.tree.sync()
        print(f" Comandos slash sincronizados: {len(synced)}")
    except Exception as e:
        print(f" Error sincronizando comandos: {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Pases de acceso · /pase"
        )
    )

# Comando Slash: /pase (El jugador consulta su pase generado)
@bot.tree.command(name="pase", description="Consulta o genera tu pase de acceso para Project LTF")
async def cmd_pase(interaction: discord.Interaction):
    pases = cargar_pases()
    user_id = str(interaction.user.id)
    
    if user_id in pases:
        token = pases[user_id]["token"]
        embed = discord.Embed(
            title="🎟️ Tu Pase de Acceso - Project LTF",
            description=f"Ya tienes un pase registrado a tu nombre.\n\n**Código de Pase:**\n`{token}`",
            color=0x8b5cf6
        )
        embed.add_field(name="Fecha de emisión", value=pases[user_id].get("fecha", "Reciente"), inline=True)
        embed.set_footer(text="Copia este código y úsalo para entrar al juego.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        # Generar un pase nuevo al usuario
        parte1 = secrets.token_hex(2).upper()
        parte2 = secrets.token_hex(2).upper()
        token = f"LTF-{parte1}-{parte2}-{datetime.now().year}"
        
        pases[user_id] = {
            "username": str(interaction.user),
            "token": token,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        guardar_pases(pases)

        embed = discord.Embed(
            title="✅ ¡Pase de Acceso Otorgado!",
            description=f"¡Bienvenido a **Project LTF**!\n\n**Tu Pase:**\n`{token}`",
            color=0x4ade80
        )
        embed.add_field(name="Válido hasta", value="30 días", inline=True)
        embed.set_footer(text="Haz clic en el código para copiarlo.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Comando Slash: /plazas (Muestra plazas libres)
@bot.tree.command(name="plazas", description="Verifica las plazas libres en el servidor privado")
async def cmd_plazas(interaction: discord.Interaction):
    pases = cargar_pases()
    totales = 17100
    ocupadas = len(pases)
    libres = max(0, 5272 - ocupadas)

    embed = discord.Embed(
        title="📊 Cupos del Servidor - Project LTF",
        description=f"**{libres:,}** de **{totales:,}** plazas libres disponibles.",
        color=0xfbbf24
    )
    embed.add_field(name="Enlace de la web", value="[Entrar a la Web](https://projectltf.onrender.com/acceso)", inline=False)
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if BOT_TOKEN == "PEGA_AQUI_EL_TOKEN_DE_TU_BOT":
        print("[!] Por favor coloca el token de tu bot en la variable BOT_TOKEN o en .env")
    else:
        bot.run(BOT_TOKEN)
