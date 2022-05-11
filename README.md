# kamonnet

Discord bot develop using **[discord.py](https://discordpy.readthedocs.io/en/latest/index.html#)** module
it was developed for starting a Minecraft server on demand using [Azure](https://portal.azure.com), Microsoft cloud service

## Minecraft server on demand
In order to do that, one need a discord bot, Azure virtual machine, Azure service principal client, 
and knowledge on how to start Minecraft on the machine automatically. 

## Setup Discord Bot
please refered to [this guide][1]

## Setup a Azure service principal Client and a Virtual Machine
service principal setup, please refered to [this guide][2]  
virtual machine setup, please refered to [this guide](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/quick-create-portal)

## Setup a Minecraft server \[java\]
Minecraft server can be downloaded from [this link](https://www.minecraft.net/en-us/download/server)
in order to run the Minecraft server you need java runtime which can be download from [this link](https://jdk.java.net)

note: for Minecraft version 1.18.2 you need jdk18 (java development kit 18)

\\ automatically start minecraft server section \\

## installation

cloning git
```
git clone https://github.com/agmaengine/kamonnet.git
```

create virtual environment
```
python -m venv .venv
```

### configure config.json
change the **config_template.json** file name to **config.json** 
fill the <> with valid keys

**discord token**, see [discord bot guide][1]  
azure **appId**, **password**, and **tanent**, see [service principal setup guide][2]  
azure machine {**resource_group**, **machine_name**} is the virtual machine information  
azure **subscription** is the subscription id that is used for allocating the resource group  
minecraft **host** is the ip address of the virtual machine hosting the server  
minecraft **port** is the rcon port can be found or set in **server.properties** rcon.port  
minecraft **password** is the rcon password can be found or set in **server.properties** rcon.password 

[1]: https://discordpy.readthedocs.io/en/latest/discord.html
[2]: https://docs.microsoft.com/en-us/azure/purview/create-service-principal-azure

### running bot
activate virtual environment
**bash**
```
source ./.venv/bin/activate
pip install -r requirements.txt
python main.py
```
**windows**
```
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

