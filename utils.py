import aiohttp
import random

async def get_roblox_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"usernames": [username], "excludeBannedUsers": True}) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data["data"]:
                    return data["data"][0]["id"]
    return None

async def get_roblox_description(user_id):
    url = f"https://users.roblox.com/v1/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("description", "")
    return None

import string

def generate_verification_code(length=12):
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))
