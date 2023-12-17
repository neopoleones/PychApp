import aiohttp
from encryption_utils import encrypt_message, decrypt_message


async def send_message_to_srv(url, message):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=message) as response:
            return await response.text()

async def receive_message_from_srv(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

