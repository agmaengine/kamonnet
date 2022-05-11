import aiomcrcon
import asyncio

# TODO create agent service which control minecraft server service specifically
# the agent need to independently deployed on server
# this agent will allow other game to be deployed on the same server


class CredentialMinecraft:
    host: str
    port: int
    password: str

    def __init__(self, configuration: dict):
        creds = configuration["token"]["minecraft"]
        self.host = creds['host']
        self.port = int(creds['port'])
        self.password = creds['password']


class ClientMinecraft(aiomcrcon.Client):
    def __init__(self, credentials: CredentialMinecraft):
        super().__init__(host=credentials.host,
                         port=credentials.port,
                         password=credentials.password)

    async def connect_repeat(self, timeout=30, n_max=5):
        """

        :param timeout: in seconds for each connection
        :param n_max: number of repeating
        :return:
        """
        n = 0
        while True:
            try:
                await self.connect(timeout=timeout)
            except aiomcrcon.RCONConnectionError as e:
                # await messaging(ctx, "Connection timeout, unable to connect to rcon")
                print(e)
                if n >= n_max:
                    # await messaging(ctx, "be able to start the server, but cannot connect to the minecraft service")
                    return "cannot connect to the minecraft service"
                # await messaging(ctx, "retry")
            except aiomcrcon.IncorrectPasswordError as e:
                # await messaging(ctx, "Incorrect password")
                print(e)
                return "incorrect password"
            finally:
                if self._ready:
                    return "connected successfully"

            n += 1
            await asyncio.sleep(30)

    async def close(self):
        print("disconnected from rcon")

    async def get_online_player_number(self):
        response = await self.send_cmd("/list")
        player_number = int(response[0].split(" ")[2])
        return player_number
