import discord

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Union, Optional

from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.commands import Context


class MixinMeta(ABC):
    bot: Red
    config: Config
    ctx: Context

    message_list: List
    user_autostats_list: Dict
    guild_autostats_list: Dict

    @abstractmethod
    def str_to_list(self, string: str) -> List:
        raise NotImplementedError()

    @abstractmethod
    async def get_apikey(self, member: discord.Member) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    async def get_user_data(self, ctx: Context, username: str) -> Tuple[str, Tuple, Optional[str]]:
        raise NotImplementedError()

    @abstractmethod
    async def uuid_to_stats(self, ctx: Context, uuid: str, gamemode: str) -> Tuple[Optional[Dict], Optional[str]]:
        raise NotImplementedError()

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    pass