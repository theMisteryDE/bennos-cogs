from discord.ext.commands import MemberConverter
from redbot.core.data_manager import bundled_data_path
from redbot.core import commands
from ..utils.wallpaper import Wallpaper
from ..utils import api_requests, general, command_checks
import discord

class StatsCommands():
    async def username_to_uuid(self, ctx, username):
        uuid = None
        if isinstance(username, str):
            resp_mojang, status_mojang = await api_requests.request_mojang(username)

        if status_mojang != 200 or isinstance(username, discord.Member):
            #Direct request failed, trying to convert the username to a Member object first

            try:
                username = await MemberConverter().convert(ctx, username)
                uuid = await self.config.user(username).uuid()
                if not uuid:
                    await ctx.send(f"User {username.mention} doesn't seem to have a mc name set yet.")
                    return
            except discord.ext.commands.BadArgument:
                await ctx.send(f"{username} is neither a valid mc name or Member of this server.")

        else:
            uuid = resp_mojang["id"]

        return uuid

    async def username_to_stats(self, ctx, username, gamemode):
        uuid = await self.username_to_uuid(ctx, username)
        if uuid != None:
            resp_hypixel, status_hypixel = await api_requests.request_hypixel(ctx, uuid)

            if status_hypixel != 200:
                await ctx.send(f"Something went wrong: \n`{resp_hypixel['cause']}`")
                return None, None, None
            else:
                try:
                    return resp_hypixel["player"]["stats"][gamemode], resp_hypixel["player"]["playername"], uuid
                except (KeyError, TypeError):
                    await ctx.send(f"Player `{username}` has `never played {gamemode}` or has `turned API off`")
                    return None, None, None

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

    async def create_stats_wallpaper(self, ctx, username_str, gamemode):
        username_list = await general.create_username_list(ctx.author, username_str)

        for username in username_list:
            async with ctx.typing():
                gamemode_stats, minecraft_name, uuid = await self.username_to_stats(ctx, str(username), gamemode)

                if gamemode_stats:
                    modules_list = await self.modules_list_get(ctx, gamemode, gamemode_stats)
                    
                    if modules_list != []:
                        xp = gamemode_stats.get(await general.xp_key_get(gamemode))

                        try:
                            if not isinstance(username, discord.Member):
                                username = await MemberConverter().convert(ctx, username)
                            color = await self.config.user(username).color()
                            color = (int(c) for c in color) if color else None
                            skin_b64 = await self.config.user(username).skin()
                        except discord.ext.commands.BadArgument:
                            color, skin_b64 = None, None

                        data_path = str(bundled_data_path(self)) + "/"
                        im = await Wallpaper.create_img(modules_list, minecraft_name, data_path, uuid, gamemode, xp=xp, header_color=color, skin_b64=skin_b64)
                        
                        await general.send_img(im, ctx)

    @commands.command(name="stats")
    async def stats(self, ctx, gamemode, *, username_list = None):
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
            await self.create_stats_wallpaper(ctx, username_list, gamemode)

    @commands.command(name="gamemodes")
    async def gamemodes(self, ctx):
        """Shows all possible gamemodes"""
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
        embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
        await ctx.send(embed=embed)