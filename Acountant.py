import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import re

# ==========================================
# 1. SEHEMU YA FLASK SERVER
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "🤖 Mhasibu BOT Yupo Hai na Salio Lipo Salama!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 2. MFUMO MPYA WA SALIO (Haufutiki kwenye Render)
# ==========================================
# Humu tutatumia kumbukumbu ya muda ya RAM. Ili isifutike,
# itasoma salio la mwanzo kutoka kwenye Render Environment ikiwemo.
SALIO_RAM = float(os.environ.get('KUMBUKUMBU_SALIO', 0.0))
MATUMIZI_RAM = float(os.environ.get('KUMBUKUMBU_MATUMIZI', 0.0))

def soma_data():
    global SALIO_RAM, MATUMIZI_RAM
    return SALIO_RAM, MATUMIZI_RAM

def hifadhi_data(salio, matumizi_leo):
    global SALIO_RAM, MATUMIZI_RAM
    SALIO_RAM = salio
    MATUMIZI_RAM = matumizi_leo

# ==========================================
# 3. SEHEMU YA DISCORD BOT (CHAT YA KAWAIDA)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

BAJETI_KWA_SIKU = 15000

@bot.event
async def on_ready():
    print(f"🤖 Bot {bot.user.name} Ameshawaka na Mfumo Imara wa Salio!")

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

    # 2. Kuingiza Pesa: "tuma 30000" au "tuma 30000 mshahara"
    elif ujumbe.startswith("tuma "):
        namba = re.findall(r'\d+\.?\d*', ujumbe)
        if namba:
            # REKEBISHO: Kuchukua namba ya kwanza kutoka kwenye list [0]
            kiasi = float(namba[0]) 
            salio, matumizi_leo = soma_data()
            salio += kiasi
            hifadhi_data(salio, matumizi_leo)
            await message.channel.send(f"✅ **MAPATO MPYA:** Tsh {kiasi:,.2f} imeingizwa. Salio jipya: Tsh {salio:,.2f}.")
        else:
            await message.channel.send("🛑 **Makosa:** Sijaona kiasi cha fedha. Mfano: `tuma 5000`")
        return

    # 3. Kurekodi Matumizi: "nimetumia 2000 chakula"
    elif ujumbe.startswith("nimetumia "):
        namba = re.findall(r'\d+\.?\d*', ujumbe)
        if namba:
            # REKEBISHO: Kuchukua namba ya kwanza kutoka kwenye list [0]
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

# ==========================================
# 4. KUWASHA SEVA ZOTE MBILI
# ==========================================
keep_alive()
TOKEN = os.environ.get('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
