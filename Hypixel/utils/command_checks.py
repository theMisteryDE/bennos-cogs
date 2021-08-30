from redbot.core import commands

def is_apikey():
    async def apikey_check(ctx):
        if await ctx.cog.config.guild(ctx.guild).apikey() or await ctx.cog.config.user(ctx.author).apikey():
            return True
        raise commands.UserFeedbackCheckFailure("Set an api key first.")
    return commands.check(apikey_check)

def is_username():
    async def username_check(ctx):
        if await ctx.cog.config.user(ctx.author).name():
            return True
        raise commands.UserFeedbackCheckFailure("Set a username first.")
    return commands.check(username_check)