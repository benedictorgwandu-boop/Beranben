import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import re
import psycopg2  # Maktaba ya kuongea na PostgreSQL database

# ==========================================
# 1. SEHEMU YA FLASK SERVER
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Mhasibu BOT wa Kudumu Yupo Hai!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. MFUMO WA DATABASE YA KUDUMU (POSTGRESQL)
# ==========================================
DB_URL = os.environ.get('DATABASE_URL')

def anzisha_db():
    if not DB_URL:
        return
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fedha (
            id SERIAL PRIMARY KEY,
            salio REAL DEFAULT 0.0,
            matumizi_leo REAL DEFAULT 0.0
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM fedha")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO fedha (id, salio, matumizi_leo) VALUES (1, 0.0, 0.0)")
    conn.commit()
    conn.close()

def soma_data():
    if not DB_URL:
        return 0.0, 0.0
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT salio, matumizi_leo FROM fedha WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return float(row[0]), float(row[1])
    except Exception as e:
        print(f"Error reading DB: {e}")
    return 0.0, 0.0

def hifadhi_data(salio, matumizi_leo):
    if not DB_URL:
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE fedha SET salio = %s, matumizi_leo = %s WHERE id = 1", (salio, matumizi_leo))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error writing DB: {e}")

# Anzisha DB mapema
try:
    anzisha_db()
except Exception as e:
    print(f"Db initialization failed: {e}")

# ==========================================
# 3. SEHEMU YA DISCORD BOT
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BAJETI_KWA_SIKU = 15000

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user.name} Ameshawaka na Database ya Kudumu!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    ujumbe = message.content.lower().strip()

    if ujumbe == "salio langu" or ujumbe == "hali":
        salio, matumizi_leo = soma_data()
        baki = BAJETI_KWA_SIKU - matumizi_leo
        ripoti = f"📊 **RIPOTI YA KIFEDHA:**\n💰 Salio la Sasa: Tsh {salio:,.2f}\n📉 Umetumia Leo: Tsh {matumizi_leo:,.2f}"
        if baki < 0:
            ripoti += f"\n🛑 Umepandisha matumizi kwa Tsh {abs(baki):,.2f}!"
        else:
            ripoti += f"\n✅ Unaweza kutumia Tsh {baki:,.2f} zaidi leo."
        await message.channel.send(ripoti)
        return

    elif ujumbe.startswith("tuma "):
        namba = re.findall(r'\d+\.?\d*', ujumbe)
        if namba:
            kiasi = float(namba[0]) 
            salio, matumizi_leo = soma_data()
            salio += kiasi
            hifadhi_data(salio, matumizi_leo)
            await message.channel.send(f"✅ **MAPATO MPYA:** Tsh {kiasi:,.2f} imeingizwa. Salio jipya: Tsh {salio:,.2f}.")
        else:
            await message.channel.send("🛑 **Makosa:** Sijaona kiasi cha fedha. Mfano: `tuma 5000`")
        return

    elif ujumbe.startswith("nimetumia "):
        namba = re.findall(r'\d+\.?\d*', ujumbe)
        if namba:
            kiasi = float(namba[0]) 
            salio, matumizi_leo = soma_data()
            
            if kiasi > salio:
                await message.channel.send(f"🛑 **Haiwezekani!** Salio lako ni Tsh {salio:,.2f} tu. Punguza matumizi!")
                return
                
            salio -= kiasi
            matumizi_leo += kiasi
            hifadhi_data(salio, matumizi_leo)
            
            jibu = f"💸 **ALERT MATUMIZI:** Umerekodi matumizi ya Tsh {kiasi:,.2f}.\n💰 Salio lililobaki: Tsh {salio:,.2f}."
            if matumizi_leo > BAJETI_KWA_SIKU:
                jibu += f"\n🚨 **ONYO KALI:** Umeshavuka kikomo cha leo cha Tsh {BAJETI_KWA_SIKU:,.2f}! Funga pochi yako! 🛑"
                await message.channel.send(f"🚨 ONYO KALI: Umepitiliza bajeti ya leo ya Tsh {BAJETI_KWA_SIKU:,.2f}!", tts=True)
            
            await message.channel.send(jibu)
        else:
            await message.channel.send("🛑 **Makosa:** Sijaona kiasi cha fedha kwenye ujumbe wako. Mfano: `nimetumia 2000 chakula`")
        return

    await bot.process_commands(message)

keep_alive()
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
