from redbot.core.utils import AsyncIter

import re
import itertools
import asyncio
import logging
import wavelink
import discord
import copy

log = logging.getLogger("red.bennos-cogs.music.tasks")

class Startup:
    def __init__(self, cog, bot, host, port, pwd):
        self.cog = cog
        self.bot = bot
        self.host = host
        self.port = port
        self.pwd = pwd

    async def _start_ll_server(self):
        await self.bot.wait_until_red_ready()
        args = ["java", "-Djdk.tls.client.protocols=TLSv1.2", "-jar", "Lavalink old.jar"]
        self._proc = await asyncio.create_subprocess_exec(
            *args,
            cwd="D:/Programming/git/bennos-cogs/music/Lavalink",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        log.debug(f"Lavalink server started on port <{self.port}> with pwd <{self.pwd}> on pid <{self._proc.pid}>")

        try:
            await asyncio.wait_for(self._wait_for_ll_server(), timeout=120)
        except asyncio.TimeoutError:
            log.debug("Timeout while starting the lavalink server")
            self.cog.ll_running = False
            return

        self.bot.loop.create_task(self._init_main_node())

    async def _wait_for_ll_server(self):
        async for i in AsyncIter(itertools.cycle(range(50))):
            line = await self._proc.stdout.readline()

            if re.compile(rb"Started Launcher in \S+ seconds").search(line):
                log.debug("LL is ready to communicate")
                break

            if i == 49:
                await asyncio.sleep(0.1)

    async def _init_main_node(self):
        async for node in AsyncIter(copy.copy(wavelink.NodePool._nodes)):
            node = wavelink.NodePool.get_node(identifier=node)
            await node.disconnect()

        try:
            self.cog.main_node = wavelink.NodePool.get_node(identifier="test_node")
            log.debug("Connected to existing node")
        except (wavelink.errors.NoMatchingNode, wavelink.errors.ZeroConnectedNodes):
            self.cog.main_node = await wavelink.NodePool.create_node(bot=self.bot,
                                                                    host=self.host,
                                                                    port=self.port,
                                                                    password=self.pwd,
                                                                    identifier="test_node") #region=discord.VoiceRegion("europe")

            log.debug("Initialized new node")
        self.cog.ll_running = True
