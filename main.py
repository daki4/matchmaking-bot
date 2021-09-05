import discord
from discord.ext import commands
import json

# Get configuration.json
with open("configuration.json", "r") as config:
    data = json.load(config)
    token = data["token"]
    prefix = data["prefix"]

# Intents
intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(prefix, intents = intents)

# Load cogs
initial_extensions = [
    "cogs.create_event",
    "cogs.setup",
    # "cogs.notify",
    # "cogs.garbage_collect"
]

print(initial_extensions)

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(e)

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f"for {bot.command_prefix}help"))
    print(discord.__version__)

bot.run(token)
