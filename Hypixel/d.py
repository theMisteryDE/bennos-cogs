import discord
from redbot.core import commands

class DiscordEvents:
    def cog_unload(self):
        for task in self.user_autostats_list.values():
            task.cancel()
        for task in self.guild_autostats_list.values():
            task.cancel()

    async def cog_before_invoke(self, ctx):
        user_apikey = await self.config.user(ctx.author).api_key()
        print(user_apikey)
        if not user_apikey:
            guild_apikey = await self.config.guild(ctx.guild).api_key()

            if not guild_apikey:
                print("Hello")
                raise commands.CheckFailure()
        else:
            pass

