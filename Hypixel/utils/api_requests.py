import aiohttp
import json
import base64
import io
from PIL import Image

async def request_hypixel(ctx, uuid, topic: str = "player", apikey: str = None):
    if not apikey:
        apikey = await ctx.cog.get_apikey(ctx.author)

    url = "https://api.hypixel.net/" + topic + "?key=" + apikey + "&uuid=" + str(uuid)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                resp = json.loads(await response.text())
            except json.JSONDecodeError:
                resp = {}

    return resp, response.status

async def request_mojang(username):
    url = "https://api.mojang.com/users/profiles/minecraft/" + str(username)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                resp = json.loads(await response.text())
        return resp, response.status
    except:
        return None, 400

async def save_skin(ctx, uuid):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://sessionserver.mojang.com/session/minecraft/profile/" + str(uuid)) as resp:
            content = json.loads(await resp.text())
    try:
        skin_array = content["properties"][0]["value"]
        skin_decode = json.loads((base64.b64decode(skin_array)).decode("utf-8"))
        skin_url = skin_decode["textures"]["SKIN"]["url"]

        async with aiohttp.ClientSession() as session:
            async with session.get(skin_url) as resp:
                im = Image.open(io.BytesIO(await resp.read()))

        im_file = io.BytesIO()
        im.save(im_file, format="PNG")
        im_bytes = im_file.getvalue()
        im_b64 = base64.b64encode(im_bytes).decode('ascii')
        return im_b64
    except KeyError:
        await ctx.send("Invalid UUID: Is your saved MC username up to date?")
        return None

async def request_valid_elements(gamemode):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://raw.githubusercontent.com/HypixelDatabase/HypixelTracking/master/API/player.json") as response:
            resp = json.loads(await response.text())
    stats = resp["player"]["stats"][gamemode]
    module_list = [key for key in stats if isinstance(stats[key], int) or isinstance(stats[key], str)]
    return module_list

async def append_custom_modules(custom_modules, gamemode):
    default_modules = await request_valid_elements(gamemode)

    for key in custom_modules.keys():
        default_modules.append(key)

    return default_modules
