import asyncio
import json
import logging
import datetime
import discord
from discord.ext import commands
import aiomcrcon
# from azure.common.credentials import ServicePrincipalCredentials
from azure.identity.aio import ClientSecretCredential
from azure.mgmt.compute.aio import ComputeManagementClient


with open("./config.json", 'r') as f:
    configuration = json.load(f)


def timestampping(func):
    nowstr = datetime.datetime.now().strftime("[%d-%m-%y %H:%M:%S]")
    print(f"{nowstr} ", end='', flush=True)
    func()


# discord
# discord_client = discord.Client()
discord_client = commands.Bot(command_prefix='.')
logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger('discord')
# logger.setLevel()


@discord_client.event
async def on_ready():
    print(f"logged into discord as {discord_client.user}")


# @discord_client.event
# async def on_message(message):
#     if message.author == discord_client.user:
#         return
#
#     print(message.author)
#     print(message.channel)
#     print(message.content)
#     if message.channel.name == "test-on-production":
#         await message.channel.send("Hi")
#         # if message.author.dm_channel is None:
#         #     await message.author.create_dm()
#         # await message.author.dm_channel.send("Stop bulling me!")

# Azure
creds = configuration['token']['Azure']

subscription_id = creds['subscription']
credentials = ClientSecretCredential(
    client_id=creds['appId'],
    client_secret=creds['password'],
    tenant_id=creds['tenant']
)
compute_client = ComputeManagementClient(credentials, subscription_id)
rg = "mycoolresourcegroup-sea"
vm = "my-cool-generic-server"


async def messaging(ctx, text):
    print(text)
    if ctx is not None:
        await ctx.send(text)


async def get_machine_state(resource_group, machine_name):
    cool_machine = await compute_client.virtual_machines.get(resource_group, machine_name, expand='instanceView')
    vm_state = cool_machine.instance_view.statuses[1].display_status
    return vm_state


# @discord_client.command()
# async def counting(ctx):
#     n=0
#     while n < 500:
#         print(n)
#         await asyncio.sleep(1)
#         n += 1

async def _machine_status(ctx=None):
    status = await(get_machine_state(rg, vm))
    status = f"{vm} is {status[3:]} on {rg}"
    await messaging(ctx, status)


async def _start_machine(ctx=None):
    if await get_machine_state(rg, vm) == "VM running":
        await messaging(ctx, "the machine is running")
        return True, 'running'
    else:
        async_vm_start = await compute_client.virtual_machines.begin_start(rg, vm)
        await messaging(ctx, "starting machine")

        await async_vm_start.wait()
        if async_vm_start.done():
            await messaging(ctx, "machine had started")
            return True, 'started'
        else:
            await messaging(ctx, "command timeout")
            return False


async def _stop_machine(ctx=None):
    if await get_machine_state(rg, vm) == 'VM deallocated':
        await messaging(ctx, "machine is deallocated")
        return True
    else:
        async_vm_deallocate = await compute_client.virtual_machines.begin_deallocate(rg, vm)
        await messaging(ctx, "deallocating machine")

        await async_vm_deallocate.wait()
        if async_vm_deallocate.done():
            await messaging(ctx, "machine had deallocated")
            return True
        else:
            await messaging(ctx, "command timeout")
            return False


@discord_client.command()
async def machine_status(ctx):
    await _machine_status(ctx)


@commands.has_role("Bot Master")
@discord_client.command()
async def start_machine(ctx):
    await _start_machine(ctx)


@commands.has_role("Bot Master")
@discord_client.command()
async def stop_machine(ctx):
    await _stop_machine(ctx)


# minecraft rcon

creds = configuration["token"]["minecraft"]
creds['port'] = int(creds['port'])
mc_client = aiomcrcon.Client(host=creds['host'],
                             port=creds['port'],
                             password=creds['password'])


async def _get_online_player_number(ctx=None):
    response = await mc_client.send_cmd("/list")
    player_number = int(response[0].split(" ")[2])
    # await messaging(ctx, f"server: {response[0]}")
    # print(player_number)
    return player_number


async def _mc_start(ctx=None):
    success, state = await _start_machine(ctx)
    if success:
        # wait for the server to be ready
        if state == "started":
            await asyncio.sleep(60)
        # try connect to the minecraft rcon
        n = 0
        while True:
            try:
                await mc_client.connect(timeout=30)
            except aiomcrcon.RCONConnectionError as e:
                await messaging(ctx, "Connection timeout, unable to connect to rcon")
                if n >= 5:
                    await messaging(ctx, "be able to start server, but cannot to the minecraft service")
                    return "cannot connect to minecraft service"
                else:
                    await messaging(ctx, "retry")
                    print(e)
            except aiomcrcon.IncorrectPasswordError as e:
                await messaging(ctx, "Incorrect password")
                print(e)
                return "incorrect password"
            else:
                await messaging(ctx, "successfully connected to rcon")
                break

            n += 1
            await asyncio.sleep(30)
    else:
        await messaging(ctx, "cannot start the machine")
        return "cannot start machine"

    # watching if there is any player ?
    n = 0
    await messaging(ctx, "machine will shutdown automatically, when there is no player on the server for 5 minutes")
    while n < 5:
        await asyncio.sleep(60)
        if await _get_online_player_number() > 0:
            n = 0
        else:
            n += 1
    # turn off machine
    await messaging(ctx, "there is no player online for 5 minutes. Shutting down Server")
    save_response = await mc_client.send_cmd("/save-all")
    await messaging(ctx, f"server: {save_response[0]}")
    await mc_client.close()
    await _stop_machine(ctx)


@commands.has_role("Bot Master")
@discord_client.command()
async def mc_rc_connect(ctx, connection_time=300):
    await mc_client.connect()
    await messaging(ctx, "connected to rcon")
    if connection_time >= 0:
        await asyncio.sleep(connection_time)
        await mc_client.close()
        await messaging(ctx, "disconnect from rcon")


@commands.has_role("Bot Master")
@discord_client.command()
async def mc_rc_close(ctx):
    await mc_client.close()
    await messaging(ctx, "disconnect from rcon")


@commands.has_role("Bot Master")
@discord_client.command()
async def mc_start(ctx):
    await _mc_start(ctx)


@discord_client.command()
async def get_online_player(ctx):
    number_of_players = _get_online_player_number(ctx)
    await messaging(ctx, f"online: {number_of_players}")


@commands.has_role("Bot Master")
@discord_client.command()
async def mc(ctx, command):
    response = await mc_client.send_cmd(command)
    print(response)


if __name__ == "__main__":
    # connect to discord
    asyncio.gather(discord_client.run(configuration['token']['discord']))
