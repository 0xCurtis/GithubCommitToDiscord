import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from filelock import FileLock
import os
import json
import datetime

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
DATA_FILE = 'data.json'
LOCK_FILE = 'data.lock'

# Intents for the bot
intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance
bot = commands.Bot(command_prefix='/', intents=intents)

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    daily_stats.start()

@client.tree.command()
async def ping(interaction: discord.Interaction):
    """Replies with Pong!"""
    await interaction.response.send_message('Pong!')

@client.tree.command()
async def add_account(interaction: discord.Interaction, account_name: str, user: discord.User):
    """Adds an account with a name and a user."""
    with FileLock(LOCK_FILE):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        data[user.id] = account_name

        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    await interaction.response.send_message(f'Account "{account_name}" has been linked to {user.mention}')

from fetch import fetch_github_contributions_for_user

@client.tree.command()
async def fetch_stats(interaction: discord.Interaction):
    """Fetches the GitHub stats for the user."""
    with FileLock(LOCK_FILE):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}
    response_strings = ""
    for user_id, account_name in data.items():
        user = await client.fetch_user(user_id)
        today = datetime.date.today()
        stats = fetch_github_contributions_for_user(account_name)
        response_strings += f'{user.mention} has made {stats} contributions today!\n'
    await interaction.response.send_message(response_strings)

@client.tree.command()
async def remove_account(interaction: discord.Interaction, user: discord.User):
    """Removes an account for a user."""
    with FileLock(LOCK_FILE):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}

        if user.id in data:
            del data[user.id]

            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)

    await interaction.response.send_message(f'Account has been unlinked from {user.mention}')

@client.tree.command()
async def list_accounts(interaction: discord.Interaction, user: discord.User):
    """Lists all the accounts linked to users."""
    with FileLock(LOCK_FILE):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}

    accounts = '\n'.join([f'{user.mention}: {account_name}' for _, account_name in data.items()])
    await interaction.response.send_message(f'Linked accounts:\n{accounts}')

@tasks.loop(time=datetime.time(23, 42))
async def daily_stats():
    with FileLock(LOCK_FILE):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {}
    print(data)
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("Gathered commit stats of the day!")


client.run(TOKEN)
