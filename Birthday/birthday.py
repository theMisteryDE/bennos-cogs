from redbot.core import commands, Config
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.vendored.discord.ext import menus
from discord.ext.commands import RoleConverter

import discord
import datetime
import logging
import pytz
import asyncio
import operator
import json
from typing import Union

from .birthday_task import Tasks

class MenuSource(menus.ListPageSource):
    def __init__(self, data, name: str):
        self.name = name
        self.length = len(data)
        super().__init__(data, per_page=1)

    def is_paginating(self) -> bool:
        return True

    async def format_page(self, menu, page) -> discord.Embed:
        offset = menu.current_page * self.per_page
        ctx = menu.ctx

        if await ctx.embed_requested():
            embed = discord.Embed(color=await ctx.embed_color())
            embed.add_field(name=bold(self.name), value=page)
            embed.set_footer(text=f"Page {offset + 1}/{self.length}")
            
            return embed
        
class Birthday(commands.Cog, Tasks):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=365911945565569036)
        self.logger = logging.getLogger(("red.benno1237.birthdays"))
        
        default_guild = {
            "birthday_enabled": True,
            "timezone": "utc",
            "upcoming_first": False,
            "channel": None,
            "role": None,
            "allow_custom_messages": False,
            "custom_message_length": 100
        }

        default_user = {
            "birthday": None
        }

        self.default_member = {
            "birthday_enabled": True,
            "birthday_message": None
        }

        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.config.register_member(**self.default_member)

        self.start()

    def check(self, m, ctx, content: str):
        return m.content.lower() == content and m.author == ctx.author

    async def clear_data_for_user(self, user: Union[discord.User, discord.Member], guild: discord.Guild = None, clear_user: bool = True):
        if clear_user:
            await self.config.user(user).clear()

        if guild == None:
            async for guild in AsyncIter(self.bot.guilds):
                if user not in guild.users:
                    await self.config.member_from_ids(guild.id, user.id).clear()
        else:
            await self.config.member_from_ids(guild.id, user.id).clear()

    async def sort_bdays(self, bdays: list, mode: bool, guild: discord.Guild):
        passed = []
        upcoming = []

        now = datetime.datetime.now(pytz.timezone(await self.config.guild(guild).timezone()))

        for bday in bdays:
            if ((int(bday[1]) >= now.day) and (int(bday[2]) == now.month)) or (int(bday[2]) > now.month):
                upcoming.append(bday)
            else:
                try:
                    passed.append((bday[0], bday[1], bday[2], str(int(bday[3]) + 1)))
                except IndexError:
                    passed.append(bday)

        upcoming.sort(key=operator.itemgetter(2, 1))
        passed.sort(key=operator.itemgetter(2, 1))

        if mode: # Starting from the beginning of the year
            bdays = upcoming + passed
        else:
            bdays = passed + upcoming
        
        return bdays

    async def get_bdays(self, guild):
        bdays = []
        async for user, data in AsyncIter((await self.config.all_users()).items()):
            user = guild.get_member(user)
            if user != None:
                if await self.config.member_from_ids(user, guild.id).birthday_enabled():
                    if len(data["birthday"].split("-")) == 3:
                        d, m, y = data["birthday"].split("-")
                        current_year = datetime.datetime.now(pytz.timezone(await self.config.guild(guild).timezone())).year
                        age = current_year - int(y)
                        bdays.append((user, d, m, age))
                    else:
                        d, m = data["birthday"].split("-")
                        bdays.append((user, d, m))
        
        return bdays

    async def bday_to_datetime(self, bday: str, channel: discord.TextChannel):
        if len(bday.split("-")) == 2:
            split_string = "%d-%m"
        else:
            split_string = "%d-%m-%Y"

        try:
            datetime_obj = datetime.datetime.strptime(bday, split_string)
            return True
        except ValueError:
            await channel.send("Invalid format!")
            return False

    async def set_bday_for_user(self, bday, user):
        await self.config.user(user).birthday.set(bday)

    async def remove_bday_for_user(self, user):
        await self.config.user(user).clear()

    async def get_custom_message(self, user: Union[discord.User, discord.Member], msg: str = None, check: bool = False):
        now = datetime.datetime.now(pytz.timezone(await self.config.guild(user.guild).timezone()))
        bday = (await self.config.user(user).birthday()).split("-")
        if not msg:
            msg = await self.config.member(user).birthday_message()
        elif isinstance(user, discord.Member):
            if len(msg) > await self.config.guild(user.guild).custom_message_length():
                return "length"

        try:
            age = now.year - int(bday[2])
            if not msg:
                msg = "{mention} is getting {age} years old today! :partying_face:"
        except ValueError:
            if not msg:
                msg = "It's {mention}'s birthday today! :partying_face:"
            age = None
            if check:
                return "age"

        _allowed_tags = {"name": user.name, "full_name": str(user), "mention": user.mention, "age": age, "guild": user.guild.name, "date": now.date()}

        msg = msg.format(name=_allowed_tags["name"], full_name=_allowed_tags["full_name"], mention=_allowed_tags["mention"], guild=_allowed_tags["guild"], date=_allowed_tags["date"], age=_allowed_tags["age"])
        return msg    

    @commands.group(name="bday", aliases=["birthday"])
    async def bday(self, ctx):
        """Birthday settings"""

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday.command(name="channel")
    async def bday_channel(self, ctx, channel: discord.TextChannel):
        """Set the channel for daily birthday reminders"""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Bday channel is now set to {channel.mention}")
    
    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday.command(name="role")
    async def bday_role(self, ctx, role: RoleConverter):
        """Sets the birthday role
        
        Set the role which will be assigned on birthday"""

        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send(f"Birthday role is now set to `{role.name}`")

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday.command(name="timezone")
    async def bday_timezone(self, ctx, timezone):
        """Sets the timezone used for the reminder
        Defaults to UTC -> reminder is sent at 00:00 UTC
        
        *All timezones can be found here:*
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        `TZ database names` are required"""

        if not self.is_running():
            await ctx.send(":x: Main task is still starting up. Try again in a few seconds.")
        else:
            try:
                pytz.timezone(timezone)
                await self.config.guild(ctx.guild).timezone.set(timezone)
                await self.update_time_for_guild(ctx.guild)
                self.reset.set()
                await ctx.send(f"Server timezone is now set to: `{timezone}`\nCurrent local time: `{datetime.datetime.now(pytz.timezone(timezone)).time().strftime('%H:%M:%S')}`")
            except pytz.exceptions.UnknownTimeZoneError:
                await ctx.send(f"Timezone `{timezone}` is not valid.\nSee a list of all valid ones here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones (Note: `TZ database names` are required.")

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday.command(name="servertoggle")
    async def bday_servertoggle(self, ctx):
        """Toggles birthday reminders on this server"""
        current = await self.config.guild(ctx.guild).birthday_enabled()
        await self.config.guild(ctx.guild).birthday_enabled.set(not current)
        await ctx.send(f"Birthday reminder status on this server: `{not current}`")

    @commands.guild_only()
    @bday.command(name="toggle")
    async def bday_toggle(self, ctx):
        """Toggles the authors birthday reminder"""
        current = await self.config.member(ctx.author).birthday_enabled()
        await self.config.member(ctx.author).birthday_enabled.set(not current)
        await ctx.send(f"{ctx.author.mention}'s birthday reminders are now set to: `{not current}`")

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday.command(name="upcomingfirst")
    async def bday_sortingmode(self, ctx, mode: bool):
        """Default sorting mode for [p]bday list
        
        True: Upcoming birthdays are shown first in
        False: Starting from the beginning of the year"""

        await self.config.guild(ctx.guild).upcoming_first.set(mode)
        if mode == False:
            await ctx.send("Sorting will start from the beginning of the year.")
        else:
            await ctx.send("Upcoming birthdays are now shown first.")

    @commands.guild_only()
    @bday.group(name="custommsg")
    async def bday_custommsg(self, ctx):
        """Custom birthday message settings"""

    @commands.guild_only()
    @bday_custommsg.command(name="reset")
    async def bday_custommsg_reset(self, ctx):
        """Resets your custom message to the default one"""

        await self.config.member(ctx.author).birthday_message.set(None)
        await ctx.tick()

    @commands.guild_only()
    @bday_custommsg.command(name="show")
    async def bday_custommsg_show(self, ctx):
        """Shows your custom message"""

        current = await self.config.member(ctx.author).birthday_message()

        if current == None:
            await ctx.send("You do not have a custom message set yet. Use `[p]bday custommsg edit` to do so.")
        else:
            formatted = await self.get_custom_message(ctx.author, current)

            embed = discord.Embed(color=discord.Color.blue(), description=formatted)
            await ctx.send(embed=embed)

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday_custommsg.command(name="allow")
    async def bday_allowcustom(self, ctx, state: bool):
        """Allows custom birthday messages

        possible states (*bool*):
        `False:` custom messages aren't allowed 
        `True:` custom messages are allowed

        *Note:* can be quite config-heavy. Not recommended on larger bots."""

        await self.config.guild(ctx.guild).allow_custom_messages.set(state)

        if state == True:
            await ctx.send("Custom birthday messages are now allowed on this server!")
        else:
            await ctx.send("Custom birthday messages are now disabled.")

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday_custommsg.command(name="maxlength")
    async def bday_custommsg_maxlength(self, ctx, length: int):
        """Max length of custom birthday messages are

        Parameters:
        `lenth`: The max length you want to allow on this server in characters

        *Note:* can get quite config-heavy if the messages are too long."""

        await self.config.guild(ctx.guild).custom_message_length.set(length)
        await ctx.send(f"Max custom message length is now set to `{length}` chars")

    @commands.guild_only()
    @bday_custommsg.command(name="edit")
    async def bday_custommsg_edit(self, ctx):
        """Sets a custom birthday message"""

        if await self.config.guild(ctx.guild).allow_custom_messages() == True:
            if await self.config.user(ctx.author).birthday() == None:
                await ctx.send(":x: set your bday using `[p]bday set` first")
                return

            if await self.config.member(ctx.author).birthday_message() != None:
                msg = await self.get_custom_message(ctx.author)
                try:
                    maybe_delete = await ctx.send("You currently have a custom message set. Would you like to overwrite it?\nType `Yes` to confirm.")
                    await self.bot.wait_for("message", check=lambda message: self.check(m=message, ctx=ctx, content="yes"), timeout=30.0)

                except asyncio.TimeoutError:
                    try:
                        await maybe_delete.delete()
                    except:
                        pass
                    return

            try:
                await ctx.send(
                    "Enter new custom birthday message below.\n"
                    "For convenience reasons, there are a few dynamic tags included which will be auto formatted by the bot. See a list of them below: \n"
                    "```\n"
                    "name: The author's name\n"
                    "full_name: The author's name including discriminator (tag)\n"
                    "mention: Mentions the author\n"
                    "age: The users age (only usable if a year is set)\n" 
                    "guild: The guild's name\n"
                    "date: Today's date\n"
                    "```"
                    "**Note:** those tags have to be inside curly brackets `{}`\n\n"
                    "**Example usage:**\n"
                    "Wohoo it's {mention}'s birthday today, the {date}."
                )
                msg = await self.bot.wait_for("message", check=lambda message: message.author == ctx.author, timeout=60.0)
                formatted = await self.get_custom_message(ctx.author, msg=msg.content, check=True)
                if formatted == "age":
                    await ctx.send("Parameter `age` cannot be used without a birthday year set.")
                elif formatted == "length":
                    await ctx.send(f"Message exceeds the allowed length of `{await self.config.guild(ctx.guild).custom_message_length()}` chars")
                else:
                    embed = discord.Embed(color=discord.Color.blue(), description=formatted)
                    await ctx.send(embed=embed)
                    maybe_delete = await ctx.send("That's the formatted output of your message.\n`Yes` to confirm.")
                    
                    await self.bot.wait_for("message", check=lambda message: message.author == ctx.author, timeout=30)

                    try:
                        await self.config.member(ctx.author).birthday_message.set(msg.content)
                    except TypeError:
                        await ctx.send("Message is not json serializable. Maybe you used unsupported emotes?")
            except asyncio.TimeoutError:
                try:
                    await maybe_delete.delete()
                except:
                    pass
                return

        else:
            await ctx.send(":x: This server does not allow custom messages. You can ask the server mods for the reason.")

    @commands.guild_only()
    @bday.command(name="set")
    async def bday_set(self, ctx, bday: str):
        """Sets your birthday date

        Format: DD-MM-YYYY or DD-MM
        -> age will not be displayed if no year is given"""

        if await self.config.user(ctx.author).birthday() == None:
            if await self.bday_to_datetime(bday, ctx.channel):      
                await self.set_bday_for_user(bday, ctx.author)
                await ctx.send(f"Your birthday is now set to: `{bday}`")
        else:
            current = await self.config.user(ctx.author).birthday()
            maybe_delete = await ctx.send(f"Your birthday is already set! Would you like to overwrite it?\nType 'Yes' to confirm.\nCurrent birthday: `{current}`")
            try:
                await self.bot.wait_for("message", check=lambda message: self.check(m=message, ctx=ctx, content="yes"), timeout=30.0)
                if await self.bday_to_datetime(bday, ctx.channel):      
                    await self.set_bday_for_user(bday, ctx.author)
                    await ctx.send(f"Your birthday is now set to: `{bday}`")
            except asyncio.TimeoutError:
                try:
                    await maybe_delete.delete()
                except:
                    pass

    @commands.guild_only()
    @bday.command(name="remove")
    async def bday_remove(self, ctx):
        """Removes your birthday date"""

        if await self.config.user(ctx.author).birthday() != None:
            await self.remove_bday_for_user(ctx.author)
            await ctx.send("Birthday successfully removed")
        else:
            await ctx.send("No birthday set.")

    @commands.guild_only()
    @bday.command(name="list")
    async def bday_list(self, ctx, mode: bool = None):
        """Lists all birthdays"""

        if mode == None:
            mode = await self.config.guild(ctx.guild).upcoming_first()

        bdays = await self.get_bdays(ctx.guild)


        if bdays != []:
            bdays = await self.sort_bdays(bdays, mode, ctx.guild)

            msg = ""
            previous_month = None

            async for bday in AsyncIter(bdays):
                month = datetime.datetime(year=1, month=int(bday[2]), day=1).strftime("%B")
                if month != previous_month:
                    msg += f"\n{bold(month)}\n"
                    previous_month = month

                try:
                    msg += f"{bday[1]}: {bold(str(bday[0]))} - {bold(str(bday[3]))} years\n"
                except IndexError:
                    msg += f"{bday[1]}: {bold(str(bday[0]))}\n"

            pages = list(pagify(msg, delims=["\n\n"], page_length=1000))

            pages = menus.MenuPages(source=MenuSource(pages, "Birthday list"), clear_reactions_after=True)
            await pages.start(ctx)
        
        else:
            await ctx.send("No birthdays set on this server.")

    @commands.guild_only()
    @bday.group(name="cleardata", invoke_without_subcommand=True)
    async def bday_cleardata(self, ctx, all_guilds: bool = False, clear_user: bool = False):
        """Clears guild specific data for the current guild

        `all_guilds` clears guild specific data for all guilds
        `clear_user` clears global user data"""

        msg = await ctx.send('**Warning** this will permanently clear your data. Would you like to proceed?\nType "Yes" to proceed')
        try:
            await self.bot.wait_for("message", check=lambda message: self.check(m=message, ctx=ctx, content="yes"), timeout=30.0)

            if self.all_guilds:
                guild = None
            else:
                guild = ctx.guild

            await self.clear_data_for_user(ctx.author, guild=guild, clear_user=clear_user)
            await ctx.send("Done.")
        except asyncio.TimeoutError:
            await msg.delete()

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday_cleardata.command(name="user")
    async def bday_cleardata_user(self, ctx, user: discord.Member, all_guilds: bool = False, clear_user: bool = False):
        """Clears data for a given user

        `all_guilds` clears guild specific data for all guilds
        `clear_user` clears global user data"""

        if self.all_guilds:
            guild = None
        else:
            guild = ctx.guild

        await self.clear_data_for_user(user, guild=guild, clear_user=clear_user)
        await ctx.send("Done.")

    @commands.admin_or_permissions(administrator=True)
    @commands.guild_only()
    @bday_cleardata.command(name="custommsg")
    async def bday_cleardata_custommsg(self, ctx):
        """Clears all custom messages"""

        msg = await ctx.send('**Warning** this will permanently clear all custom messages. Would you like to proceed?\nType "Yes" to proceed')
        try:
            await self.bot.wait_for("message", check=lambda message: self.check(m=message, ctx=ctx, content="yes"), timeout=30.0) 

            member_conf = self.config._get_base_group(self.config.MEMBER)

            try:
                async with member_conf.all() as member_conf:
                    for member, data in member_conf[str(ctx.guild.id)].items():
                        data["birthday_message"] = None

                        if data == self.default_member:
                            del member_conf[str(ctx.guild.id)][member]

                await ctx.send("Done")
            except KeyError:
                await ctx.send(":x: This guild does not have any data configured yet")

        except asyncio.TimeoutError:
            await msg.delete()       

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.clear_data_for_user(user=member, guild=member.guild, clear_user=True)

            

                            
