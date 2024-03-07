import discord
from discord import Message as DiscordMessage
import logging
from base import Message, Conversation
from constants import (
    BOT_INVITE_URL,
    DISCORD_BOT_TOKEN,
    EXAMPLE_CONVOS,
    ACTIVATE_THREAD_PREFX,
    MAX_THREAD_MESSAGES,
    SECONDS_DELAY_RECEIVING_MSG,
)
import asyncio
from utils import (
    logger,
    should_block,
    close_thread,
    is_last_message_stale,
    discord_message_to_message,
)
import completion

import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import MySQLdb
import requests
import time


logging.basicConfig(
    format="[%(asctime)s] [%(filename)s:%(lineno)d] %(message)s", level=logging.INFO
)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user}. Invite URL: {BOT_INVITE_URL}")
    completion.MY_BOT_NAME = client.user.name
    completion.MY_BOT_EXAMPLE_CONVOS = []
    for c in EXAMPLE_CONVOS:
        messages = []
        for m in c.messages:
            if m.user == "Lenard":
                messages.append(Message(user=client.user.name, text=m.text))
            else:
                messages.append(m)
        completion.MY_BOT_EXAMPLE_CONVOS.append(Conversation(messages=messages))
    await tree.sync()


# /chat
@tree.command(name="help", description="create private thread for you to chat with Upstreet Mods")
@discord.app_commands.checks.has_permissions(send_messages=True)
@discord.app_commands.checks.has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(send_messages=True)
@discord.app_commands.checks.bot_has_permissions(view_channel=True)
@discord.app_commands.checks.bot_has_permissions(manage_threads=True)
async def thread_command(int: discord.Interaction):
    try:
        # only support creating thread in text channel
        if not isinstance(int.channel, discord.TextChannel):
            return

        # block servers not in allow list
        if should_block(guild=int.guild):
            return
                        
        user = int.user
        try:
            embed = discord.Embed(
                title='Response will be sent on private thread!',
                description=f"{int.user.mention} be sure not to spam! ",
                color=discord.Color.green()
            )           

            await int.response.send_message(embed=embed)

            # create the thread
            thread = await int.channel.create_thread(
                name=f"{ACTIVATE_THREAD_PREFX} {int.user.name[:20]}",
                slowmode_delay=1,
                reason="gpt-bot",
                auto_archive_duration=60,
                invitable=True,
                type=None
            )

            await thread.send(f"Hello dear {int.user.mention}. Welcome to your private Help thread.")
            await thread.send(f"Let me invite <@!951854496844234843> to help you.")
        
            val = ({str(datetime.now())}, {str(int.user.id)})

            embed = discord.Embed(
                            color=discord.Color.green(),
                            title=f"Be advised with instructions:",
                            description=''
                        )
                
            embed.add_field(name='✅ Send here your questions:', value='This is a private thread for you to send all your questions regarding the current Redemption Phase.', inline=False)
            embed.add_field(name='👷 Ask for help:', value='You can ask for help from the team or from @thegen', inline=False)

            await thread.send(embed=embed)
        
        except Exception as e:
            logger.exception(e)
            await int.response.send_message(
                f"Failed to start chat, please try again. If the error continues reach out to moderators with specifications of when the error occured.", ephemeral=True
            )
            return

            await int.response.send_message(embed=embed)
        
    except Exception as e:
        logger.exception(e)
        await int.response.send_message(
            f"Failed to start chat, please try again. If the error continues reach out to moderators with specifications of when the error occured.", ephemeral=True
        )

client.run(DISCORD_BOT_TOKEN)
