import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# インテントを設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# コマンドプレフィックスとインテントを指定
bot = commands.Bot(command_prefix='!', intents=intents)

# チャンネルIDとロールID（要変更）
START_CHANNEL_ID = 1406312576299565197  # 新しいチャンネルID
RESULT_CHANNEL_ID = 1406017767152422934    # 正しいIDに
COMPLETED_ROLE_ID = 1405986619181502595    # 正しいIDに

# アンケート用モーダル
class SurveyModal(discord.ui.Modal, title="プロフィール"):
    name = discord.ui.TextInput(
        label="名前",
        placeholder="あなたの名前を入力してください",
        required=True,
        max_length=50
    )
    gender = discord.ui.TextInput(
        label="性別",
        placeholder="例: 男性/女性/その他",
        required=True,
        max_length=20
    )
    hobby = discord.ui.TextInput(
        label="趣味",
        placeholder="あなたの趣味を教えてください",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=200
    )
    comment = discord.ui.TextInput(
        label="一言",
        placeholder="一言メッセージをどうぞ",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        print(f"Survey submitted by: {interaction.user} (ID: {interaction.user.id})")
        # モーダルデータを保存
        view = SurveyView(interaction.user)
        view.name = self.name.value
        view.gender = self.gender.value
        view.hobby = self.hobby.value
        view.comment = self.comment.value
        await interaction.response.defer(ephemeral=True)
        await view.process_results(interaction)

# モーダル結果処理用ビュー
class SurveyView(discord.ui.View):
    def __init__(self, user: discord.Member):
        super().__init__(timeout=None)
        self.user = user
        self.name = None
        self.gender = None
        self.hobby = None
        self.comment = None

    async def process_results(self, interaction: discord.Interaction):
        print(f"Processing results for user: {self.user}")
        roles_to_add = []
        completed_role = interaction.guild.get_role(COMPLETED_ROLE_ID)
        if completed_role is None:
            print(f"Error: COMPLETED_ROLE_ID {COMPLETED_ROLE_ID} not found")
            await interaction.followup.send(
                content="エラー：ロールが見つかりません。管理者にお問い合わせください。",
                ephemeral=True
            )
            self.stop()
            return
        roles_to_add.append(completed_role)
        
        try:
            await self.user.add_roles(*roles_to_add, reason="アンケート回答")
        except discord.Forbidden:
            print(f"Error: Failed to add roles for user {self.user}")
            await interaction.followup.send(
                content="ロール付与に失敗しました。BOTの権限を確認してください。",
                ephemeral=True
            )
            self.stop()
            return

        result_channel = bot.get_channel(RESULT_CHANNEL_ID)
        if result_channel is None:
            print(f"Error: RESULT_CHANNEL_ID {RESULT_CHANNEL_ID} not found")
            await interaction.followup.send(
                content="エラー：結果チャンネルが見つかりません。管理者にお問い合わせください。",
                ephemeral=True
            )
            self.stop()
            return
        
        embed = discord.Embed(title="メンバープロフィール", color=discord.Color.blue())
        embed.add_field(name="名前", value=self.name or "不明", inline=False)
        embed.add_field(name="性別", value=self.gender or "不明", inline=False)
        embed.add_field(name="趣味", value=self.hobby or "不明", inline=False)
        embed.add_field(name="一言", value=self.comment or "不明", inline=False)
        try:
            await result_channel.send(embed=embed)
            print("Result message sent successfully")
        except Exception as e:
            print(f"Failed to send result message: {e}")
            await interaction.followup.send(
                content="結果の投稿に失敗しました。管理者にお問い合わせください。",
                ephemeral=True
            )
            self.stop()
            return
        
        await interaction.followup.send(
            content="プロフィールの記入ありがとう！",
            ephemeral=True
        )
        self.stop()

# スタートボタン
class StartButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="プロフィール記入", style=discord.ButtonStyle.green, custom_id="start_survey")
    async def start_survey(self, interaction: discord.Interaction, button: discord.ui.Button):
        print(f"Start button clicked by: {interaction.user} (ID: {interaction.user.id})")
        if COMPLETED_ROLE_ID in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("あなたはすでにプロフィール作成済みです。", ephemeral=True)
            return
        modal = SurveyModal()
        modal.name.default = str(interaction.user)
        await interaction.response.send_modal(modal)

# BOT起動時
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    channel = bot.get_channel(START_CHANNEL_ID)
    print(f'Start Channel: {channel} (ID: {START_CHANNEL_ID})')
    if channel:
        # 古いメッセージを削除
        try:
            async for message in channel.history(limit=10):
                if message.author == bot.user and "プロフィールを作成するには以下をクリック！" in message.content:
                    try:
                        await message.delete()
                        print("Deleted existing start message")
                    except Exception as e:
                        print(f"Failed to delete existing message: {e}")
        except Exception as e:
            print(f"Failed to access channel history: {e}")
        
        # 新しいメッセージを送信
        view = StartButton()
        try:
            await channel.send("プロフィールを作成するには以下をクリック！", view=view)
            print("Initial message sent successfully")
        except Exception as e:
            print(f"Failed to send initial message: {e}")
    else:
        print(f'Start Channel {START_CHANNEL_ID} not found')

# BOT実行
if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))