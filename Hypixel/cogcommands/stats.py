import discord

from typing import List, Union

from discord.ext.commands import MemberConverter
from redbot.core.data_manager import bundled_data_path
from redbot.core import commands

from ..utils.wallpaper import Wallpaper
from ..utils import api_requests, general, command_checks
from ..utils.abc import MixinMeta, CompositeMetaClass

class StatsCommands(MixinMeta, metaclass=CompositeMetaClass):
    async def get_apikey(self, author: Union[discord.User, discord.Member]):
        apikey = await self.config.user(author).apikey()
        if not apikey and isinstance(author, discord.Member):
            apikey = await self.config.guild(author.guild).apikey()

        return apikey if apikey else None

    def str_to_list(self, string: str) -> List:
        username_list = string.split(" ")

        username_list = list(set(username_list))
        return username_list

    async def get_user_data(self, ctx, username):
        default_color = tuple(await self.config.guild(ctx.guild).header_color())
        if isinstance(username, str):
            resp_mojang, status_mojang = await api_requests.request_mojang(username)
            if status_mojang == 200:
                uuid = resp_mojang["id"]
                color = default_color
                skin = None

            else:
                #Direct request failed, trying to convert the username to a Member object first
                try:
                    username = await MemberConverter().convert(ctx, username)
                except discord.ext.commands.BadArgument:
                    return ctx.send(f"Username {username} doesn't seem to be valid")

                user_data = await self.config.user(username).all()
                uuid = user_data["uuid"]
                color = tuple(user_data["header_color"]) if user_data["header_color"] else default_color
                skin = user_data["skin"]

                if not uuid:
                    await ctx.send(f"User {username.mention} doesn't seem to have a mc name set yet.")
                    return
        else:
            user_data = await self.config.user(username).all()
            uuid = user_data["uuid"]
            color = tuple(user_data["header_color"]) if user_data["header_color"] else default_color
            skin = user_data["skin"]

            if not uuid:
                await ctx.send(f"User {username.mention} doesn't seem to have a mc name set yet.")
                return
        return uuid, color, skin

    async def uuid_to_stats(self, ctx, uuid, gamemode):
        resp_hypixel, status_hypixel = await api_requests.request_hypixel(ctx, uuid)

        if status_hypixel != 200:
            await ctx.send(f"Something went wrong: \n`{resp_hypixel['cause']}`")
            raise ValueError
        else:
            return resp_hypixel["player"]["stats"][gamemode], resp_hypixel["player"]["playername"]

    async def modules_list_get(self, ctx, gamemode, gamemode_stats):
        modules_list = []
        enabled_elements = await self.config_get(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower())
        custom_modules = await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower())
        for item in enabled_elements:
            if item[0] in custom_modules.keys():
                try:
                    result = eval(custom_modules[item[0]])
                    modules_list.append((item[1], result))
                except KeyError:
                    modules_list.append((item[1], 0))

            else:
                try:
                    modules_list.append((item[1], gamemode_stats[item[0]]))
                except KeyError:
                    modules_list.append((item[1], 0))
        if modules_list == []:
            await ctx.send(f"No modules added for `{gamemode}`. Add a valid module before with `[p]module add`")
        return modules_list

    async def create_stats_wallpaper(self, ctx, username_str: str, gamemode):
        if username_str:
            username_list = self.str_to_list(username_str)
        else:
            username_list = [ctx.author]

        failed = []

        for username in username_list:
            async with ctx.typing():
                uuid, color, skin_b64 = await self.get_user_data(ctx, username)
                if not uuid:
                    continue

                try:
                    gamemode_stats, minecraft_name = await self.uuid_to_stats(ctx, uuid, gamemode)
                except (KeyError, ValueError):
                    failed.append(username)
                    continue

                modules_list = await self.modules_list_get(ctx, gamemode, gamemode_stats)

                if modules_list:
                    xp = gamemode_stats.get(await general.xp_key_get(gamemode))

                    data_path = str(bundled_data_path(self)) + "/"
                    im = await Wallpaper.create_img(modules_list, minecraft_name, data_path, uuid, gamemode, xp=xp, header_color=color, skin_b64=skin_b64)

                    await general.send_img(im, ctx)

    @commands.command(name="stats")
    async def stats(self, ctx, gamemode, *, usernames: str = None):
        """Shows current stats in specific gamemode
        username_list:
            default: yourself
            optional: one ore more player (dc or mc name)
                leave spaces between players
        to show gamemode list:
            [p]gamemodes
        """
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.create_stats_wallpaper(ctx, usernames, gamemode)

    @commands.command(name="gamemodes")
    async def gamemodes(self, ctx):
        """Shows all possible gamemodes"""
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
        embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
        await ctx.send(embed=embed)