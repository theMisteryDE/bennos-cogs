import discord
import asyncio
import logging
import time
import textwrap

from redbot.core import commands
from discord.ext import tasks
from discord.ext.commands import MemberConverter
from redbot.core.data_manager import bundled_data_path

from ..utils.wallpaper import Wallpaper
from ..utils import api_requests, general, command_checks
from ..utils.abc import MixinMeta, CompositeMetaClass

log = logging.getLogger("red.cogs.hypixel.autostats")

def exception_catching_callback(task):
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        log.error("Task autostats has encountered an error.", exc_info=exc)

class AutoStats():
    def __init__(self, user_list, gamemode, ctx):
        self.path = str(bundled_data_path(ctx.cog)) + "/"
        self.gamemode = gamemode
        self.user_list = user_list
        self.ctx = ctx
        self.previous_games_played = None
        self.message_list = []
        self.previous_stats = []
        self.wins = 0
        self.games_played = 0
        self.last_updated = time.time()
        self.game_start_time = 0
        self.gametype = ""

    async def is_updated(self):
        if self.gametype == "":
            self.gametype = (await general.read_json(self.path + "hypixel_dict_keys.json")).get(self.gamemode.lower()).get("gametype_value")

        if time.time() > (self.last_updated + 5400):
            await self.clear_messages()
            await self.ctx.send(f"Autostats for {self.ctx.author.display_name} cancelled due to inactivity.")
        
            if self.ctx.author in self.ctx.cog.guild_autostats_list.keys():
                del self.ctx.cog.guild_autostats_list[str(self.ctx.author)]
            else:
                del self.ctx.cog.user_autostats_list[str(self.ctx.author)]
            
            return False

        resp_stats, status = await api_requests.request_hypixel(self.ctx, self.user_list[0]["uuid"], topic="recentgames")

        if status == 200:
            for idx, item in enumerate(resp_stats["games"]):
                if self.gametype == item["gameType"]:
                    if item["date"] == self.game_start_time:
                        if item.get("ended") != None:
                            self.game_start_time = 0
                            self.last_updated = time.time()
                            return True
                    else:
                        if item.get("ended") == None:
                            if idx == 0:
                                temp = True if self.game_start_time != 0 else False
                                self.last_updated = time.time() if temp else self.last_updated
                                self.game_start_time = item["date"]
                                return temp
            else:
                return False

    async def fetch_stats(self):
        if self.message_list != []:
            await self.clear_messages()

        custom_json = await general.read_json(self.path + "hypixel_dict_keys.json")
        key_json = custom_json[self.gamemode.lower()]
        for idx, user in enumerate(self.user_list):
            resp_stats, status = await api_requests.request_hypixel(self.ctx, user["uuid"])
            if status == 200:
                gamemode_stats = resp_stats["player"]["stats"][key_json.get("stats_key")]
                name = resp_stats["player"]["playername"]
                statslist = await self.ctx.cog.modules_list_get(self.ctx, key_json.get("stats_key"), gamemode_stats)

                if (idx == 0) and (self.previous_stats != []):
                    if isinstance(key_json.get("wins_key"), list):
                        for k in key_json.get("wins_key"):
                            if gamemode_stats.get(k) != self.previous_stats[idx].get(k):
                                self.wins += 1
                    else:
                        self.wins = self.wins + 1 if gamemode_stats.get(key_json.get("wins_key")) != self.previous_stats[0].get(key_json.get("wins_key")) else self.wins
                    self.games_played += 1

                roundstats = []
                if len(self.previous_stats) < len(self.user_list):
                    self.previous_stats.append(gamemode_stats)
                else:
                    previous_statslist = await self.ctx.cog.modules_list_get(self.ctx, self.gamemode, self.previous_stats[idx])
                    roundstats = await general.calculate_summary_stats(previous_statslist, statslist)
                    self.previous_stats[idx] = gamemode_stats

                xp = gamemode_stats.get(key_json.get("xp_key"))

                if isinstance(user["name"], discord.Member):
                    color = await self.ctx.cog.config.user(user["name"]).header_color()
                    skin = await self.ctx.cog.config.user(user["name"]).skin()
                else:
                    color, skin = None, None
                
                im = await Wallpaper.create_img(statslist, name, self.path, user["uuid"], self.gamemode, xp, roundstats, header_color=color, skin_b64=skin)
                if idx == 0:
                    message = await general.send_img(im, self.ctx, self.wins, self.games_played)
                else:
                    message = await general.send_img(im, self.ctx)
                self.message_list.append(message)

    async def clear_messages(self):
        for msg in self.message_list:
            try:
                await msg.delete()
            except discord.NotFound:
                pass
        self.message_list.clear()

class AutoStatsCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.group(name="autostats", invoke_without_command=True)
    async def autostats(self, ctx, gamemode, *, username_list = None):
        """Starts autostats in specific gamemode
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
            if not await self.config_get(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower()):
                await ctx.send(f"No modules added for `{gamemode}`. Add a valid module before with `[p]module add`")
            else:
                user_list = []
                if username_list:
                    username_list = self.str_to_list(username_list)
                else:
                    username_list = [ctx.author]

                for idx, username in enumerate(username_list):
                    uuid, *_ = await self.get_user_data(ctx, username)
                    if uuid:
                        user_list.append({"name": username, "uuid": uuid})
                    else:
                        await ctx.send("Invalid usernames.")
                        break
                else:
                    if self.user_autostats_list.get(str(ctx.author)):
                        await ctx.send("You already have an autostats task running. Cancel it first.")
                    else:
                        if len(self.guild_autostats_list.keys()) >= 5:
                            if not await self.config.user(ctx.author).apikey():
                                await ctx.send("Already five autostats running on guild api key. Please set your own first.")
                                return
                        autostats = AutoStats(user_list, key_json[gamemode.lower()]["stats_key"], ctx)
                        task = asyncio.create_task(self.autostats_task(autostats, str(ctx.author)))
                        task.add_done_callback(exception_catching_callback)
                        apikey = await self.config.user(ctx.author).apikey()
                        if not apikey:
                            self.guild_autostats_list[str(ctx.author)] = task
                        else:
                            self.user_autostats_list[str(ctx.author)] = task
                        username_str = textwrap.indent('\n'.join(username_list), '\t•')
                        await ctx.send(f"Starting autostats for these users:\n```{username_str}```")

    @autostats.group(name="stop", invoke_without_command=True)
    async def autostats_stop(self, ctx):
        """Stops running autostats"""
        if str(ctx.author) in self.user_autostats_list.keys():
            del self.user_autostats_list[str(ctx.author)]

            if str(ctx.author) in self.guild_autostats_list.keys():
                del self.guild_autostats_list[str(ctx.author)]
            await ctx.send(f"Autostats for `{ctx.author.display_name}` cancelled")

        else:
            await ctx.send(f"No Autostats running for `{ctx.author.display_name}`")

    @autostats_stop.command(name="all")
    async def autostats_stop_all(self, ctx):
        """Stops all running autostats
        must be owner to execute this command"""
        if await self.bot.is_owner(ctx.author):
            if self.user_autostats_list:
                for task in self.user_autostats_list.values():
                    task.cancel()
                self.user_autostats_list.clear()
                await ctx.send("All running autostats processes stopped.")
            else:
                await ctx.send("No running autostats processes.")

        elif ctx.guild.owner == ctx.author:
            if self.guild_autostats_list:
                for task in self.guild_autostats_list.items():
                    if task[0].guild == ctx.guild:
                        task[1].cancel()

                await ctx.send("All running autostats processes which use the guild api key stopped.")
            else:
                await ctx.send("No running autostats processes which use the guild api key.")

    async def autostats_task(self, autostats, author):
        await autostats.fetch_stats()
        while True:
            if not self.user_autostats_list.get(author):
                break
            if await autostats.is_updated():
                await autostats.fetch_stats()
            await asyncio.sleep(10)
        await autostats.clear_messages()
