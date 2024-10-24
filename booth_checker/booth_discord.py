import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from pytz import timezone
import logging

class DiscordBot:
    def __init__(self, booth_db, logger):
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="/", intents=intents)
        self.setup_commands()
        self.bot.event(self.on_ready)
        self.booth_db = booth_db
        self.logger = logger

    def setup_commands(self):            
        @self.bot.tree.command(name="booth_register", description="BOOTH 계정 등록")
        @app_commands.describe(cookie="""BOOTH.pm의 "_plaza_session_nktz7u"의 쿠키 값을 입력 해주세요""")
        async def booth_register(interaction: discord.Interaction, cookie: str):
            try:
                self.booth_db.add_booth_account(cookie, interaction.user.id, interaction.channel.id)
                await interaction.response.send_message("BOOTH 세션 쿠키 등록 완료", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"BOOTH 세션 쿠키 등록 실패: {e}", ephemeral=True)

        @self.bot.tree.command(name="booth_add_item", description="BOOTH 아이템 등록")
        @app_commands.describe(order_number="BOOTH 주문 번호를 입력 해주세요")
        @app_commands.describe(item_name="아이템 이름을 입력 해주세요")
        @app_commands.describe(check_only="확인하고 싶은 아이템의 상품페이지 번호를 입력해주세요 (ex. 1234567,2345678)")
        @app_commands.describe(intent_encoding="아이템 이름의 인코딩 방식을 입력해주세요")
        async def set_item(
            interaction: discord.Interaction, 
            order_number: str, 
            item_name: str = None, 
            check_only: str = None, 
            intent_encoding: str = "shift_jis"
        ):
            try:
                self.booth_db.add_booth_item(
                    interaction.user.id, 
                    order_number, 
                    item_name, 
                    check_only, 
                    intent_encoding, 
                    )
                self.logger.info(f"User {interaction.user.id} is adding item with order number {order_number}")
                await interaction.response.send_message("BOOTH 아이템 등록 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while adding BOOTH item: {e}")
                await interaction.response.send_message(f"BOOTH 아이템 등록 실패: {e}", ephemeral=True)

    async def send_message(self, name, url, thumb, local_version_list, download_short_list, author_info, number_show, changelog_show, s3_upload_file, channel_id):
        if local_version_list:
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

        embed = discord.Embed(title=name, description=description, url=url, colour=discord.Color.blurple(), timestamp=datetime.now(timezone('Asia/Seoul')))
        embed.set_author(name=author_name, icon_url=author_icon)
        embed.set_thumbnail(url=thumb)
        if number_show:
            if local_version_list:
                embed.add_field(name="LOCAL", value=str(local_version_list), inline=True)
            embed.add_field(name="BOOTH", value=str(download_short_list), inline=True)
        embed.set_footer(text="BOOTH.pm", icon_url="https://booth.pm/static-images/pwa/icon_size_128.png")

        channel = self.bot.get_channel(channel_id)
        await channel.send(content="@here", embed=embed)
                
    async def send_error_message(self, channel_id, discord_user_id):
        channel = self.bot.get_channel(channel_id)
        embed = discord.Embed(title="BOOTH 세션 쿠키 만료됨", description="/booth_register 명령어로 세션 쿠키를 재등록해주세요", colour=discord.Color.red())
        await channel.send(content=f'<@{discord_user_id}>', embed=embed)

    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BOOTH.pm"))
        self.logger.info(f'Logged in as {self.bot.user}')
        try:
            synced = await self.bot.tree.sync()
            self.logger.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            self.logger.error(f'Error syncing commands: {e}')
