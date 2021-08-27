from redbot.core import commands, Config

from . import cogcommands
from .d import DiscordEvents

class Hypixel(commands.Cog, cogcommands.CogCommands):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=69420)
        self.message_list = []
        self.user_autostats_list = {}
        self.guild_autostats_list = {}

        default_user = {
            "name": None,
            "uuid": None,
            "color": None,
            "timezone": None,
            "skin": None,
            "api_key":None
        }

        default_guild = {
            "api_key": None,
            "bedwars": {
                "enabled_modules_bedwars": [
                    ("games_played_bedwars", "Games played"),
                    ("kills_bedwars", "Kills"),
                    ("normal_kd", "KD"),
                    ("beds_broken_bedwars", "Beds broken"),
                    ("wins_bedwars", "Wins"),
                    ("winstreak", "Winstreak"),
                    ("final_kills_bedwars", "Final kills"),
                    ("final_kd", "Final KD")
                ],
                "custom_modules_bedwars": {
                    "wl_rate": "round((gamemode_stats['wins_bedwars'] / gamemode_stats['losses_bedwars']), 2)",
                    "normal_kd": "round((gamemode_stats['kills_bedwars'] / gamemode_stats['deaths_bedwars']), 2)",
                    "final_kd": "round((gamemode_stats['final_kills_bedwars'] / gamemode_stats['final_deaths_bedwars']), 2)",
                }
            },
            "skywars": {
                "enabled_modules_skywars": [

                ],
                "custom_modules_skywars": {

                }
            },
            "hungergames": {
                "enabled_modules_hungergames": [

                ],
                "custom_modules_hungergames": {

                }
            },
            "mcgo": {
                "enabled_modules_mcgo": [

                ],
                "custom_modules_mcgo": {

                }
            },
            "arena": {
                "enabled_modules_arena": [

                ],
                "custom_modules_arena": {

                }
            },
            "arcade": {
                "enabled_modules_arcade": [

                ],
                "custom_modules_arcade": {

                }
            },
            "uhc": {
                "enabled_modules_uhc": [

                ],
                "custom_modules_uhc": {

                }
            },
            "speeduhc": {
                "enabled_modules_speeduhc": [

                ],
                "custom_modules_speeduhc": {

                }
            },
            "supersmash": {
                "enabled_modules_supersmash": [

                ],
                "custom_modules_supersmash": {

                }
            },
            "walls3": {
                "enabled_modules_walls3": [

                ],
                "custom_modules_walls3": {

                }
            },
            "battleground": {
                "enabled_modules_battleground": [

                ],
                "custom_modules_battleground": {

                }
            },
            "gingerbread": {
                "enabled_modules_gingerbread": [

                ],
                "custom_modules_gingerbread": {

                }
            },
            "truecombat": {
                "enabled_modules_truecombat": [

                ],
                "custom_modules_truecombat": {

                }
            },
            "skyclash": {
                "enabled_modules_skyclash": [

                ],
                "custom_modules_skyclash": {

                }
            },
            "walls": {
                "enabled_modules_walls": [

                ],
                "custom_modules_walls": {

                }
            },
            "paintball": {
                "enabled_modules_paintball": [

                ],
                "custom_modules_paintball": {

                }
            },
            "quake": {
                "enabled_modules_quake": [

                ],
                "custom_modules_quake": {

                }
            },
            "vampirez": {
                "enabled_modules_vampirez": [

                ],
                "custom_modules_vampirez": {

                }
            },
            "tntgames": {
                "enabled_modules_tntgames": [

                ],
                "custom_modules_tntgames": {

                }
            },
            "legacy": {
                "enabled_modules_legacy": [

                ],
                "custom_modules_legacy": {

                }
            },
            "murdermystery": {
                "enabled_modules_murdermystery": [

                ],
                "custom_modules_murdermystery": {

                }
            },
            "duels": {
                "enabled_modules_duels": [

                ],
                "custom_modules_duels": {

                }
            },
            "buildbattle": {
                "enabled_modules_buildbattle": [

                ],
                "custom_modules_buildbattle": {

                }
            },
            "skyblock": {
                "enabled_modules_skyblock": [

                ],
                "custom_modules_skyblock": {

                }
            },
            "pit": {
                "enabled_modules_pit": [

                ],
                "custom_modules_pit": {

                }
            },
            "housing": {
                "enabled_modules_housing": [

                ],
                "custom_modules_housing": {

                }
            }
        }

        self.config.register_user(**default_user)
        self.config.register_guild(**default_guild)

    def cog_unload(self):
        for task in self.user_autostats_list.values():
            task.cancel()
        for task in self.guild_autostats_list.values():
            task.cancel()

    async def cog_before_invoke(self, ctx):
        if self.enter in [ctx.command, ctx.command.root_parent]:
            return

        if self.module in [ctx.command, ctx.command.root_parent]:
            if not await ctx.cog.config.user(ctx.author).uuid():
                await ctx.send("You have to set a username first before being able to use this command")
                raise commands.CheckFailure()

        user_apikey = await self.config.user(ctx.author).api_key()
        if not user_apikey:
            guild_apikey = await self.config.guild(ctx.guild).api_key()

            if not guild_apikey:
                await ctx.send("There is no server nor personal apikey set.")
                raise commands.CheckFailure()
