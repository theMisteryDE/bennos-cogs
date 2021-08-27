from redbot.core import commands

class CompareCommands():
    @commands.group(name="compare")
    async def compare(self, ctx):
        pass

    @compare.command(name="bedwars")
    async def compare_bedwars(self, ctx, user1, user2):
        pass
        # resp1, status1 = await self.fetch_uuid(user1)
        # resp2, status2 = await self.fetch_uuid(user2)
        # if (status1 != 200) or (status2 != 200):
        #     await ctx.send("One or more usernames are not valid.")
        # else:
        #     uuid1 = resp1["id"]
        #     uuid2 = resp2["id"]

        #     topic = "player"
        #     identifier1 = "&uuid=" + uuid1
        #     identifier2 = "&uuid=" + uuid2
        #     resp_stats1, status1 = await self.fetch_stats(topic, identifier1)
        #     resp_stats2, status2 = await self.fetch_stats(topic, identifier2)

        #     if status1 != 200:
        #         await ctx.send("Something went wrong: \n`{}`".format(resp_stats1["cause"]))
        #     elif status2 != 200:
        #         await ctx.send("Something went wrong: \n`{}`".format(resp_stats2["cause"]))
        #     else:
        #         try:
        #             u1 = resp_stats1["player"]["stats"]["Bedwars"]
        #             u2 = resp_stats2["player"]["stats"]["Bedwars"]

        #             names = ["Games played", "Losses", "Wins", "W/L Rate", "Kills", "Deaths", "K/D", "Final kills", "Final deaths", "Final K/D"]

        #             u1_list = []
        #             u1_list.append(u1["games_played_bedwars"])
        #             u1_list.append(u1["losses_bedwars"])
        #             u1_list.append(u1["wins_bedwars"])
        #             u1_list.append(round(u1_list[2] / u1_list[1], 2))
        #             u1_list.append(u1["kills_bedwars"])
        #             u1_list.append(u1["deaths_bedwars"])
        #             u1_list.append(round(u1_list[4] / u1_list[5], 2))
        #             u1_list.append(u1["final_kills_bedwars"])
        #             u1_list.append(u1["final_deaths_bedwars"])
        #             u1_list.append(round(u1_list[7] / u1_list[8], 2))

        #             u2_list = []
        #             u2_list.append(u2["games_played_bedwars"])
        #             u2_list.append(u2["losses_bedwars"])
        #             u2_list.append(u2["wins_bedwars"])
        #             u2_list.append(round(u2_list[2] / u2_list[1], 2))
        #             u2_list.append(u2["kills_bedwars"])
        #             u2_list.append(u2["deaths_bedwars"])
        #             u2_list.append(round(u2_list[4] / u2_list[5], 2))
        #             u2_list.append(u2["final_kills_bedwars"])
        #             u2_list.append(u2["final_deaths_bedwars"])
        #             u2_list.append(round(u2_list[7] / u2_list[8], 2))

        #             d_list = []
        #             for i in range(0, len(u1_list)):
        #                 d_list.append(round((u1_list[i] - u2_list[i]), 2))

        #             embeds = []
        #             embeds = self.create_embed(1, user1, user2, embeds)
        #             n = 0

        #             for i in range(0, len(u1_list)):
        #                 if (i % 7 == False) and (i != 0):
        #                     n = int(i/7)
        #                     embeds = self.create_embed(n + 1, user1, user2, embeds)

        #                 embeds[n].add_field(name=names[i], value=u1_list[i])
        #                 embeds[n].add_field(name=names[i], value=u2_list[i])
        #                 embeds[n].add_field(name=names[i], value=d_list[i])

        #             message = await ctx.send(embed=embeds[0])
                    
        #             await message.add_reaction('◀')
        #             await message.add_reaction('▶')

        #             def check(reaction, user):
        #                 return user == ctx.author
            
        #             i = 0
        #             reaction = None

        #             while True:
        #                 if str(reaction) == '◀':
        #                     if i > 0:
        #                         i -= 1
        #                     else:
        #                         i = (len(embeds) -1)
        #                     await message.edit(embed = embeds[i])
        #                 elif str(reaction) == '▶':
        #                     if i < (len(embeds) -1):
        #                         i += 1
        #                     else:
        #                         i = 0
        #                     await message.edit(embed = embeds[i])
                        
        #                 try:
        #                     reaction, user = await self.bot.wait_for('reaction_add', timeout = 60.0, check = check)
        #                     await message.remove_reaction(reaction, user)
        #                 except:
        #                     break

        #             await message.clear_reactions()
        #         except:
        #             await ctx.send("`One Player has turned the API off`\n")