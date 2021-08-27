from redbot.core import commands

def is_ll_started():
    async def ll_connection_check(ctx):
        if not ctx.cog.ll_running:
            await ctx.send("Connection to lavalink not established")
            return False
        return True
    return commands.check(ll_connection_check)