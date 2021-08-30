import discord

from redbot.core import commands

from .utils.abc import MixinMeta, CompositeMetaClass

class DiscordEvents(MixinMeta, metaclass=CompositeMetaClass):
    def cog_unload(self):
        for task in self.user_autostats_list.values():
            task.cancel()
        for task in self.guild_autostats_list.values():
            task.cancel()

    async def cog_before_invoke(self, ctx):
        if self.enter in [ctx.command, ctx.command.root_parent]:
            return

        apikey = await self.get_apikey(ctx.author)
        if not apikey:
            raise commands.UserFeedbackCheckFailure("There is no server or personal apikey set.")
