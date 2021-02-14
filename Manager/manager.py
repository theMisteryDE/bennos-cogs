from redbot.core import commands, Config, checks
from redbot.core.data_manager import bundled_data_path
import aiohttp
import asyncio
import discord
import time
from pathlib import Path
from PIL import ImageFont, ImageDraw, Image
import numpy #needed
import random
import cv2 #needed opencv-python
import string
from collections.abc import Sequence

class Manager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12873686)

        default_guild = {
            "blacklisted_names": [],
            "ban_or_kick": "ignore",
            "captcha_mode": "None",
            "captcha_configured": False,
            "captcha_status": False,
            "captcha_activation_time": 0,
            "captcha_role": None,
            "allowed_users": 10,
            "allowed_time": 300,
            "time_since_reset": 0,
            "users_since_reset": 0,
            "captcha_cooldown": 900,
        }

        self.config.register_guild(**default_guild)

        self.fonts = []
        for font in Path(bundled_data_path(self) / "fonts").glob("**/*.ttf"):
            self.fonts.append(str(font))

        for captcha in Path(bundled_data_path(self) / "captchas").glob("**/*.png"):
            captcha.unlink()

    async def reset_captcha_conf(self, guild):
        conf = self.config.guild(guild)
        await conf.captcha_mode.set("None")
        await conf.captcha_configured.set(False)
        await conf.captcha_role.set(None)
        await conf.allowed_users.set(10)
        await conf.allowed_time.set(5)
        await conf.captcha_cooldown(900)

    def message_check(self, channel=None, author=None, content=None, ignore_bot=True, lower=True):
        channel = self.make_sequence(channel)
        author = self.make_sequence(author)
        content = self.make_sequence(content)
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

    def make_sequence(self, seq):
        if seq is None:
            return ()
        if isinstance(seq, Sequence) and not isinstance(seq, str):
            return seq
        else:
            return (seq,)

    async def create_captcha(self, captcha_text, length):
        '''credits to Siddhant Sadangi
        https://medium.com/better-programming/how-to-generate-random-text-captchas-using-python-e734dd2d7a51'''
        size = random.randint(100, 160)
        length_line = random.randint(80, 120)
        background = numpy.zeros(((size)+20, length*size, 3), numpy.uint8)
        background_pil = Image.fromarray(background+220)
        
        font = ImageFont.truetype(random.choice(self.fonts), size)
        draw = ImageDraw.Draw(background_pil)
        draw.text((5, 10), captcha_text, font=font, fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        draw.line([(random.choice(range(0 + size)), random.choice(range((size*2)+5))),(random.choice(range(length_line*size)), random.choice(range((size*2)+5)))], width=10, fill=(random.randint(120,255), random.randint(120,255), random.randint(120,255)))

        captcha = numpy.array(background_pil)
        thresh = random.randint(1,5)/100
        for i in range(captcha.shape[0]):
            for j in range(captcha.shape[1]):
                rdn = random.random()
                if rdn < thresh:
                    captcha[i][j] = random.randint(0,123)
                elif rdn > 1-thresh:
                    captcha[i][j] = random.randint(123,255)
        captcha = cv2.blur(captcha,(int(size/random.randint(10,20)),int(size/random.randint(10,30))))        
        #captcha.resize((300, 620))
        return captcha

    async def verified_role(self, ctx, response):
        guild = ctx.guild

        await ctx.send("Creating role `{}` and adding it to all users. This might take a while...".format(response.content))

        for role in guild.roles:
            if role.name == response.content:
                await role.delete()

        perms = discord.Permissions(send_messages=True, read_messages=True, create_instant_invite=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, read_message_history=True, send_tts_messages=True, connect=True, speak=True, stream=True, use_voice_activation=True, view_channel=True)
        captcha_role = await guild.create_role(name=response.content, permissions=perms)

        everyone_role = discord.utils.get(guild.roles, name="@everyone")
        perms_everyone = discord.Permissions(read_messages=False, view_channel=False)
        await everyone_role.edit(permissions=perms_everyone)

        try:
            for member in guild.members:
                await member.add_roles(captcha_role)
                await asyncio.sleep(0.3)

            await ctx.send("Successfully added the role `{}` to all users!".format(captcha_role.name))
            await ctx.send("Captchas are now enabled on this server!")
            await self.config.guild(guild).captcha_configured.set(True)

            await self.config.guild(guild).captcha_role.set(captcha_role.name)

        except (discord.HTTPException or discord.Forbidden) as e:
            await ctx.send("An error occured while adding the role to all users: \n`{}`".format(str(e)))
            await self.reset_captcha_conf(guild)      

    async def count_users(self, guild):
        conf = self.config.guild(guild)

        current_time = time.time()
        last_time = await conf.time_since_reset()
        allowed_time = await conf.allowed_time()

        if (current_time - last_time) <= allowed_time:
            allowed_users = await conf.allowed_users()

            users_since_reset = await conf.users_since_reset()
            users_since_reset += 1
            if users_since_reset > allowed_users:
                await conf.captcha_status.set(True)
                await conf.captcha_activation_time.set(current_time)
                await conf.time_since_reset.set(current_time)
                await conf.users_since_reset.set(0)
            else:
                await conf.users_since_reset.set(users_since_reset)
        else:
            await conf.time_since_reset.set(current_time)
            await conf.users_since_reset.set(0)

    @commands.group(name="banish")
    async def banish(self, ctx):
        """Manage the blacklist settings for this server"""
        pass

    @banish.command(name="add")
    async def banish_add(self, ctx, *, username):
        """Add a username to the blacklist"""
        guild = ctx.guild
        async with self.config.guild(guild).blacklisted_names() as current_blacklist:
            if username not in current_blacklist:
                current_blacklist.append(username)

                await ctx.send("Username `{}` successfully blacklisted!".format(username))

            else:
                await ctx.send("Username `{}` is already blacklisted. Use '[p]blacklist remove' to remove it.".format(username))

    @banish.command(name="remove")
    async def banish_remove(self, ctx, *, username):
        """Remove a username from the blacklist"""
        guild = ctx.guild

        async with self.config.guild(guild).blacklisted_names() as current_blacklist:
            if username not in current_blacklist:
                await ctx.send("Username `{}` is not blacklisted.".format(username))

            else:
                current_blacklist.remove(username)
                await ctx.send("Username `{}` removed from the blacklist.".format(username))

    @banish.command(name="list")
    async def banish_list(self, ctx):
        """Lists the current blacklisted usernames"""
        guild = ctx.guild

        current_blacklist = await self.config.guild(guild).blacklisted_names()
        current_action = await self.config.guild(guild).ban_or_kick()

        if not current_blacklist == []:
            blacklisted_usernames = ""
            for i in current_blacklist:
                blacklisted_usernames = blacklisted_usernames + "\n" + i
        else:
            blacklisted_usernames = "None"

        embed = discord.Embed(color=discord.Color.blue(), description="Blacklist")
        embed.add_field(name="current action", value=current_action, inline=False)
        embed.add_field(name="blacklisted usernames", value=blacklisted_usernames, inline=False)

        await ctx.send(embed=embed)

    @banish.group(name="set")
    async def banish_set(self, ctx):
        """Modify the blacklist settings"""
        pass

    @banish_set.command(name="kick_or_ban")
    async def banish_set_kick_or_ban(self, ctx, arg):
        """Action on join
        Choose what the bot should do if a member with blacklisted username joins.
        Valid options are kick/ban/ignore"""
        guild = ctx.guild
        valid_args = ["kick", "ban", "ignore"]
        arg = arg.lower()

        if arg.lower() in valid_args:
            await self.config.guild(guild).ban_or_kick.set(arg)
            await ctx.send("I will now `{}` users with blacklisted usernames on join.".format(arg))
        else:
            await ctx.send("Action is not valid. Valid actions are: \n`{}, {}, {}`".format(valid_args[0], valid_args[1], valid_args[2]))    

    @commands.group(name="captcha")
    async def captcha(self, ctx):
        """Modify the captcha settings"""

    @captcha.command(name="toggle")
    async def captcha_toggle(self, ctx):
        guild = ctx.guild
        current_status = await self.config.guild(guild).captcha_configured()

        if current_status == False:
            await ctx.send("Setting up some required stuff...")
            captcha_role = await self.config.guild(guild).captcha_role()
            print(captcha_role)
            if captcha_role == None:
                await ctx.send("At first, we need to create a role for verified users. Users without this role won't be able to see messages in this server.\nAll existing users will get the role added. \nEnter your desired name below (note: if the role already exists, it will get deleted, type 'cancel' to cancel the setup):")
                response = await self.bot.wait_for("message", check=self.message_check(channel=ctx.channel, author=ctx.author), timeout=30)
            else:
                captcha_role = discord.utils.get(guild.roles, name=captcha_role)
                if captcha_role != None:
                    await ctx.send("Role for verified users currently is `{}`. \nWould you like to delete it and add a new one? If not, setup will continue with the current one. `cancel` will cancel the setup. \ny/n".format(captcha_role.name))
                    response = await self.bot.wait_for("message", check=self.message_check(channel=ctx.channel, author=ctx.author), timeout=30)

                else:
                    await ctx.send("Old captcha role couldn't be found anymore, thus you have to set a new one up.\nEnter new name below:")
                    response = await self.bot.wait_for("message", check=self.message_check(channel=ctx.channel, author=ctx.author), timeout=30)

            if response.content.lower() == "cancel":
                await ctx.send("Cancelling and cleaning up...")
                await self.config.guild(guild).captcha_configured.set(False)

            elif ((response.content.lower() == "yes") or (response.content.lower() == "y")) and (captcha_role != None):
                await captcha_role.delete()
                await ctx.send("Role `{}` successfully deleted. Enter new rolename for verified users below:".format(captcha_role.name))
                response = await self.bot.wait_for("message", check=self.message_check(channel=ctx.channel, author=ctx.author))
                await self.verified_role(ctx, response)

            elif ((response.content.lower() == "no") or (response.content.lower() == "n")) and (captcha_role != None):
                perms = discord.Permissions(send_messages=True, read_messages=True, create_instant_invite=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, read_message_history=True, send_tts_messages=True, connect=True, speak=True, stream=True, use_voice_activation=True, view_channel=True)
                await captcha_role.edit(permissions=perms)
                everyone_role = discord.utils.get(guild.roles, name="@everyone")
                perms_everyone = discord.Permissions(read_messages=False, view_channel=False)
                await everyone_role.edit(permissions=perms_everyone)
                await ctx.send("Captchas are now enabled on this server!")
                await self.config.guild(guild).captcha_configured.set(True)

            else:
                await self.verified_role(ctx, response)

        else:
            await ctx.send("Captchas are now turned off for this server. \nWould you like to delete all data? \n y/n")
            response = await self.bot.wait_for("message", check=self.message_check(channel=ctx.channel, author=ctx.author))

            perms = discord.Permissions(send_messages=True, read_messages=True, create_instant_invite=True, embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True, read_message_history=True, send_tts_messages=True, connect=True, speak=True, stream=True, use_voice_activation=True, view_channel=True)                
            everyone_role = discord.utils.get(guild.roles, name="@everyone")
            await everyone_role.edit(permissions=perms)

            if (response.content.lower() == "yes") or (response.content.lower() == "y"):
                captcha_role = await self.config.guild(guild).captcha_role()
                captcha_role = discord.utils.get(guild.roles, name=captcha_role)

                if captcha_role in guild.roles:
                    try:
                        await captcha_role.delete()
                    except:
                        await ctx.send("Error while deleting role `{}`".format(captcha_role))

                await self.reset_captcha_conf(guild)
                await ctx.send("Data cleared and captchas disabled.")
                await self.config.guild(guild).captcha_configured.set(False)
            else:
                await self.config.guild(guild).captcha_configured.set(False)
                await ctx.send("Captchas are now disabled.")

    @captcha.command(name="mode")
    async def captcha_mode(self, ctx, mode):
        guild = ctx.guild
        args = ["threshold", "everyone", "none"]
        if mode.lower() in args:
            captcha_configured = await self.config.guild(guild).captcha_configured()
            await self.config.guild(guild).captcha_mode.set(mode.lower())
            await ctx.send("Captcha mode is now set to {}".format(mode))
            if captcha_configured == False:
                await ctx.send("**Warning**: Captchas are not enabled. Use `[p]captcha toggle`")
        else:
            await ctx.send("This mode is not valid. Valid modes are:\n```everyone:  captcha is shown to everyone on join\nthreshold:  captcha is shown if too many people join in a given period\nnone:  no captcha is shown```")

    @captcha.command(name="threshold")
    async def captcha_threshold(self, ctx, users: int, time: int, cooldown: int):
        """Set the threshold settings.
        Parameters: 
            users:      users that can join in a given period before the captcha gets activated (in sec)
            time:       the time period
            cooldown:   deactivation time once the captcha has been activated (in sec)"""
        conf = self.config.guild(ctx.guild)
        await conf.allowed_users.set(users)
        await conf.allowed_time.set(time)
        await conf.captcha_cooldown.set(cooldown)
        captcha_configured = await conf.captcha_configured()
        
        await ctx.send("Captcha will be activated if more than `{} users` join within `{} min`.\nAfter `{} min` it will deactivate again.".format(users, time/60, cooldown/60))
        if captcha_configured == False:
            await ctx.send("**Warning**: Captchas are not enabled. Use `[p]captcha toggle`")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        current_time = time.time()
        guild = member.guild
        username = member.name

        current_blacklist = await self.config.guild(guild).blacklisted_names()
        ban_or_kick = await self.config.guild(guild).ban_or_kick()
        captcha_configured = await self.config.guild(guild).captcha_configured()
        storage_path_captchas = bundled_data_path(self) / "captchas"
        captcha_mode = await self.config.guild(guild).captcha_mode()

        if captcha_mode == "threshold":
            await self.count_users(guild)
            print("check 1")
            captcha_status = await self.config.guild(guild).captcha_status()
            if captcha_status == True:
                print("check 2")
                captcha_activation_time = await self.config.guild(guild).captcha_activation_time()
                captcha_cooldown = await self.config.guild(guild).captcha_cooldown()
                if (current_time - captcha_activation_time) > captcha_cooldown:
                    print("check 3")
                    captcha_status = False
                    await self.config.guild(guild).captcha_status.set(False)

        elif captcha_mode == "everyone":
            captcha_status = True

        else:
            captcha_status = False

        print(captcha_status)

        if username in current_blacklist:
            if ban_or_kick == "kick":
                await member.kick(reason="Autokick due to blacklisted username.")
            elif ban_or_kick == "ban":
                await member.ban(reason="Autoban due to blacklisted username.")

        if (captcha_configured == True) and (captcha_status == False):
            role = discord.utils.get(guild.roles, name=await self.config.guild(guild).captcha_role())
            await member.add_roles(role)

        if captcha_configured and captcha_status:
            length = random.randint(4, 8)
            text = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(length))
            captcha = await self.create_captcha(text, length)
            cv2.imwrite(f"{storage_path_captchas}/{member}.png", captcha)

            embed = discord.Embed(color=discord.Color.blue(), description="Welcome to *{}*!".format(member.guild))
            embed.add_field(name="Why do I see this message?", value="You are required to complete the captcha below before being able to access the server. \n The captcha is case sensitive!")

            file = discord.File(fp=str(storage_path_captchas) + f"/{member}.png", filename=f"{member}.png")
            embed.set_image(url=f"attachment://{file.filename}")

            await member.send(embed=embed)
            await member.send(file=file)

            print(text)
            for i in range(3, 0, -1):
                try:
                    response = await self.bot.wait_for('message', check=self.message_check(channel=member.dm_channel), timeout=30)
                    if response.content == text:
                        await member.send("Captcha passed!")
                        role = discord.utils.get(guild.roles, name=await self.config.guild(guild).captcha_role())
                        await member.add_roles(role)
                        break
                    else:
                        await member.send("Wrong answer. {} tries left.".format(str(i - 1)))

                    if i == 1:
                        await member.send("Captcha failed. Rejoin to try again.")
                except asyncio.TimeouError:
                    await member.send("Timeout.")
                    break

            Path(str(storage_path_captchas) + f"/{member}.png").unlink()

    @commands.command()
    async def test(self, ctx):
        length = random.randint(4, 8)
        text = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(length))
        captcha = await self.create_captcha(text, length)

        storage_path_captchas = bundled_data_path(self) / "captchas"
        cv2.imwrite(f"{storage_path_captchas}/{ctx.author}.png", captcha)
        file = discord.File(fp=str(storage_path_captchas) + f"/{ctx.author}.png", filename=f"{ctx.author}.png")

        await ctx.author.send(file=file)

        for i in range(3, 0, -1):
            try:
                response = await self.bot.wait_for('message', check=self.message_check(channel=ctx.author.dm_channel), timeout=30)
                if response.content == text:
                    await ctx.author.send("Captcha passed!")
                    break
                else:
                    await ctx.author.send("Wrong answer. {} tries left.".format(str(i - 1)))

                if i == 1:
                    await ctx.author.send("Captcha failed. Rejoin to try again.")
            except asyncio.TimeouError:
                await ctx.author.send("Timeout.")
                break

        Path(str(storage_path_captchas) + f"/{ctx.author}.png").unlink()

    @commands.command()
    async def test2(self, ctx):
        self.task = self.bot.loop.create_task(self.initialize())