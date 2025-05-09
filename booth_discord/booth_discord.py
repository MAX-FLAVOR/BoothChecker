import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from pytz import timezone
from quart import Quart, request, jsonify
import asyncio

class DiscordBot(commands.Bot):
    def __init__(self, booth_db, logger, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="/", intents=intents, *args, **kwargs)
        self.booth_db = booth_db
        self.logger = logger
        self.embed_message = None  # on_ready에서 초기화 예정
        self.app = Quart(__name__)  # Quart 앱 초기화
        self.setup_commands()
        self.setup_routes()
        self.error_counts = {}
        self.error_count_user = set()
        # on_ready 이벤트는 메서드로 정의되므로 별도 등록이 필요 없음

    async def setup_hook(self):
        # 봇이 로그인된 후, 준비되기 전에 호출되는 메서드
        # 여기서 웹 서버를 시작합니다.
        asyncio.create_task(self.run_app())

    async def run_app(self):
        # Quart 앱 실행
        await self.app.run_task(host='0.0.0.0', port=5000)

    def setup_commands(self):
        @self.tree.command(name="booth", description="BOOTH 계정 등록")
        @app_commands.describe(cookie="""BOOTH.pm의 "_plaza_session_nktz7u"의 쿠키 값을 입력 해주세요""")
        async def booth(interaction: discord.Interaction, cookie: str):
            try:
                self.booth_db.add_booth_account(cookie, interaction.user.id)
                self.logger.info(f"User {interaction.user.id} is registering BOOTH account")
                await interaction.response.send_message("BOOTH 계정 등록 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while adding BOOTH account: {e}")
                await interaction.response.send_message(f"BOOTH 계정 등록 실패: {e}", ephemeral=True)

        @self.tree.command(name="item_add", description="BOOTH 아이템 등록")
        @app_commands.describe(item_number="BOOTH 상품 번호를 입력 해주세요")
        @app_commands.describe(item_name="아이템 이름을 입력 해주세요")
        @app_commands.describe(intent_encoding="아이템 이름의 인코딩 방식을 입력해주세요 (기본값: shift_jis)")
        @app_commands.describe(summary_this="업데이트 내용 요약 (기본값: True)")
        async def item_add(
            interaction: discord.Interaction,
            item_number: str,
            item_name: str = None,
            intent_encoding: str = "shift_jis",
            summary_this: bool = True
        ):
            try:
                await interaction.response.defer(ephemeral=True)
                self.booth_db.add_booth_item(
                    interaction.user.id,
                    interaction.channel_id,
                    item_number,
                    item_name,
                    intent_encoding,
                    summary_this,
                )
                self.logger.info(f"User {interaction.user.id} is adding item with item number {item_number}")
                await interaction.followup.send(f"[{item_number}] 등록 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while adding BOOTH item: {e}")
                try:
                    await interaction.followup.send(f"[{item_number}] 등록 실패: {e}", ephemeral=True)
                except discord.errors.NotFound:
                    self.logger.error("Failed to send error response due to invalid interaction.")

        @self.tree.command(name="booth_del", description="BOOTH 계정 등록 해제")
        async def booth_del(interaction: discord.Interaction):
            try:
                self.booth_db.del_booth_account(interaction.user.id)
                self.logger.info(f"User {interaction.user.id} is removing BOOTH account")
                await interaction.response.send_message("BOOTH 계정 삭제 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while removing BOOTH account: {e}")
                await interaction.response.send_message(f"BOOTH 계정 삭제 실패: {e}", ephemeral=True)

        @self.tree.command(name="item_del", description="BOOTH 아이템 삭제")
        @app_commands.describe(item="BOOTH 상품 번호를 입력해주세요")
        async def item_del(interaction: discord.Interaction, item: str):
            try:
                self.booth_db.del_booth_item(interaction.user.id, item)
                self.logger.info(f"User {interaction.user.id} is removing item with order number {item}")
                await interaction.response.send_message(f"[{item}] 삭제 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while removing BOOTH item: {e}")
                await interaction.response.send_message(f"[{item}] 삭제 실패: {e}", ephemeral=True)

        @self.tree.command(name="item_list", description="아이템 목록 확인")
        async def item_list(interaction: discord.Interaction):
            try:
                items = self.booth_db.list_booth_items(interaction.user.id, interaction.channel_id)
                if items:
                    items_list = [row[0] for row in items]
                    items_list = '\n'.join([f' - {i}' for i in items_list])
                    await interaction.response.send_message(f"# 등록된 아이템 목록\n{items_list}", ephemeral=True)
                    self.logger.info(f"User {interaction.user.id} is checking item list")
                else:
                    await interaction.response.send_message("등록된 아이템이 없습니다", ephemeral=True)
                    self.logger.info(f"User {interaction.user.id} has no item")
            except Exception as e:
                await interaction.response.send_message(f"아이템 목록 불러오기 실패: {e}", ephemeral=True)
                self.logger.error(f"Error occurred while listing BOOTH items: {e}")

        @self.tree.command(name="noti_update", description="업데이트 알림을 받을 채널 설정")
        @app_commands.describe(item_number="이 채널에서 업데이트 알림을 받을 아이템 번호를 입력해주세요")
        async def noti_update(interaction: discord.Interaction, item_number: str):
            try:
                self.booth_db.update_discord_noti_channel(interaction.user.id, interaction.channel.id, item_number)
                self.logger.info(f"User {interaction.user.id} is setting update notification channel")
                await interaction.response.send_message("업데이트 알림 채널 설정 완료", ephemeral=True)
            except Exception as e:
                self.logger.error(f"Error occurred while setting update notification channel: {e}")
                await interaction.response.send_message(f"업데이트 알림 채널 설정 실패: {e}", ephemeral=True)

    def setup_routes(self):
        @self.app.route("/send_message", methods=["POST"])
        async def send_message():
            data = await request.get_json()

            name = data.get("name")
            url = data.get("url")
            thumb = data.get("thumb")
            item_number = data.get("item_number")
            local_version_list = data.get("local_version_list")
            download_short_list = data.get("download_short_list")
            author_info = data.get("author_info")
            number_show = data.get("number_show")
            changelog_show = data.get("changelog_show")
            channel_id = data.get("channel_id")
            s3_object_url = data.get("s3_object_url")
            summary = data.get("summary")

            await self.send_message(
                name,
                url,
                thumb,
                item_number,
                local_version_list,
                download_short_list,
                author_info,
                number_show,
                changelog_show,
                channel_id,
                s3_object_url,
                summary
            )

            return jsonify({"status": "Message sent"}), 200

        @self.app.route("/send_error_message", methods=["POST"])
        async def send_error_message():
            data = await request.get_json()
            channel_id = data.get("channel_id")
            user_id = data.get("user_id")
            item_number = data.get("item_number")
            await self.send_error_message(channel_id, user_id, item_number)
            return jsonify({"status": "Error message sent"}), 200
        
        @self.app.route("/send_changelog", methods=["POST"])
        async def send_changelog():
            data = await request.get_json()
            channel_id = data.get("channel_id")
            file = data.get("file")
            await self.send_changelog(channel_id, file)
            return jsonify({"status": "Message sent"}), 200

    async def send_message(self, name, url, thumb, item_number, local_version_list, download_short_list, author_info, number_show, changelog_show, channel_id, s3_object_url=None, summary=None):
        if local_version_list:
            description = "# 업데이트 발견!"
        else:
            description = "# 새 아이템 등록!"

        if changelog_show and s3_object_url:
            description = f'{description} \n ## [변경사항 보기]({s3_object_url})'

        if author_info is not None:
            author_icon = author_info[0]
            author_name = author_info[1] + " "
        else:
            author_icon = ""
            author_name = ""

        embed = discord.Embed(
            title=name,
            description=description,
            url=url,
            colour=discord.Color.blurple(),
            timestamp=datetime.now(timezone('Asia/Seoul'))
        )
        embed.set_author(name=author_name, icon_url=author_icon)
        embed.set_thumbnail(url=thumb)
        embed.add_field(name="아이템 번호", value=str(item_number), inline=False)
        if number_show:
            if local_version_list:
                embed.add_field(name="LOCAL", value=str(local_version_list), inline=True)
            embed.add_field(name="BOOTH", value=str(download_short_list), inline=True)
        if summary: 
            embed.add_field(name="요약", value=str(summary), inline=False)
        embed.set_footer(text="BOOTH.pm", icon_url="https://booth.pm/static-images/pwa/icon_size_128.png")

        channel = self.get_channel(int(channel_id))
        await channel.send(content="@here", embed=embed)

    async def send_error_message(self, channel_id, discord_user_id, item_number):
        channel = self.get_channel(int(channel_id))
        
        key = f'{discord_user_id}_error_count'
        count = self.error_counts.get(key, 0) + 1
        self.logger.info(f'{key} = {count}')
        self.error_counts[key] = count

        if count >= 2 and discord_user_id not in self.error_count_user:
            self.error_count_user.add(discord_user_id)
            embed = discord.Embed(
                title="BOOTH 세션 쿠키 만료됨",
                description = (
                    "2회 이상 BOOTH가 응답하지 않았습니다.\n"
                    "/booth 명령어로 쿠키를 재등록해 주세요."
                ),
                colour=discord.Color.red()
            )
            await channel.send(content=f'<@{discord_user_id}>', embed=embed)

    async def send_changelog(self, channel_id, file):
        channel = self.get_channel(int(channel_id))
        await channel.send(file=discord.File(file))

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BOOTH.pm"))
        self.logger.info(f'Logged in as {self.user}')
        try:
            synced = await self.tree.sync()
            self.logger.info(f'Synced {len(synced)} command(s)')
        except Exception as e:
            self.logger.error(f'Error syncing commands: {e}')
