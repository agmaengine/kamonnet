import asyncio
# from azure.common.credentials import ServicePrincipalCredentials
from azure.identity.aio import ClientSecretCredential
from azure.mgmt.compute.aio import ComputeManagementClient


# TODO There should be abstract interface to make it easier add more cloud API


class CredentialAzure:
    subscription_id: str
    credentials: ClientSecretCredential
    compute_client: ComputeManagementClient

    def __init__(self, configuration: dict):

        creds = configuration['token']['Azure']
        self.subscription_id = creds['subscription']
        self.credentials = ClientSecretCredential(
            client_id=creds['appId'],
            client_secret=creds['password'],
            tenant_id=creds['tenant']
        )
        self.compute_client = ComputeManagementClient(self.credentials, self.subscription_id)


class MachineIDAzure:
    resource_group: str
    machine_name: str

    def __init__(self, configuration: dict):
        self.resource_group = configuration['token']['Azure']['machine']['resource_group']
        self.machine_name = configuration['token']['Azure']['machine']['machine_name']


class APITimeOutError(Exception):
    """API calling timeout, the task result are not determined"""


class MachineAzure:

    def __init__(self, machine_id: MachineIDAzure, credentials: CredentialAzure):
        self.key = {
            "id": (machine_id.resource_group, machine_id.machine_name),
            "credentials": credentials,
        }
        # self.machine_controller = await credentials.compute_client.virtual_machines
        self.machine_controller = credentials.compute_client.virtual_machines

    async def get_state(self):
        machine_info = await self.machine_controller.get(*self.key["id"], expand='instanceView')
        return machine_info.instance_view.statuses[1].display_status  # machine status

    @property
    async def status(self):
        status = await self.get_state()
        return status

    async def start(self):
        if not (await self.get_state() == "VM running"):
            async_vm_start = await self.machine_controller.begin_start(*self.key["id"])  # starting machine
            await async_vm_start.wait()
            if not async_vm_start.done():
                raise APITimeOutError

            return 0  # machine successfully started

        return 1  # machine is running

    async def stop(self):
        if not (await self.get_state() == 'VM deallocated'):
            async_vm_deallocate = await self.machine_controller.begin_deallocate(*self.key["id"])
            await async_vm_deallocate.wait()
            if not async_vm_deallocate.done():
                raise APITimeOutError

            return 0  # machine successfully deallocated

        return 1  # machine is deallocated
