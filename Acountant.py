import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import sqlite3
import re  # Maktaba maalum ya kutafuta namba kwenye maandishi

# ==========================================
# 1. SEHEMU YA FLASK SERVER (KWA AJILI YA RENDER)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Mhasibu BOT Yupo Hai na Anafanya Kazi Mtandaoni!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. SEHEMU YA DATABASE (SQLITE)
# ==========================================
def anzisha_db():
    conn = sqlite3.connect("mhasibu.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fedha (
            id INTEGER PRIMARY KEY,
            salio REAL,
            matumizi_leo REAL
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM fedha")
    if cursor.fetchone() == 0:
        cursor.execute("INSERT INTO fedha (id, salio, matumizi_leo) VALUES (1, 0.0, 0.0)")
    conn.commit()
    conn.close()

def soma_data():
    conn = sqlite3.connect("mhasibu.db")
    cursor = conn.cursor()
    cursor.execute("SELECT salio, matumizi_leo FROM fedha WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return 0.0, 0.0

def hifadhi_data(salio, matumizi_leo):
    conn = sqlite3.connect("mhasibu.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE fedha SET salio = ?, matumizi_leo = ? WHERE id = 1", (salio, matumizi_leo))
    conn.commit()
    conn.close()

anzisha_db()

# ==========================================
# 3. SEHEMU YA DISCORD BOT (CHAT RAHISI)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BAJETI_KWA_SIKU = 15000

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user.name} Ameshawaka na Mfumo wa Maelezo!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    ujumbe = message.content.lower().strip()

    # 1. Kuangalia Salio: "salio langu" au "hali"
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

    # 2. Kuingiza Pesa: "tuma 5000" au "tuma 5000 ya mshahara"
    elif ujumbe.startswith("tuma "):
        # Inatafuta namba yoyote kwenye ujumbe
        namba = re.findall(r'\d+\.?\d*', ujumbe)
        if namba:
            kiasi = float(namba[0])
            salio, matumizi_leo = soma_data()
            salio += kiasi
            hifadhi_data(salio, matumizi_leo)
            await message.channel.send(f"✅ **MAPATO MPYA:** Tsh {kiasi:,.2f} imeingizwa. Salio jipya: Tsh {salio:,.2f}.")
        else:
            await message.channel.send("🛑 **Makosa:** Sijaona kiasi cha fedha. Mfano: `tuma 5000 mshahara`")
        return

    # 3. Kurekodi Matumizi: "nimetumia 200 chakula"
    elif ujumbe.startswith("nimetumia "):
        # Inatafuta namba yoyote kwenye ujumbe
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
            await message.channel.send("🛑 **Makosa:** Sijaona kiasi cha fedha kwenye ujumbe wako. Mfano: `nimetumia 200 chakula`")
        return

    await bot.process_commands(message)

# ==========================================
# 4. KUWASHA SEVA ZOTE MBILI
# ==========================================
keep_alive()
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
