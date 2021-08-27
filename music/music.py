from redbot.core import commands, data_manager

from .tasks import Startup
from .utils import checks

import wavelink
import discord
import asyncio
import logging

log = logging.getLogger("red.bennos-cogs.music")

class TrackConverter:
    @staticmethod
    async def convert_yt_query(query: str, node: wavelink.Node):
        tracks = await node.get_tracks(cls=wavelink.YouTubeTrack,
                                       query=f"ytsearch:{query}")
        return tracks


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.host = "localhost"
        self.port = 2333
        self.pwd = "youshallnotpass"
        self.ll_running = False

        self.startup_task = Startup(self, self.bot, self.host, self.port, self.pwd)
        self.bot.loop.create_task(self.startup_task._start_ll_server())

    def cog_unload(self):
        log.debug("Internal LL server stopped")
        self.startup_task._proc.kill()

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        log.debug(f"Node: {node.identifier} is ready")

    def _has_player(self, guild):
        return True if self.main_node.get_player(guild) else False

    async def connect(self, channel: discord.VoiceChannel):
        if self._has_player(channel.guild):
            return

        player_class = wavelink.Player(client=self.bot, channel=channel, node=self.main_node)
        await channel.connect(cls=player_class)

    async def disconnect(self, guild: discord.Guild):
        if self._has_player(guild):
            player = self.main_node.get_player(guild)
            await player.disconnect(force=True)

    @checks.is_ll_started()
    @commands.command(name="connect")
    async def command_connect(self, ctx, channel: discord.VoiceChannel = None):
        if (not channel) and (not ctx.author.voice.channel):
            return

        channel = channel if channel else ctx.author.voice.channel
        await self.connect(channel)

    @checks.is_ll_started()
    @commands.command(name="disconnect")
    async def command_disconnect(self, ctx):
        await self.disconnect(ctx.guild)

    @checks.is_ll_started()
    @commands.command(name="play")
    async def command_play(self, ctx, query: str):
        tracks = await TrackConverter.convert_yt_query(query, self.main_node)
        if not self._has_player(ctx.guild):
            await self.connect(ctx.author.voice.channel)
        elif ctx.voice_client and (ctx.voice_client.channel != ctx.author.voice.channel):
            return

        player = self.main_node.get_player(ctx.guild)
        log.debug(f"Player started. Track: {tracks[0]}")
        await player.play(tracks[0])
