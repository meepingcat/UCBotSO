import boto3
import discord

from discord import app_commands
import sys
import traceback
import json
import os

with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

GUILD_IDs = TOKENS["guilds"]
ADMINS = TOKENS["admins"]
DEBUG_CHANNELS = TOKENS["debug_channels"]
GUILDS = [discord.Object(id=g) for g in GUILD_IDs]
TOKEN = TOKENS["bot_token"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def sync_commands():
    for guild in GUILDS:
        await tree.sync(guild=guild)

async def check_permissions(interaction: discord.Interaction):
    if interaction.user.id not in ADMINS:
            await interaction.response.send_message("You do not have the permissions for this")
        
@tree.command(name = "sync", description = "sync commands with server", guilds=GUILDS)
async def sync(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Syncing commands!")
    await sync_commands()

@tree.command(name = "update", description = "Update Gnomebot's code", guilds=GUILDS)
async def update(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Updating!")
    os.system("git pull")
    sys.exit(0)

@tree.command(name = "stop", description = "shut down gnomebot", guilds=GUILDS)
async def stop(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Shutting down!")
    sys.exit(-1)

@tree.command(name = "restart", description = "reboot gnomebot", guilds=GUILDS)
async def restart(interaction : discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Restarting!")
    sys.exit(0)

@tree.command(name = "ping", description = "Check that Gnomebot works", guilds=GUILDS)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@tree.command(name = "code", description = "Link to the Gnomebot Github repo", guilds=GUILDS)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message("https://github.com/Noam-Elisha/GnomeBot")

async def debug(message):
    for cid in DEBUG_CHANNELS:
        channel = client.get_channel(cid)
        await channel.send(message)
    
@client.event
async def on_ready():
    await debug("UCBotSO is online!")
    print("Gnomebot is Online!")

@client.event
async def on_error(event, *args, **kwargs):
    await debug("on_error")
    await debug("```{}```".format(traceback.format_exc()))

@client.event
async def on_command_error(context, exception):
    await debug("on_error")
    await debug("```{}```".format(traceback.format_exc()))

client.run(TOKEN)