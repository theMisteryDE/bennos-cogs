import discord
import datetime
import pytz
from os import remove

from redbot.core import commands
from redbot.core.data_manager import bundled_data_path

from ..utils import api_requests

class ChangeConfig():
    async def config_set(self, guild, dict, subdict, value):
        try:
            async with getattr(self.config.guild(guild), dict)() as dict:
                dict[subdict] = value
        except AttributeError:
            raise AttributeError(f"dictionary not found:\n{dict} / {subdict}")

    async def config_get(self, guild, dict, subdict = None):
        try: 
            async with getattr(self.config.guild(guild), dict)() as dict:
                if subdict == None:
                    return dict
                else:
                    return dict[subdict]
        except AttributeError:
            raise AttributeError(f"dictionary not found:\n{dict} / {subdict}")

    @commands.group(name="enter")
    async def enter(self, ctx):
        """Save utils to:
            make sure all commands are available
            speed other commands up"""
        pass

    @commands.dm_only()
    @enter.command(name="apikey")
    async def enter_apikey(self, ctx, api_key, guild: discord.Guild = None):
        """Set your api key
        Must be set in order to activate the other commands
        can be obtained by typing `/api` on hypixel
        guild (optional): The guild to set the api key for. If this is given
        the key is seen as a guild key and is thus used by all users of said guild
        who dont have a personal key set
        """
        resp, status = await api_requests.request_hypixel(ctx, "test", apikey=api_key)
        if status == 403:
            await ctx.send(f"Something went wrong: \n`{resp['cause']}`")
        else:
            if guild:
                await self.config.guild(guild).api_key.set(api_key)
                await ctx.send("Api key set")
            else:
                await self.config.user(ctx.author).api_key.set(api_key)
                await ctx.send("Api key set")
            
    @enter.command(name="username")
    async def enter_username(self, ctx, username):
        """Set your MC username
        username will be saved as uuid
        to speed other commands up"""
        resp, status = await api_requests.request_mojang(username)
        if status != 200:
            await ctx.send(f"Adding username `{username}` failed. Maybe it is not valid?")
        else:
            await self.config.user(ctx.author).name.set(username)
            await self.config.user(ctx.author).uuid.set(resp["id"])

            await ctx.send(f"Set your MC name to `{username}`")
        
    @enter.command(name="skin")
    async def enter_skin(self, ctx):
        """Save your current MC Skin
        to speed other commands up"""
        uuid = await self.config.user(ctx.author).uuid()
        if uuid != None:
            skin = await api_requests.save_skin(ctx, uuid)
            if skin != None:
                await self.config.user(ctx.author).skin.set(skin)
                await ctx.send(f"Saved your skin")
        else:
            await ctx.send("Set your username first with [p]enter username")

    @enter.command(name="timezone")
    async def enter_timezone(self, ctx, timezone: str):
        """Set your personal timezone
        Useful for the `[p]summary` commands
        All available timezones: 
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        ^ `TZ database names` are required"""
        try:
            tz = pytz.timezone(timezone)
            time = datetime.datetime.now(tz).strftime("%H:%M:%S")
            await self.config.user(ctx.author).timezone.set(timezone)
            await ctx.send(f"Personal timezone set to `{timezone}`.\nCurrent Time: `{time}`")
        except pytz.exceptions.UnknownTimeZoneError:
            await ctx.send("Timezone is not valid. See a list of all supported ones here:\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones\n^ `TZ database names` are required")

    @enter.command(name="color")
    async def enter_color(self, ctx, *, color):
        """Enter your unique color for
        playername on wallpaper
        could be html color (length must be 6)
        or R, G, B value
        splits by ',' or ' '"""
        if ("," in color) or (" " in color):
            color = color.replace("(", "").replace(")", "").replace(" ", "")
            if "," in color:
                color = color.split(",")
            else:
                color = color.split(" ")
            if "" in color:
                color.remove("")
            if len(color) == 3:
                for v in color:
                    if not ((int(v) >= 0) and (int(v) <= 255)):
                        await ctx.send("At least one value is invalid. Must be between `0 - 255`")
                        break
                else:
                    color = tuple((int(color[0]), int(color[1]), int(color[2])))
            else:
                await ctx.send("Too many or to less values for (R, G, B)")
    
        else:
            color = color.replace("#", "")
            if len(color) == 6:
                color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

        if isinstance(color, tuple):
            await self.config.user(ctx.author).color.set(color)
            await ctx.send("Color saved")
        else:
            await ctx.send("Color not saved. Please check your input")

    @commands.group(name="reset")
    async def reset(self, ctx):
        """Reset something you saved before"""
        pass

    @reset.command(name="apikey")
    async def reset_apikey(self, ctx, reset_type = "user"):
        """Reset current api key
        reset_type (optional): guild, user"""
        if reset_type == "user":
            await self.config.user(ctx.author).api_key.set(None)
            await ctx.send("Player api key resetted")
        elif reset_type == "guild":
            if ctx.author == ctx.guild.owner:
                await self.config.guild(ctx.guild).api_key.set(None)
                await ctx.send("Guild Api key resetted")
            else:
                await ctx.send("You must be guild owner to do this")
        else:
            await ctx.send("save type is invalid. `guild` or `user` is valid")

    @reset.command(name="username")
    async def reset_username(self, ctx):
        """Reset your current username"""
        await self.config.user(ctx.author).name.set(None)
        await self.config.user(ctx.author).uuid.set(None)

        await ctx.send("Username resetted")

    @reset.command(name="skin")
    async def reset_skin(self, ctx):
        """Reset your current saved skin"""
        uuid = await self.config.user(ctx.author).uuid()
        if uuid != None:
            try:
                remove(str(bundled_data_path(self)) + "/skins/" + uuid + ".png")
                await ctx.send("Removed your current skin file")
            except FileNotFoundError:
                await ctx.send("No saved skin for your username")
        else:
            await ctx.send("Set your username first with [p]enter username")

    @reset.command(name="color")
    async def reset_color(self, ctx):
        """Reset your current saved color"""
        color = await self.config.user(ctx.author).color()
        if color != None:
            await self.config.user(ctx.author).color.set(None)
            await ctx.send("Current color removed")
        else:
            await ctx.send("No saved color")