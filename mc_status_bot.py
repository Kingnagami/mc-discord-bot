import discord
from discord.ext import commands, tasks
from mcstatus import JavaServer
from datetime import datetime
import os

# ============================================================
#  ตั้งค่าตรงนี้
# ============================================================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID    = int(os.environ.get("CHANNEL_ID"))
SERVER_HOST   = "KNB1.aternos.me"
SERVER_PORT   = 62733

CHECK_INTERVAL_MINUTES = 10       # เช็คทุกกี่นาที
OFFLINE_ALERT_THRESHOLD = 3       # แจ้งเตือนถ้าออฟไลน์ติดกันกี่ครั้ง (3 x 30 = 90 นาที)
# ============================================================

intents = discord.Intents.default()
intents.message_content = True   # 👈 เพิ่มบรรทัดนี้
bot = commands.Bot(command_prefix="!", intents=intents)

prev_online   = None
offline_count = 0


def check_java():
    try:
        server = JavaServer.lookup(f"{SERVER_HOST}:{SERVER_PORT}")
        status = server.status()
        return True, status.players.online, status.players.max, str(status.version.name)
    except Exception:
        return False, 0, 0, "N/A"


def make_embed(title, description, color, is_online, players, max_players, version):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
    embed.add_field(
        name="☕ Java Edition",
        value=(
            f"สถานะ: {'🟢 Online' if is_online else '🔴 Offline'}\n"
            f"ผู้เล่น: `{players}/{max_players}`\n"
            f"เวอร์ชัน: `{version}`"
        ),
        inline=False
    )
    embed.set_footer(text=f"🖥️ {SERVER_HOST}:{SERVER_PORT}")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot พร้อมแล้ว! เข้าสู่ระบบในชื่อ {bot.user}")
    check_server.start()


@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_server():
    global prev_online, offline_count

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ ไม่พบ channel กรุณาตรวจสอบ CHANNEL_ID")
        return

    is_online, players, max_players, version = check_java()

    if is_online:
        offline_count = 0

        if prev_online is False:
            embed = make_embed(
                "🟢 เซิร์ฟเวอร์กลับมา Online แล้ว!",
                f"มีผู้เล่นอยู่ **{players}** คน",
                discord.Color.green(), True, players, max_players, version
            )
            await channel.send(embed=embed)

        elif prev_online is None:
            embed = make_embed(
                "📡 Bot เริ่มทำงานแล้ว!",
                "กำลังตรวจสอบสถานะเซิร์ฟเวอร์",
                discord.Color.blurple(), True, players, max_players, version
            )
            await channel.send(embed=embed)

        await bot.change_presence(
            activity=discord.Game(name=f"🎮 {players}/{max_players} คนออนไลน์ | {SERVER_HOST}")
        )

    else:
        offline_count += 1

        if prev_online is True:
            embed = make_embed(
                "🔴 เซิร์ฟเวอร์ออฟไลน์แล้ว!",
                "เซิร์ฟเวอร์ไม่ตอบสนอง",
                discord.Color.red(), False, 0, 0, "N/A"
            )
            await channel.send(embed=embed)

        elif prev_online is None:
            embed = make_embed(
                "📡 Bot เริ่มทำงานแล้ว!",
                "เซิร์ฟเวอร์ออฟไลน์อยู่",
                discord.Color.blurple(), False, 0, 0, "N/A"
            )
            await channel.send(embed=embed)

        elif offline_count >= OFFLINE_ALERT_THRESHOLD:
            embed = make_embed(
                f"⚠️ เซิร์ฟเวอร์ออฟไลน์มาแล้ว {offline_count * CHECK_INTERVAL_MINUTES} นาที!",
                "กรุณาตรวจสอบเซิร์ฟเวอร์ Aternos",
                discord.Color.orange(), False, 0, 0, "N/A"
            )
            await channel.send(embed=embed)
            offline_count = 0

        await bot.change_presence(
            activity=discord.Game(name="💤 เซิร์ฟเวอร์ออฟไลน์")
        )

    prev_online = is_online


@bot.command(name="status")
async def status_command(ctx):
    is_online, players, max_players, version = check_java()

    if is_online:
        embed = make_embed(
            "🟢 เซิร์ฟเวอร์ออนไลน์",
            "ตรวจสอบสถานะล่าสุด",
            discord.Color.green(), True, players, max_players, version
        )
    else:
        embed = make_embed(
            "🔴 เซิร์ฟเวอร์ออฟไลน์",
            "ตรวจสอบสถานะล่าสุด",
            discord.Color.red(), False, 0, 0, "N/A"
        )
    await ctx.send(embed=embed)


bot.run(DISCORD_TOKEN)
