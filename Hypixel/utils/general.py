from collections.abc import Sequence
from io import BytesIO
from os import path
import discord
import json
import aiofiles

def message_check(channel=None, author=None, content=None, ignore_bot=True, lower=True):
    channel = make_sequence(channel)
    author = make_sequence(author)
    content = make_sequence(content)
    if lower:
        content = tuple(c.lower() for c in content)
    def check(message):
        if ignore_bot and message.author.bot:
            return False
        if channel and message.channel not in channel:
            return False
        if author and message.author not in author:
            return False
        actual_content = message.content.lower() if lower else message.content
        if content and actual_content not in content:
            return False
        return True
    return check

def make_sequence(seq):
    if seq is None:
        return ()
    if isinstance(seq, Sequence) and not isinstance(seq, str):
        return seq
    else:
        return (seq,)

async def send_img(img, ctx, wins = None, games = None):
    with BytesIO() as image_binary:
        img.save(image_binary, "PNG")
        image_binary.seek(0)
        if (wins != None) and (games != None):
            message = await ctx.send(file=discord.File(fp=image_binary, filename="stats.png"), content=f"`Games Played:` {games}, `Wins:` {wins}")
        else:
            message = await ctx.send(file=discord.File(fp=image_binary, filename="stats.png"))
        return message

async def create_username_list(author, username_str):
    if not username_str:
        username_list = [author]
    else:
        username_list = username_str.split(" ")
    username_list = list(set(username_list))
    return username_list

async def read_json(path_and_name):
    async with aiofiles.open(path_and_name) as json_file:
        try:
            current_saved_stats = json.loads(await json_file.read())
        except json.decoder.JSONDecodeError:
            current_saved_stats = []
    return current_saved_stats

async def write_json(path_and_name, object_to_save):
    async with aiofiles.open(path_and_name, 'w') as json_file:
        await json_file.write(json.dumps(object_to_save))
        await json_file.flush()

async def calculate_summary_stats(previous_stats, current_stats):
    result_modules = [(current[0], current[1] - previous[1]) for current, previous in zip(current_stats, previous_stats)]
    return result_modules

async def xp_key_get(gamemode):
    if gamemode.lower() == "bedwars":
        return "Experience"
    elif gamemode.lower() == "skywars":
        return "skywars_experience"
    return None