import os
import requests
import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

SOOP_ID = "secretto486"
DISCORD_CHANNEL_ID = 1551184385502613514
CHECK_INTERVAL = 30

SOOP_URL = f"https://www.sooplive.com/station/{SOOP_ID}"

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# 현재 방송 정보 기억
last_notified_bno = None
last_title = None


def check_soop():
    url = "https://live.sooplive.com/afreeca/player_live_api.php"

    data = {
        "bid": SOOP_ID,
        "type": "live",
        "player_type": "html5",
        "stream_type": "common",
        "quality": "HD",
        "mode": "landing",
        "from_api": "0",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.post(
            url,
            data=data,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()
        channel = result.get("CHANNEL", {})

        is_live = str(channel.get("RESULT")) == "1"

        title = channel.get("TITLE", "제목 없음")
        nickname = channel.get("BJNICK", "비밀소녀")
        broadcast_number = channel.get("BNO")

        return {
            "live": is_live,
            "title": title,
            "nickname": nickname,
            "broadcast_number": broadcast_number
        }

    except Exception as e:
        print("SOOP 확인 오류:", e)
        return None


@client.event
async def on_ready():
    print("--------------------------------")
    print(f"로그인 성공: {client.user}")
    print(f"감시 대상: {SOOP_ID}")
    print(f"알림 채널: {DISCORD_CHANNEL_ID}")
    print("--------------------------------")

    if not check_live.is_running():
        check_live.start()


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_live():
    global last_notified_bno
    global last_title

    info = check_soop()

    if info is None:
        return

    is_live = info["live"]
    title = info["title"]
    nickname = info["nickname"]
    bno = info["broadcast_number"]

    print(
        f"[SOOP] 방송중={is_live} "
        f"BNO={bno} "
        f"제목={title}"
    )

    # ==============================
    # 방송 종료
    # ==============================
    if not is_live:

        if last_notified_bno is not None:

            channel = client.get_channel(DISCORD_CHANNEL_ID)

            if channel is not None:

                embed = discord.Embed(
                    title=f"⚫ {nickname} 방송 종료",
                    description="방송이 종료되었습니다.",
                    url=SOOP_URL
                )

                embed.set_footer(
                    text="SOOP 방송 알림"
                )

                await channel.send(embed=embed)

                print(">>> 방송 종료 알림을 보냈습니다.")

        last_notified_bno = None
        last_title = None

        return

    # BNO가 없는 경우
    if not bno:
        return

    channel = client.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        print("디스코드 알림 채널을 찾을 수 없습니다.")
        return

    # ==============================
    # 새로운 방송 시작
    # ==============================
    if str(bno) != str(last_notified_bno):

        last_notified_bno = bno
        last_title = title

        thumbnail_url = f"https://liveimg.sooplive.com/m/{bno}"
        broadcast_url = f"https://play.sooplive.com/{SOOP_ID}/{bno}"

        embed = discord.Embed(
            title=f"🔴 {nickname} 뱅온",
            description=f"**{title}**",
            url=broadcast_url
        )

        embed.set_image(url=thumbnail_url)

        embed.add_field(
            name="📺 방송 보기",
            value=f"[▶ SOOP에서 방송 보기]({broadcast_url})",
            inline=False
        )

        embed.set_footer(
            text="SOOP 방송 알림"
        )

        await channel.send(
            content="@everyone",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                everyone=True
            )
        )

        print(">>> 새로운 방송 알림을 보냈습니다.")

        return

    # ==============================
    # 방송 제목 변경
    # ==============================
    if title != last_title:

        old_title = last_title
        last_title = title

        broadcast_url = f"https://play.sooplive.com/{SOOP_ID}/{bno}"

        embed = discord.Embed(
            title="📝 방송 제목 변경",
            url=broadcast_url
        )

        embed.add_field(
            name="이전 제목",
            value=old_title,
            inline=False
        )

        embed.add_field(
            name="새 제목",
            value=title,
            inline=False
        )

        embed.add_field(
            name="📺 방송 보기",
            value=f"[▶ SOOP에서 방송 보기]({broadcast_url})",
            inline=False
        )

        await channel.send(embed=embed)

        print(
            f">>> 방송 제목 변경: "
            f"{old_title} → {title}"
        )


# ==============================
# Discord 봇 실행
# ==============================

if not TOKEN:
    print("ERROR: DISCORD_TOKEN이 없습니다.")
    print(".env 파일을 확인해주세요.")

else:
    client.run(TOKEN)
