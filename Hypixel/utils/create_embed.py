import discord

async def current_modules_embed(current_modules):
    left, right = ("", "")
    length_of_current_modules = len(current_modules)
    half = int(length_of_current_modules / 2) + 1 if length_of_current_modules % 2 != 0 else int(length_of_current_modules / 2)
    embed = discord.Embed(color=discord.Color.blue(), description="Current modules")

    if length_of_current_modules > 5:
        for idx, item in enumerate(current_modules):
            if idx < half:
                left += f"\n{idx + 1}. {item[1]}"
            else:
                right += f"\n{idx + 1}. {item[1]}"
        embed.add_field(name="left", value=left, inline=True)
        embed.add_field(name="right", value=right, inline=True)
    else:
        for idx, item in enumerate(current_modules):
            left += f"\n{idx + 1}. {item[1]}"
        embed.add_field(name="left", value=left, inline=True)
    return embed

# async def comparison_embed(number: int, user1: str, user2: str, embeds: list):
#     embed = discord.Embed(color=discord.Color.blue(), description="Comparison")
#     embed.set_footer(text="Page " + str(number))
#     embed.add_field(name="User1", value=user1)
#     embed.add_field(name="User2", value=user2)
#     embed.add_field(name="Difference", value="User1 stats - User2 stats")
#     embeds.append(embed)

#     return embeds