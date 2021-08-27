from redbot.core.data_manager import bundled_data_path
from redbot.core import commands
from discord.ext.commands import MemberConverter
import discord
import json
import time
import datetime
import pytz
import base64
from PIL import Image
import io
import re
from ..utils.wallpaper import Wallpaper
from ..utils import general, command_checks, api_requests

class SummaryStatsCommands():
    async def save_stats(self, ctx, username_str, gamemode):
        username_list = await general.create_username_list(ctx.author, username_str)
        current_saved_stats = await general.read_json(str(bundled_data_path(self)) + "/summaries/summary.json")

        if not ctx.author.guild_permissions.administrator:
            if len(username_list) > 1:
                if username_list[0] != str(ctx.author):
                    await ctx.send("You must be admin to save stats for other players.")
                    return

        for username in username_list:
            gamemode_stats, minecraft_name, uuid = await self.username_to_stats(ctx, username, gamemode)

            if gamemode_stats != None:
                try:
                    if not isinstance(username, discord.Member):
                        username = await MemberConverter().convert(ctx, username)
                    timezone = await self.config.user(username).timezone()
                    time = datetime.datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d %H:%M:%S")
                    username = username.display_name
                except discord.ext.commands.BadArgument:
                    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                temp_dict = {
                    'uuid': uuid,
                    gamemode: (gamemode_stats, time)
                }

                for idx, item in enumerate(current_saved_stats):
                    if uuid == item['uuid']:
                        message = "Overwrote" if gamemode in item else "Saved"
                        current_saved_stats[idx][gamemode] = temp_dict[gamemode]
                        break
                else:
                    current_saved_stats.append(temp_dict)
                    message = "Saved"

                await ctx.send(f"{message} `{username}`'s current `{gamemode}` stats")

        await general.write_json(str(bundled_data_path(self)) + "/summaries/summary.json", current_saved_stats)

    async def show_summary_stats(self, ctx, username_str, gamemode):
        username_list = await general.create_username_list(ctx.author, username_str)
        saved_stats = await general.read_json(str(bundled_data_path(self)) + "/summaries/summary.json")

        if saved_stats != []:
            for username in username_list:
                gamemode_stats, minecraft_name, uuid = await self.username_to_stats(ctx, username, gamemode)
                if gamemode_stats != None:
                    current_stats = await self.modules_list_get(ctx, gamemode, gamemode_stats)

                    try:
                        if not isinstance(username, discord.Member):
                            username = await MemberConverter().convert(ctx, username)
                        skin_b64 = await self.config.user(username).skin()
                        color = await self.config.user(username).color()
                        username = username.display_name
                    except discord.ext.commands.BadArgument:
                        skin_b64, color = None, None

                    xp = gamemode_stats.get(await general.xp_key_get(gamemode))

                    for item in saved_stats:
                        if uuid == item['uuid']:
                            if gamemode in item:
                                previous_stats = await self.modules_list_get(ctx, gamemode, item[gamemode][0])
                                compared_stats = await general.calculate_summary_stats(previous_stats, current_stats)
                                await ctx.send(f"Compare current stats for `{username}` in `{gamemode}` to stats at `{item[gamemode][1]}`.")
                                break
                    else:
                        await ctx.send(f"No saved stats for `{username}` in `{gamemode}`. Show only current stats instead.")

                    im = await Wallpaper.create_img(current_stats, minecraft_name, str(bundled_data_path(self)) + "/", uuid, gamemode, xp, compared_stats, skin_b64 = skin_b64, header_color=color)
                    await general.send_img(im, ctx)

    async def reset_summary_stats(self, ctx, username_str, gamemode):
        username_list = await general.create_username_list(ctx.author, username_str)

        if not ctx.author.guild_permissions.administrator:
            if len(username_list) > 1:
                if username_list[0] != str(ctx.author):
                    await ctx.send("You must be admin to save stats for other players.")
                    return

        current_saved_stats = await general.read_json(str(bundled_data_path(self)) + "/summaries/summary.json")

        if current_saved_stats != []:
            for idx, username in enumerate(username_list):
                uuid = await self.username_to_uuid(ctx, username)
                if uuid != None:
                    try:
                        if not isinstance(username, discord.Member):
                            username = await MemberConverter().convert(ctx, username)
                        username = username.display_name
                    except discord.ext.commands.BadArgument:
                        pass
                    for idx, item in enumerate(current_saved_stats):
                        if item['uuid'] == uuid:
                            if gamemode in item:
                                current_saved_stats[idx].pop(gamemode)
                                if len(current_saved_stats[idx]) == 1:
                                    del current_saved_stats[idx]
                                await ctx.send(f"Removed `{username}`'s saved `{gamemode}` stats")
                            else:
                                await ctx.send(f"No saved stats for `{username}` in `{gamemode}`")
                            break
                    else:
                        await ctx.send(f"No saved stats for `{username}`")
                        
            await general.write_json(str(bundled_data_path(self)) + "/summaries/summary.json", current_saved_stats)
        else:
            await ctx.send("No saved stats")

    @commands.group(name="summary")
    async def summary(self, ctx):
        pass

    @summary.command(name="start")
    async def summary_start(self, ctx, gamemode, *, username_list = None):
        """Save current stats in specific gamemode
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
            await self.save_stats(ctx, username_list, gamemode)

    @summary.command(name="show")
    async def summary_show(self, ctx, gamemode, *, username_list = None):
        """Show current stats in specific gamemode compared to start stats
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
            await self.show_summary_stats(ctx, username_list, gamemode)

    @summary.group(name="reset", invoke_without_command=True)
    async def summary_reset(self, ctx, gamemode, *, username_list = None):
        """Reset saved stats for specific gamemode
        to clear all saved stats: [p]summary reset all
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
            await self.reset_summary_stats(ctx, username_list, gamemode)

    @summary_reset.command(name="all")
    @commands.is_owner()
    async def summary_reset_all(self, ctx):
        """resets saved summary config"""
        with open(str(bundled_data_path(self)) + '/summaries/summary.json', 'w') as json_file:
            json.dump([], json_file)
        await ctx.send("Cleared saved stats")