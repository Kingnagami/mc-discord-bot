import discord
from discord.ext import commands, tasks
import mcstatus
from mcstatus import JavaServer, BedrockServer
import asyncio
from datetime import datetime

# ============================================================
#  ตั้งค่าตรงนี้
# ============================================================
import os
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID    = int(os.environ.get("CHANNEL_ID"))          # ใส่ ID ของ channel ที่ต้องการส่ง
SERVER_HOST   = "KNB1.aternos.me"
SERVER_PORT_JAVA    = 62733
SERVER_PORT_BEDROCK = 62733                    # เปลี่ยนถ้า Bedrock ใช้ port ต่างกัน

CHECK_INTERVAL_MINUTES = 30                    # เช็คทุกกี่นาที
OFFLINE_ALERT_THRESHOLD = 3                    # แจ้งเตือนถ้าออฟไลน์ติดกันกี่ครั้ง
# ============================================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# สถานะก่อนหน้า
prev_java_online    = None
prev_bedrock_online = None
offline_count_java    = 0
offline_count_bedrock = 0


def check_java():
    try:
        server = JavaServer.lookup(f"{SERVER_HOST}:{SERVER_PORT_JAVA}")
        status = server.status()
        return True, status.players.online, status.players.max, str(status.version.name)
    except Exception:
        return False, 0, 0, "N/A"


def check_bedrock():
    try:
        server = BedrockServer.lookup(f"{SERVER_HOST}:{SERVER_PORT_BEDROCK}")
        status = server.status()
        return True, status.players_online, status.players_max, str(status.version.brand)
    except Exception:
        return False, 0, 0, "N/A"


def make_embed(title, description, color, java_data, bedrock_data, timestamp):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=timestamp)

    java_online, java_players, java_max, java_ver = java_data
    bedrock_online, bedrock_players, bedrock_max, bedrock_ver = bedrock_data

    embed.add_field(
        name="☕ Java Edition",
        value=(
            f"สถานะ: {'🟢 Online' if java_online else '🔴 Offline'}\n"
            f"ผู้เล่น: `{java_players}/{java_max}`\n"
            f"เวอร์ชัน: `{java_ver}`"
        ),
        inline=True
    )
    embed.add_field(
        name="🪨 Bedrock Edition",
        value=(
            f"สถานะ: {'🟢 Online' if bedrock_online else '🔴 Offline'}\n"
            f"ผู้เล่น: `{bedrock_players}/{bedrock_max}`\n"
            f"เวอร์ชัน: `{bedrock_ver}`"
        ),
        inline=True
    )
    embed.set_footer(text=f"🖥️ {SERVER_HOST}:{SERVER_PORT_JAVA}")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot พร้อมแล้ว! เข้าสู่ระบบในชื่อ {bot.user}")
    check_server.start()


@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_server():
    global prev_java_online, prev_bedrock_online
    global offline_count_java, offline_count_bedrock

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ ไม่พบ channel กรุณาตรวจสอบ CHANNEL_ID")
        return

    now = datetime.utcnow()
    java_data    = check_java()
    bedrock_data = check_bedrock()

    java_online, java_players, _, _       = java_data
    bedrock_online, bedrock_players, _, _ = bedrock_data

    # --- ตรวจ Java ---
    if java_online:
        offline_count_java = 0
        if prev_java_online is False:
            # เพิ่งกลับมา Online
            embed = make_embed(
                "🟢 Java Server กลับมา Online แล้ว!",
                f"มีผู้เล่นอยู่ **{java_players}** คน",
                discord.Color.green(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
        elif prev_java_online is None:
            # ครั้งแรกที่ bot เริ่ม
            embed = make_embed(
                "📡 ตรวจสอบสถานะเซิร์ฟเวอร์",
                "Bot เริ่มทำงานแล้ว!",
                discord.Color.blurple(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
    else:
        offline_count_java += 1
        if prev_java_online is True:
            # เพิ่งออฟไลน์
            embed = make_embed(
                "🔴 Java Server ออฟไลน์แล้ว!",
                "เซิร์ฟเวอร์ไม่ตอบสนอง",
                discord.Color.red(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
        elif offline_count_java >= OFFLINE_ALERT_THRESHOLD:
            # ออฟไลน์นานเกินไป
            embed = make_embed(
                f"⚠️ Java Server ออฟไลน์มาแล้ว {offline_count_java * CHECK_INTERVAL_MINUTES} นาที!",
                "กรุณาตรวจสอบเซิร์ฟเวอร์ Aternos",
                discord.Color.orange(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
            offline_count_java = 0  # reset เพื่อไม่ให้สแปม

    # --- ตรวจ Bedrock ---
    if bedrock_online:
        offline_count_bedrock = 0
        if prev_bedrock_online is False:
            embed = make_embed(
                "🟢 Bedrock Server กลับมา Online แล้ว!",
                f"มีผู้เล่นอยู่ **{bedrock_players}** คน",
                discord.Color.green(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
    else:
        offline_count_bedrock += 1
        if prev_bedrock_online is True:
            embed = make_embed(
                "🔴 Bedrock Server ออฟไลน์แล้ว!",
                "เซิร์ฟเวอร์ไม่ตอบสนอง",
                discord.Color.red(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
        elif offline_count_bedrock >= OFFLINE_ALERT_THRESHOLD:
            embed = make_embed(
                f"⚠️ Bedrock Server ออฟไลน์มาแล้ว {offline_count_bedrock * CHECK_INTERVAL_MINUTES} นาที!",
                "กรุณาตรวจสอบเซิร์ฟเวอร์ Aternos",
                discord.Color.orange(), java_data, bedrock_data, now
            )
            await channel.send(embed=embed)
            offline_count_bedrock = 0

    # อัปเดตสถานะก่อนหน้า
    prev_java_online    = java_online
    prev_bedrock_online = bedrock_online

    # อัปเดต presence ของ bot
    total_players = java_players + bedrock_players
    if java_online or bedrock_online:
        await bot.change_presence(
            activity=discord.Game(name=f"🎮 {total_players} คนออนไลน์ | {SERVER_HOST}")
        )
    else:
        await bot.change_presence(
            activity=discord.Game(name=f"💤 เซิร์ฟเวอร์ออฟไลน์")
        )


# คำสั่ง !status - เช็คสถานะทันที
@bot.command(name="status")
async def status_command(ctx):
    now = datetime.utcnow()
    java_data    = check_java()
    bedrock_data = check_bedrock()
    java_online, _, _, _    = java_data
    bedrock_online, _, _, _ = bedrock_data

    if java_online or bedrock_online:
        color = discord.Color.green()
        title = "🟢 เซิร์ฟเวอร์ออนไลน์"
    else:
        color = discord.Color.red()
        title = "🔴 เซิร์ฟเวอร์ออฟไลน์"

    embed = make_embed(title, "ตรวจสอบสถานะล่าสุด", color, java_data, bedrock_data, now)
    await ctx.send(embed=embed)


bot.run(DISCORD_TOKEN)
