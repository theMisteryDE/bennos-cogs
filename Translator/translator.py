from redbot.core import commands, Config, checks
import json
import aiohttp
import discord
from typing import Union, Optional

supported_languages = {'af': 'afrikaans', 'sq': 'albanian', 'am': 'amharic', 'ar': 'arabic', 'hy': 'armenian', 'az': 'azerbaijani', 'eu': 'basque', 'be': 'belarusian', 'bn': 'bengali', 'bs': 'bosnian', 'bg': 'bulgarian', 'ca': 'catalan', 'ceb': 'cebuano', 'ny': 'chichewa', 'zh-cn': 'chinese (simplified)', 'zh-tw': 'chinese (traditional)', 'co': 'corsican', 'hr': 'croatian', 'cs': 'czech', 'da': 'danish', 'nl': 'dutch', 'en': 'english', 'eo': 'esperanto', 'et': 'estonian', 'tl': 'filipino', 'fi': 'finnish', 'fr': 'french', 'fy': 'frisian', 'gl': 'galician', 'ka': 'georgian', 'de': 'german', 'el': 'greek', 'gu': 'gujarati', 'ht': 'haitian creole', 'ha': 'hausa', 'haw': 'hawaiian', 'iw': 'hebrew', 'he': 'hebrew', 'hi': 'hindi', 'hmn': 'hmong', 'hu': 'hungarian', 'is': 'icelandic', 'ig': 'igbo', 'id': 'indonesian', 'ga': 'irish', 'it': 'italian', 'ja': 'japanese', 'jw': 'javanese', 'kn': 'kannada', 'kk': 'kazakh', 'km': 'khmer', 'ko': 'korean', 'ku': 'kurdish (kurmanji)', 'ky': 'kyrgyz', 'lo': 'lao', 'la': 'latin', 'lv': 'latvian', 'lt': 'lithuanian', 'lb': 'luxembourgish', 'mk': 'macedonian', 'mg': 'malagasy', 'ms': 'malay', 'ml': 'malayalam', 'mt': 'maltese', 'mi': 'maori', 'mr': 'marathi', 'mn': 'mongolian', 'my': 'myanmar (burmese)', 'ne': 'nepali', 'no': 'norwegian', 'or': 'odia', 'ps': 'pashto', 'fa': 'persian', 'pl': 'polish', 'pt': 'portuguese', 'pa': 'punjabi', 'ro': 'romanian', 'ru': 'russian', 'sm': 'samoan', 'gd': 'scots gaelic', 'sr': 'serbian', 'st': 'sesotho', 'sn': 'shona', 'sd': 'sindhi', 'si': 'sinhala', 'sk': 'slovak', 'sl': 'slovenian', 'so': 'somali', 'es': 'spanish', 'su': 'sundanese', 'sw': 'swahili', 'sv': 'swedish', 'tg': 'tajik', 'ta': 'tamil', 'te': 'telugu', 'th': 'thai', 'tr': 'turkish', 'uk': 'ukrainian', 'ur': 'urdu', 'ug': 'uyghur', 'uz': 'uzbek', 'vi': 'vietnamese', 'cy': 'welsh', 'xh': 'xhosa', 'yi': 'yiddish', 'yo': 'yoruba', 'zu': 'zulu'}

