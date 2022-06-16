import typing
import socket
import subprocess
from ipaddress import ip_address, IPv4Address
import httpx
import re
import copy


class MacAddress:
    _address: str
    _compressed: str
    _compressed_dash: str

    def __init__(self, mac_address_str: str):
        assert re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address_str.lower()), "input mac address format is not correct"
        self._address = mac_address_str
    
    def __repr__(self):
        return f"<MacAddress {self._compressed}>"

    def to_bytes(self):
        return bytes.fromhex(self.compressed)

    @property
    def compressed(self):
        if '-' in self._address:
            return self._address.replace('-', ':').lower()
        return self._address.lower()

    @property
    def compressed_dash(self):
        if ':' in self._address:
            return self._address.replace(':', '-').lower()
        return self._address.lower()



def macstr2bytes(mac_address_str: str) -> bytes:
    """convert mac address string like ff:ff:ff:ff:ff:ff to bytes format"""
    # format checking
    # if there is five colons (":") separater
    assert re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac_address_str.lower()), "input mac address format is not correct"
    return bytes.fromhex(mac_address_str)


def wol(mac_address: str, ip: str='255.255.255.255', port: int=9):
    """
    turn target machine on with wake-on-lan protocol
    wake-on-lan does not work on a Wireless Network
    controller must connected to the same LAN network as target the machine
    """
    mac_address = macstr2bytes(mac_address)
    magic = b'\xff' * 6 + mac_address * 16
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    
    s.sendto(magic, (ip, port))
    s.close()


def poweroff_ssh(ip_str: str, username: str, password: str):
    """
    power off machine functionality
    this function require a lot of setup on controller
    the controller need to have authentication key for ssh to the target machine
    consult 
    https://www.ssh.com/academy/ssh/key or 
    https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server
    for more information about ssh key authentication

    sudo plivilege of the machine is required meaning sudo username and password are needed to be stored on the controller host
    not that secure tbh
    """
    ip = ip_address(ip_str) # this function will do validation for ip
    subprocess.run(['ssh', f'{username}@{ip.compressed}', 'sudo', '-S', 'poweroff'], input=password.encode)


def wol(mac_address: MacAddress, ip: IPv4Address=ip_address('255.255.255.255'), port: int=9):
    """
    turn target machine on with wake-on-lan protocol
    wake-on-lan does not work on a Wireless Network
    controller must connected to the same LAN network as target the machine
    """
    assert type(ip) is IPv4Address, "only support ipv4"
    magic = b'\xff' * 6 + mac_address.to_bytes() * 16
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    
    s.sendto(magic, (ip.compressed, port))
    s.close()


# the local machine need to be instance
class AgentMachine(httpx.AsyncClient):
    """
    machine_agent deployed on the target machine for
    monitoring machine status and
    managing predetermined programs on the taget machine.
        to control the programs agent configuration is required
        this will limit the ability of Kamonnet to control the machine directly
    """
    def __init__(
        self, 
        target_ip_str: str, 
        domain_name: typing.Optional[str] =None,
        *args, 
        **kwargs
    ):
        self.ip = ip_address(target_ip_str)
        self.domain_name = domain_name
        super().__init__(base_url=f"http://{self.domain_name or self.ip}:8000", *args, **kwargs)

    async def status(self):
        return await self.get('/machine')


class LocalAgentMachine(AgentMachine):
    mac_address: MacAddress

    def __init__(
        self,
        target_ip_str: str,
        domain_name: typing.Optional[str]=None,
        mac_address: typing.Optional[str]=None,
        *args,
        **kwargs
    ):
        super().__init__(
            target_ip_str, 
            domain_name=domain_name,
            *args,
            **kwargs
            )
        self.mac_address = MacAddress(mac_address)

    async def start_machine(self):
        wol()