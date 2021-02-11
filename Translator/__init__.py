from .translator import Translator
from redbot.core.bot import Red

def setup(bot: Red):
    bot.add_cog(Translator(bot))