class Translator(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=42069)
        self.request_url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={}&tl={}&q={}"

        default_global = {
            "reactions": {}
        }

        default_guild = {
            "reactions": {},
            "use_global_reactions": False,
            "status": False
        }

        default_channel = {
            "autotrans_status": False,
            "autotrans_dest_lang": None
        }

        self.config.register_global(**default_global)
        self.config.register_guild(**default_guild)
        self.config.register_channel(**default_channel)

    async def translate_message(self, message, dest_lang, src_lang = "auto"):
        """Translating the messages.
        Using a custom forked google translate API link."""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.request_url.format(src_lang, dest_lang, message)) as resp:
                trans_dict = json.loads(await resp.text())

        trans_msg = trans_dict["sentences"][0]["trans"]
        src_lang = trans_dict["src"]
        conf = trans_dict["confidence"] * 100

        return trans_msg, src_lang, conf

    async def create_embed_status_autotrans(self, channel):
        """Creating the "autotrans" status embed.
        Cleaning the main code up."""

        embed = discord.Embed(
            color = discord.Color.blue(),
            description = "Autotranslate")

        embed.add_field(name="Status: ", value= str(await self.config.channel(channel).autotrans_status()), inline=False)
        embed.add_field(name="Destination Language: ", value= supported_languages[str(await self.config.channel(channel).autotrans_dest_lang())], inline=False)

        return embed

    async def create_embed_status_reactions(self, guild):
        """Creating the "reactions" status embed.
        Cleaning the main code up."""

        embed = discord.Embed(
            color = discord.Color.blue(),
            description = "Reaction settings")

        embed.add_field(name="Status: ", value= str(await self.config.guild(guild).status()), inline=False)
        embed.add_field(name="Use global reactions: ", value=await self.config.guild(guild).use_global_reactions(), inline=False)

        return embed

    async def create_embed_translated(self, trans_message, dest_lang, src_lang, conf):
        """Creating an embed for the look of the translated message.
        Cleaning the main code up."""

        embed = discord.Embed(
            color = discord.Color.blue(),
            description = "Translator")
        
        embed.add_field(name="Translated message to {}:".format(supported_languages[dest_lang]), value=trans_message, inline=False)
        embed.add_field(name="Translated from:", value=supported_languages[src_lang] + " \n Detected with a confidence of {}%".format(conf), inline=False)

        return embed

    @checks.mod()
    @commands.group()
    async def autotrans(self, ctx):
        """Modify the channels autotranslate settings.
        Translated by Google Translate.
        """
        pass

    @autotrans.command(name="status")
    async def autotrans_status(self, ctx):
        """Get the current autotranslate status and destination language of this channel."""
        channel = ctx.channel
        
        await ctx.send(embed=await self.create_embed_status_autotrans(channel))

    @autotrans.command(name="toggle")
    async def autotrans_toggle(self, ctx):
        """Toggle autotranslate for this channel"""
        channel = ctx.channel
        current = await self.config.channel(channel).autotrans_status()

        new = not current

        await self.config.channel(channel).autotrans_status.set(new)

        await ctx.send(embed=await self.create_embed_status_autotrans(channel))
    
    @autotrans.command(name="lang")
    async def autotrans_dest_lang(self, ctx, lang):
        """Set the destination language for this channel"""
        channel = ctx.channel

        if not lang in supported_languages:
            await ctx.send("This language is not valid. You can get a list of supported ones here: \n https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages")

        else:
            await self.config.channel(channel).autotrans_dest_lang.set(lang)
            await ctx.send(embed=await self.create_embed_status_autotrans(channel))

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        """Wait for message.
        If autotranslate is activated, translate and send an embed"""
        channel = message.channel
        status = await self.config.channel(channel).autotrans_status()
        dest_lang = await self.config.channel(channel).autotrans_dest_lang()
        prefix, *_ = await self.bot.get_valid_prefixes(message.guild)

        if (status) and (dest_lang != None) and (message.content.startswith(prefix) == False) and (message.author.name != "Arc-Bot"):
            trans_msg, src_lang, conf = await self.translate_message(message.content, dest_lang)
            
            await channel.send(embed=await self.create_embed_translated(trans_msg, dest_lang, src_lang, conf))

    @checks.mod()
    @commands.group()
    async def reaction(self, ctx):
        """Modify the available local reactions.
        Might be buggy with custom emojis atm."""

        pass

    @reaction.group(name="add")
    async def reaction_add(self, ctx):
        "Add a reaction to the global/guild list."
        pass

    @reaction_add.command(name="guild")
    async def reaction_add_guild(self, ctx, reaction: Union[discord.Emoji, str], dest_lang):
        """Add an emoji/reaction for a language to the guild list."""
        if dest_lang not in supported_languages:
            await ctx.send("This destination language is not valid. You can find a list of supported ones here: \n https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages")

        else:
            guild = ctx.guild
            current = await self.config.guild(guild).reactions()

            if reaction not in current:
                async with self.config.guild(ctx.guild).reactions() as current: 
                    current[reaction] = dest_lang

                await ctx.send("{} is now translating to {}".format(reaction, supported_languages[dest_lang]))
            else:
                dest_lang = current[reaction]
                await ctx.send("{} is already there and translating to {}".format(reaction, supported_languages[dest_lang]))

    @checks.is_owner()
    @reaction_add.command(name="global")
    async def reaction_add_global(self, ctx, reaction: Union[discord.Emoji, str], dest_lang):
        """Add an emoji/reaction for a language to the global list"""
        if dest_lang not in supported_languages:
            await ctx.send("This destination language is not valid. You can find a list of supported ones here: \n https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages")
 
        else:
            current = await self.config.reactions()

            if reaction not in current:
                async with self.config.reactions() as current:
                    current[reaction] = dest_lang

                await ctx.send("{} is now translating to {}".format(reaction, supported_languages[dest_lang]))
            else:
                dest_lang = current[reaction]
                await ctx.send("{} is already there and translating to {}".format(reaction, supported_languages[dest_lang]))

    @reaction.group(name="remove")
    async def reaction_remove(self, ctx):
        """Remove a reaction from the global/guild list."""
        pass

    @reaction_remove.command(name="guild")
    async def reaction_remove_guild(self, ctx, reaction: Union[discord.Emoji, str]):
        """Remove an emoji/reaction for a language from the guild list."""
        guild = ctx.guild
        current = await self.config.guild(guild).reactions()

        if reaction in current:
            current.pop(reaction)
            await self.config.guild(guild).reactions.set(current)

            await ctx.send("Sucessfully removed: {}".format(reaction))

        else:
            await ctx.send("Reaction is not saved in the guild specific list. Might be in the global list?")

    @checks.is_owner()
    @reaction_remove.command(name="global")
    async def reaction_remove_global(self, ctx, reaction: Union[discord.Emoji, str]):
        """Remove an emoji/reaction for a language from the global list."""
        current = await self.config.reactions()

        if reaction in current:
            current.pop(reaction)
            await self.config.reactions.set(current)

            await ctx.send("Successfully removed: {}".format(reaction))

        else:
            await ctx.send("Reaction is not a saved in the global list. Might be in the guild specific list?")

    @reaction.group(name="set")
    async def reaction_set(self, ctx):
        """Modify the reaction-translator settings"""
        pass

    @reaction_set.command(name="toggle_global_list")
    async def reaction_set_toggle_global_list(self, ctx):
        """Turn the global reactions list on/off for this server."""
        guild = ctx.guild
        global_list_status = not await self.config.guild(guild).use_global_reactions()
        await self.config.guild(guild).use_global_reactions.set(global_list_status)

        await ctx.send(embed=await self.create_embed_status_reactions(guild))

    @reaction_set.command(name="toggle_status")
    async def reaction_set_toggle_status(self, ctx):
        """Turn the reaction-translator on/off for this server."""
        guild = ctx.guild
        status = not await self.config.guild(guild).status()
        await self.config.guild(guild).status.set(status)

        await ctx.send(embed=await self.create_embed_status_reactions(guild))        

    @reaction.command(name="status")
    async def reaction_settings(self, ctx):
        """Get this guilds current reaction-translator settings"""
        await ctx.send(embed=await self.create_embed_status_reactions(ctx.guild))

    @reaction.command(name="list")
    async def reaction_list(self, ctx):
        """Lists all available reactions and their destination language."""
        guild = ctx.guild
        global_status = await self.config.guild(guild).use_global_reactions()

        if global_status:
            global_reactions = await self.config.reactions()
            embed_global = discord.Embed(color=discord.Color.blue(), description="Global reactions")

            if global_reactions:
                global_emoji = ""
                global_dest_lang = ""
                for reaction in global_reactions:
                    global_emoji = (global_emoji + "\n" + reaction)
                    global_dest_lang = (global_dest_lang + "\n" + supported_languages[global_reactions[reaction]])
                
                embed_global.add_field(name="Emoji:", value=global_emoji, inline=True)
                embed_global.add_field(name="Translating to:", value=global_dest_lang, inline=True)
        
        guild_reactions = await self.config.guild(guild).reactions()
        if guild_reactions:
            embed_guild = discord.Embed(color=discord.Color.blue(), description="Guild reactions")
            guild_emoji = ""
            guild_dest_lang = ""
            for reaction in guild_reactions:
                guild_emoji = (guild_emoji + "\n" + reaction)
                guild_dest_lang = (guild_dest_lang + "\n" + supported_languages[guild_reactions[reaction]])

            embed_guild.add_field(name="Emoji:", value=guild_emoji, inline=True)
            embed_guild.add_field(name="Translating to:", value=guild_dest_lang, inline=True)

        pages = [embed_global, embed_guild]

        message = await ctx.send(embed=embed_guild)
        await message.add_reaction('◀')
        await message.add_reaction('▶')

        def check(reaction, user):
            return user == ctx.author
 
        i = 0
        reaction = None

        while True:
            if str(reaction) == '◀':
                if i > 0:
                    i -= 1
                else:
                    i = (len(pages) -1)
                await message.edit(embed = pages[i])
            elif str(reaction) == '▶':
                if i < (len(pages) -1):
                    i += 1
                else:
                    i = 0
                await message.edit(embed = pages[i])
            
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout = 60.0, check = check)
                await message.remove_reaction(reaction, user)
            except:
                break

        await message.clear_reactions()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        channel = message.channel
        status = await self.config.guild(message.guild).status()

        if status:
            valid_guild_reactions = await self.config.guild(message.guild).reactions()

            if await self.config.guild(message.guild).use_global_reactions():
                valid_global_reactions = await self.config.reactions()
        
            else:
                valid_global_reactions = {}

            if ((reaction.emoji in valid_guild_reactions) or (reaction.emoji in valid_global_reactions)):
                try:
                    async with self.config.reactions() as valid_global_reactions:
                        dest_lang = valid_global_reactions[reaction.emoji]
                except:
                    async with self.config.guild(message.guild).reactions() as valid_guild_reactions:
                        dest_lang = valid_guild_reactions[reaction.emoji]

                trans_msg, src_lang, conf = await self.translate_message(message.content, dest_lang)
                await channel.send(embed=await self.create_embed_translated(trans_msg, dest_lang, src_lang, conf))

    @commands.command(name="translate")
    async def translate(self, ctx, dest_lang, *, message: str):
        '''translates a given message'''
        trans_msg, src_lang, conf = await self.translate_message(message, dest_lang)
        await ctx.send(embed=await self.create_embed_translated(trans_msg, dest_lang, src_lang, conf))        
