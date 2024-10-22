import discord
from discord import app_commands
from discord.ext import commands
import booth_sqlite
from datetime import datetime
from pytz import timezone

class DiscordBot:
    def __init__(self, DISCORD_BOT_TOKEN):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="/", intents=intents)
        self.setup_commands()
        self.bot.event(self.on_ready)
        self.bot.run(DISCORD_BOT_TOKEN)

    def setup_commands(self):            
        @self.bot.tree.command(name="booth_register", description="BOOTH 계정 등록")
        @app_commands.describe(cookie="""BOOTH.pm의 "_plaza_session_nktz7u"의 쿠키 값을 입력 해주세요""")
        @app_commands.describe(chanel=True)
        async def booth_register(interaction: discord.Interaction, cookie: str):
            try:
                booth_sqlite.add_session_cookie(cookie)
                await interaction.response.send_message("BOOTH 세션 쿠키 등록 완료", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"BOOTH 세션 쿠키 등록 실패: {e}", ephemeral=True)

        @self.bot.tree.command(name="booth_add_item", description="BOOTH 아이템 등록")
        @app_commands.describe(order_number="BOOTH 주문 번호를 입력 해주세요")
        async def set_item(interaction: discord.Interaction, order_number: int, item_name: str = None, check_only: str = None, intent_encoding: str = "shift_jis", download_number_show: bool = False, changelog_show: bool = True, archive_this: bool = False):
            try:
                booth_sqlite.add_item(interaction.user.id, order_number, item_name, check_only, intent_encoding, download_number_show, changelog_show, archive_this)
                await interaction.response.send_message("BOOTH 아이템 등록 완료", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"BOOTH 아이템 등록 실패: {e}", ephemeral=True)

    def send_message(self, channel_id, url, name, version_list, download_short_list, author_info, thumb, number_show, changelog_show, s3_upload_file):
        if version_list:
            description = "업데이트 발견!"
        else:
            description = "새 아이템 등록!"
            
        if changelog_show:
            description = f'# {description} \n ## [변경사항 보기]({s3_upload_file})'
        
        if author_info is not None:
            author_icon = author_info[0]
            author_name = author_info[1] + " "
        else:
            author_icon = ""
            author_name = ""

        embed = discord.Embed(name=name, description=description, url=url, colour=discord.Color.blurple(), timestamp=datetime.now(timezone('Asia/Seoul')).isoformat())
        embed.set_author(name=author_name, icon_url=author_icon)
        embed.set_thumbnail(url=thumb)
        if number_show:
            if version_list:
                embed.add_field(name="LOCAL", value=str(version_list), inline=True)
            embed.add_field(name="BOOTH", value=str(download_short_list), inline=True)
        embed.set_footer(text="BOOTH.pm", icon_url="https://booth.pm/static-images/pwa/icon_size_128.png")

        channel = self.bot.get_channel(channel_id)
        channel.send(content="@here", embed=embed)
        
    def error_message(self, channel_id, discord_user_id):
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(title="BOOTH 세션 쿠키 만료됨", description="/booth_register 명령어로 세션 쿠키를 재등록해주세요", colour=discord.Color.red())
        channel.send(content=f'<@{discord_user_id}>', embed=embed)

    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BOOTH.pm"))
        try:
            synced = await self.bot.tree.sync()
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Error syncing commands: {e}')
        print(f'Logged in as {self.bot.user}')
