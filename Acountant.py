import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import sqlite3

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
# 2. SEHEMU YA DATABASE (SQLITE) - BADALA YA TXT
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
    # Weka data za mwanzo kama hazipo
    cursor.execute("SELECT COUNT(*) FROM fedha")
    if cursor.fetchone()[0] == 0:
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

# Anzisha database kodi inapowaka
anzisha_db()

# ==========================================
# 3. SEHEMU YA DISCORD BOT
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BAJETI_KWA_SIKU = 15000

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user.name} Ameshawaka mtandaoni na anasikiliza simu yako!")

# 1. Amri ya kuingiza pesa (!ingiza 50000)
@bot.command()
async def ingiza(ctx, kiasi: float):
    salio, matumizi_leo = soma_data()
    salio += kiasi
    hifadhi_data(salio, matumizi_leo)
    await ctx.send(f"✅ **MAPATO MPYA:** Tsh {kiasi:,.2f} imeingizwa. Salio jipya: Tsh {salio:,.2f}.")

# 2. Amri ya kurekodi matumizi (!tumia 5000)
@bot.command()
async def tumia(ctx, kiasi: float):
    salio, matumizi_leo = soma_data()
    if kiasi > salio:
        await ctx.send(f"🛑 **Haiwezekani!** Salio lako ni Tsh {salio:,.2f} tu. Punguza matumizi!")
        return
        
    salio -= kiasi
    matumizi_leo += kiasi
    hifadhi_data(salio, matumizi_leo)
    
    jibu = f"💸 **ALERT MATUMIZI:** Umerekodi matumizi ya Tsh {kiasi:,.2f}.\n💰 Salio lililobaki: Tsh {salio:,.2f}."
    if matumizi_leo > BAJETI_KWA_SIKU:
        jibu += f"\n🚨 **ONYO KALI:** Umeshavuka kikomo cha leo cha Tsh {BAJETI_KWA_SIKU:,.2f}! Funga pochi yako! 🛑"
        # TTS inafanya kazi vizuri kwenye simu pia ikitumwa kama ujumbe wa sauti wa roboti
        await ctx.send(f"🚨 ONYO KALI: Umepitiliza bajeti ya leo ya Tsh {BAJETI_KWA_SIKU:,.2f}!", tts=True)
    
    await ctx.send(jibu)

# 3. Amri ya kuangalia hali ya fedha (!hali)
@bot.command()
async def hali(ctx):
    salio, matumizi_leo = soma_data()
    baki = BAJETI_KWA_SIKU - matumizi_leo
    ripoti = f"📊 **RIPOTI YA KIFEDHA:**\n💰 Salio: Tsh {salio:,.2f}\n📉 Umetumia Leo: Tsh {matumizi_leo:,.2f}"
    if baki < 0:
        ripoti += f"\n🛑 Umepandisha matumizi kwa Tsh {abs(baki):,.2f}!"
    else:
        ripoti += f"\n✅ Unaweza kutumia Tsh {baki:,.2f} zaidi leo."
    await ctx.send(ripoti)

# ==========================================
# 4. KUWASHA SEVA ZOTE MBILI
# ==========================================
keep_alive()  # Hii inawasha Flask kwanza ili Render isizime

# Hapa itasoma Token kutoka kwenye mipangilio ya siri ya Render (Environment Variables)
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ ERROR: Token ya Discord haijapatikana kwenye Environment Variables!")
