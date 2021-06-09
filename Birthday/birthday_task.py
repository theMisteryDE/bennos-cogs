from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, pagify

from discord.ext import tasks
import discord
import datetime
import pytz
import asyncio

class Tasks():
    def start(self):
        if self.is_running():
            self.stop()
               
        self.task_main.start()

    def stop(self):
        self.task_main.cancel()

    def is_running(self):
        return self.task_main.is_running()

    async def initialize_guild_loops(self):
        self.time_for_guild_loops = {}
        async for guild in AsyncIter(self.bot.guilds):
            await self.update_time_for_guild(guild)

        self.start()

    async def update_time_for_guild(self, guild: discord.Guild):
        timezone = await self.config.guild(guild).timezone()
        now = datetime.datetime.now(pytz.timezone(timezone))

        utc_time_for_guild_loop: datetime.datetime = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(hour=0)) - now.utcoffset()

        self.time_for_guild_loops[guild.id] = utc_time_for_guild_loop.strftime("%Y-%m-%d.%H:%M:%S")

    @tasks.loop(seconds=120.0)
    async def task_main(self):
        async for guild in AsyncIter(self.bot.guilds): #type: discord.Guild
            guild: discord.Guild
            if await self.config.guild(guild).birthday_enabled():
                time_for_guild_loop = datetime.datetime.strptime(self.time_for_guild_loops[guild.id], "%Y-%m-%d.%H:%M:%S")
                time_for_guild_loop = pytz.timezone("utc").localize(time_for_guild_loop)

                if datetime.datetime.now(pytz.timezone("utc")) >= time_for_guild_loop:
                    await self.update_time_for_guild(guild)

                    channel = guild.get_channel(await self.config.guild(guild).channel())
                    role = guild.get_role(await self.config.guild(guild).role())

                    if channel != None:
                        bdays = await self.get_bdays(guild)

                        msg = ""
                        async for bday in AsyncIter(bdays):
                            now = datetime.datetime.now(pytz.timezone(await self.config.guild(guild).timezone()))
                            month = now.month
                            day = now.day

                            if (int(bday[1]) == int(day)) and (int(bday[2]) == int(month)):
                                bday_msg = await self.get_custom_message(bday[0])
                                msg += bday_msg + "\n\n"

                                if role != None:
                                    async for member in AsyncIter(role.members):
                                        member: discord.Member
                                        await member.remove_roles(role, reason="Birthday is over")

                                    async for bday in AsyncIter(bdays):
                                        if isinstance(bday[0], discord.Member):
                                            await bday[0].add_roles(role, reason="Birthday")  

                        if msg != "":
                            pages = list(pagify(msg, delims=["\n\n"]))
                            for page in pages:
                                embed = discord.Embed(color=discord.Color.blue(), description=page)
                                await channel.send(embed=embed)                  

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.update_time_for_guild(guild)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        if guild.id in self.time_for_guild_loops.keys():
            del self.time_for_guild_loops[guild.id]

    def cog_unload(self):
        self.stop()