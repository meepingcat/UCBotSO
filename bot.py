import json
import multiprocessing as mp
import os
import sys
import time
import traceback

import boto3
import discord
import mcstatus
from discord import app_commands
from flask import Flask, request

app = Flask(__name__)

with open("tokens.json", "r") as f:
    TOKENS = json.load(f)

GUILD_IDs = TOKENS["guilds"]
ADMIN_GUILD_IDs = TOKENS["admin_guilds"]
GUILDS = [discord.Object(id=g) for g in GUILD_IDs]
ADMIN_GUILDS = [discord.Object(id=g) for g in ADMIN_GUILD_IDs]
ADMINS = TOKENS["admins"]
DEBUG_CHANNELS = TOKENS["debug_channels"]
TOKEN = TOKENS["bot_token"]
aws_access_key_id = TOKENS["AWS_access_key"]
aws_secret_access_key = TOKENS["AWS_secret_access_key"]
aws_region = TOKENS["AWS_region"]
instance_id = TOKENS["EC2_instance_id"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def sync_commands():
    for guild in GUILDS:
        await tree.sync(guild=guild)


async def check_permissions(interaction: discord.Interaction):
    if interaction.user.id not in ADMINS:
        await interaction.response.send_message(
            "You do not have the permissions for this"
        )


@tree.command(name="sync", description="Sync commands with server", guilds=ADMIN_GUILDS)
async def sync(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Syncing commands!")
    await sync_commands()


@tree.command(name="update", description="Update UCBotSO code", guilds=ADMIN_GUILDS)
async def update(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Updating!")
    os.system("git pull")
    sys.exit(0)


@tree.command(name="stop", description="Shut down UCBotSO", guilds=ADMIN_GUILDS)
async def stop(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Shutting down!")
    sys.exit(-1)


@tree.command(name="restart", description="Reboot UCBotSO", guilds=ADMIN_GUILDS)
async def restart(interaction: discord.Interaction):
    await check_permissions(interaction)
    await interaction.response.send_message("Restarting!")
    sys.exit(0)


@tree.command(name="ping", description="Check that UCBotSO works", guilds=GUILDS)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@tree.command(name="code", description="Link to the UCBotSO Github repo", guilds=GUILDS)
async def code(interaction: discord.Interaction):
    await interaction.response.send_message("https://github.com/Noam-Elisha/UCBotSO")


@tree.command(
    name="ip", description="Get the ip for the Minecraft server", guilds=GUILDS
)
async def ip(interaction: discord.Interaction):
    await interaction.response.send_message("18.189.160.118:25565")


@tree.command(
    name="serveron", description="Turn on the Minecraft server", guilds=GUILDS
)
async def serveron(interaction: discord.Interaction):
    ec2_client = boto3.client(
        "ec2",
        region_name="us-east-2",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    ec2_client.start_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    await interaction.response.send_message(
        "Turning on the server. This will take a moment.\nPlease remember to turn it off using /serveroff when you're done"
    )


@tree.command(
    name="serveroff", description="Turn off the Minecraft server", guilds=GUILDS
)
async def serveroff(interaction: discord.Interaction):
    ec2_client = boto3.client(
        "ec2",
        region_name="us-east-2",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    ec2_client.stop_instances(
        InstanceIds=[
            instance_id,
        ],
    )
    await interaction.response.send_message("Thank you for turning off the server")


@tree.command(
    name="serverstatus",
    description="Show how many players are currently on the server",
    guilds=GUILDS,
)
async def serverstatus(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        server = mcstatus.JavaServer.lookup(TOKENS["server_ip"])
        status = server.status()
    except:
        await interaction.followup.send("The server is offline.")
        return
    await interaction.followup.send(
        f"The server has {status.players.online} player(s) online"
    )


async def debug(message, code=False):
    for cid in DEBUG_CHANNELS:
        channel = client.get_channel(cid)
        if code:
            await channel.send(f"```{str(message)}```")
        else:
            await channel.send(str(message))


@client.event
async def on_ready():
    await debug("UCBotSO is online!")
    print("UCBotSO is Online!")


@client.event
async def on_error(event, *args, **kwargs):
    await debug("on_error")
    await debug("```{}```".format(traceback.format_exc()))


@client.event
async def on_command_error(context, exception):
    await debug("on_error")
    await debug("```{}```".format(traceback.format_exc()))


# https://www.ocf.berkeley.edu/docs/services/web/flask/
@app.route("/email", methods=["POST"])
async def send_email_to_discord():
    channel = client.get_channel(1100661212246724618)
    req = request.data
    await channel.send(req)


def flask_run():
    app.run()  # unsure if this blocks, preventing discord client from running?


if __name__ == "__main__":
    flask_process = mp.Process(target=flask_run)
    client.run(TOKEN)

    flask_process.join()
