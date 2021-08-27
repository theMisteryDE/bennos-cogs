import re
import discord

async def check_and_test_calculation(ctx, calc_to_check, valid_math_operators, valid_elements, gamemode):
    invalid_elements = []

    calc_output = ""
    calc_test = ""

    for item in calc_to_check:
        if item != "":
            match = re.match("([a-z]|[A-Z])", item)
            if isinstance(match, re.Match):
                if item in valid_elements:
                    value = valid_elements[item]
                    item = gamemode.lower() + f"['{item}']"
                    calc_test += str(value)
                else:
                    invalid_elements.append(item)
            else:
                calc_test += item
            calc_output += str(item)

    invalid_operators = [i for i in calc_test if (not i.isdigit()) and (i not in valid_math_operators)]

    if (invalid_elements == []) and (invalid_operators == []):
        return True, calc_output, calc_test
    else:
        embed = discord.Embed(color=discord.Color.red(), description="**this/these are invalid:**") 

        if invalid_operators != []:
            embed.add_field(name="math operators", value="\n".join(invalid_operators), inline=True)

        if invalid_elements != []:
            embed.add_field(name="elements", value="\n".join(invalid_elements), inline=True)
        
        await ctx.send(embed=embed)

        return False, None, None