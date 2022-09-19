import asyncio
import json
import logging
import datetime
import discord
from discord.ext import commands
import aiomcrcon
from azureutil import *
from minecraftutil import *


with open("./config.json", 'r') as f:
    configuration = json.load(f)


def timestamping(func):
    """
        timestamping decorators
        maybe there, built-in one in the logging need to check
    """
    nowstr = datetime.datetime.now().strftime("[%d-%m-%y %H:%M:%S]")
    print(f"{nowstr} ", end='', flush=True)
    func()


# discord
# discord_client = discord.Client()
discord_client = commands.Bot(command_prefix='.')
logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger('discord')
# logger.setLevel()

# Azure
azure_creds = CredentialAzure(configuration)
azure_machine_id = MachineIDAzure(configuration)
machine = MachineAzure(azure_machine_id, azure_creds)

# minecraft rcon
mc_creds = CredentialMinecraft(configuration)
mc_client = ClientMinecraft(mc_creds)


@discord_client.event
async def on_ready():
    print(f"logged into discord as {discord_client.user}")


async def messaging(ctx, text):
    print(text)
    if ctx is not None:
        await ctx.send(text)


@discord_client.command()
async def machine_status(ctx):
    status = await machine.status
    await messaging(ctx, f"{machine.key['id'][1]} is {status[3:]} on {machine.key['id'][0]}")


@commands.has_role("Bot Master")
@discord_client.command()
async def start_machine(ctx):
    result = -1
    try:
        result = await machine.start()
    except APITimeOutError:
        await messaging(ctx, "timeout")
    except Exception as e:
        print(e)
    finally:
        if result == 0:
            await messaging(ctx, "start machine successfully")
            return 0
        elif result == 1:
            await messaging(ctx, "machine is running")
            return 0

    await messaging(ctx, "machine state undetermined")


@commands.has_role("Bot Master")
@discord_client.command()
async def stop_machine(ctx):
    result = -1
    try:
        result = await machine.stop()
    except APITimeOutError:
        await messaging(ctx, "timeout")
    except Exception as e:
        print(e)
    finally:
        if result == 0:
            await messaging(ctx, "stop and deallocated machine successfully")
            return 0
        elif result == 1:
            await messaging(ctx, "machine is deallocated")
            return 0

        await messaging(ctx, "machine state undetermined")


async def _mc_start(ctx=None):
    result = await start_machine(ctx)
    if not (result == 0):
        await messaging(ctx, "cannot start the machine")
        return "cannot start machine"

    # wait for the server to be ready
    if await machine.status != "VM running":
        await asyncio.sleep(60)
    # try connect to the minecraft rcon
    result = await mc_client.connect_repeat()
    await messaging(ctx, result)
    # watching if there is any player ?
    n = 0
    await messaging(ctx, "machine will shutdown automatically, when there is no player on the server for 5 minutes")
    while n < 5:
        await asyncio.sleep(60)
        if await mc_client.get_online_player_number() > 0:
            n = 0
        else:
            n += 1
    # turn off machine
    await messaging(ctx, "there is no player online for 5 minutes. Shutting down the Server")
    save_response = await mc_client.send_cmd("/save-all")
    await messaging(ctx, f"server: {save_response[0]}")
    await mc_client.close()
    await stop_machine(ctx)


@commands.has_role("Bot Master")
@discord_client.command()
async def mc_rc_connect(ctx, connection_time=300):
    """connect bot to minecraft server console"""
    await mc_client.connect()
    await messaging(ctx, "connected to rcon")
    if connection_time >= 0:
        await asyncio.sleep(connection_time)
        await mc_client.close()
        await messaging(ctx, "disconnect from rcon")


@commands.has_role("Bot Master")
@discord_client.command()
async def mc_rc_close(ctx):
    """disconnect bot from minecraft server console"""
    await mc_client.close()
    await messaging(ctx, "disconnect from rcon")


@commands.has_any_role("Bot Master", "Player")
@discord_client.command()
async def mc_start(ctx):
    """start minecraft server, server will be shutdown if there is no player on the server for 5 minutes"""
    await _mc_start(ctx)


@discord_client.command()
async def get_online_player(ctx):
    """get number of currently online player on the server"""
    number_of_players = await mc_client.get_online_player_number()
    await messaging(ctx, f"online: {number_of_players}")


@commands.has_role("Bot Master")
@discord_client.command()
async def mc(ctx, command):
    """send command to the minecraft server console"""
    response = await mc_client.send_cmd(command)
    await messaging(ctx, f"{response}")
    print(response)


@commands.has_role("Bot Master")
@discord_client.command()
async def leave_guild(ctx, id):
    """leave a specified guild"""
    guild = discord_client.get_guild(id)
    guild.leave()
    await messaging(ctx, f"leaving guild: {id}")
    return 0


if __name__ == "__main__":
    # connect to discord
    asyncio.gather(discord_client.run(configuration['token']['discord']))
