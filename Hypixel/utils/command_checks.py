from redbot.core import commands

def is_api_key():
    async def api_key_check(ctx):
        if await ctx.cog.config.guild(ctx.guild).api_key() or await ctx.cog.config.user(ctx.author).api_key():
            return True
        raise commands.UserFeedbackCheckFailure("Set an api key first.")
    return commands.check(api_key_check)

def is_username():
    async def username_check(ctx):
        if await ctx.cog.config.user(ctx.author).name():
            return True
        raise commands.UserFeedbackCheckFailure("Set a username first.")
    return commands.check(username_check)