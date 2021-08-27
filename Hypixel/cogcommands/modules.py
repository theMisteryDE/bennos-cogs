import discord
from redbot.core import commands
import re
from io import BytesIO
import asyncio
from redbot.core.data_manager import bundled_data_path
from ..utils import create_embed, check_calc, api_requests, general, command_checks

class ModuleCommands():
    async def add_module(self, ctx, module, name, gamemode):
        duplicate = None
        current_modules = await self.config_get(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower())
        for key, value in current_modules:
            if module == key:
                duplicate = value
                break

        if module == None:
            valid_elements = await api_requests.append_custom_modules(await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower()), gamemode)
            as_bytes = map(str.encode, valid_elements)
            modules = b"\n".join(as_bytes)
            await ctx.send("Valid modules", file=discord.File(BytesIO(modules), "modules.txt"))

        elif (len(current_modules) == 10):
            await ctx.send("There are already 10 modules added. Remove some first")

        elif duplicate != None:
            await ctx.send(f"Module `{module}` already added as `{duplicate}`. Remove it first or choose another module.")

        else:
            valid_elements = await api_requests.append_custom_modules(await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower()), gamemode)
            as_bytes = map(str.encode, valid_elements)
            modules = b"\n".join(as_bytes)
            if module.lower() not in valid_elements:
                await ctx.send("Input is not a valid module. Try again with one element out of here", file=discord.File(BytesIO(modules), "modules.txt"))

            else:
                current_modules.append((module, name))
                await self.config_set(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower(), current_modules)
                await ctx.send(f"Module `{module}` added as `{name}`")

    async def remove_module(self, ctx, module, gamemode):
        current_modules = await self.config_get(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower())
        modules, names = [list(item) for item in zip(*current_modules)]

        if module == None:
            await ctx.send(embed=await create_embed.current_modules_embed(current_modules))

        elif (module.casefold() not in (m.casefold() for m in modules)) and (module.casefold() not in (n.casefold() for n in names)):
            await ctx.send(f"Module `{module}` is not added")
            await ctx.send(embed=await create_embed.current_modules_embed(current_modules))

        else:
            for idx, item in enumerate(current_modules):
                if (item[0].lower() == module.lower()) or (item[1].lower() == module.lower()):
                    current_modules.pop(idx)
                    break
            await self.config_set(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower(), current_modules)
            await ctx.send(f"Module `{module}` successfully removed!")

    async def sort_modules(self, ctx, gamemode):
        current_modules = await self.config_get(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower())
        
        await ctx.send(embed=await create_embed.current_modules_embed(current_modules))
        await ctx.send("To change the sorting, type the modules in the corresponding order. Example: \n```Kills \nFinal Kills \nKD \n...``` \nThis will put `Kills` to the top left. `Final kills` to the second spot and so on. \nSeparate each entry with a new line.")

        try:
            response = await self.bot.wait_for("message", check=general.message_check(channel=ctx.channel, author=ctx.author), timeout=120)
            resp_modules = response.content.lower()
            resp_modules = resp_modules.split("\n")
            if len(resp_modules) != len(current_modules):
                    await ctx.send("amount of enabled modules are not equal to amount of response modules")
            else:
                name_modules = []
                for x, y in current_modules:
                    name_modules.append(y.lower())
                temp_list = [(x,y) for item in resp_modules for x, y in current_modules if y.lower() == item]
                new_list = set(temp_list)
                missing_list = [x for x in name_modules if x not in resp_modules]
                duplicate_list = list(set([x for x in temp_list if temp_list.count(x) > 1]))
                invalid_list = [x for x in resp_modules if x not in name_modules]

                if len(new_list) != len(current_modules):
                    embed = discord.Embed(color=discord.Color.blue(), description="wrong inputs:")

                    if duplicate_list != []:
                        embed.add_field(name="duplicate", value="\n".join(duplicate_list), inline=True)

                    if missing_list != []:
                        embed.add_field(name="missing", value="\n".join(missing_list), inline=True)

                    if invalid_list != []:
                        embed.add_field(name="invalid", value="\n".join(invalid_list), inline=True)
                    
                    await ctx.send(embed=embed)

                else:
                    await self.config_set(ctx.guild, gamemode.lower(), "enabled_modules_" + gamemode.lower(), temp_list)
                    await ctx.send("Updated order.")

        except asyncio.TimeoutError:
            await ctx.send("Timeout")

    async def create_module(self, ctx, key, round_to, calc_input, gamemode):
        valid_elements = await api_requests.request_valid_elements(gamemode)
        valid_math_operators = ["(", ")", "/", "*", "+", "-"]
        calc_input = calc_input.replace(" ", "")
        search = re.compile(r"(/|\*|\(|\)|\+|\-)")
        calc_list = re.split(search, calc_input)

        calc_is_checked, calc_output, calc_test = await check_calc.check_and_test_calculation(ctx, calc_list, valid_math_operators, valid_elements, gamemode)

        if calc_is_checked == True:
            result = eval(f"round({calc_test}, {round_to})")
            msg = await ctx.send(f"Your calculation:\nRaw: `{calc_input}`\nOutput: `{calc_test} = {result}`\n\nWould you like to save it as `{key}`?\nY/N - timeout: 30 sec")
            try:
                response = await self.bot.wait_for("message", check=general.message_check(channel=ctx.channel, author=ctx.author), timeout=30)
                if response.content.lower() == "y":
                    current_modules = await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower())
                    current_modules[key] = calc_output
                    await self.config_set(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower(), current_modules)
                    await ctx.send(f"Module `{key}` saved.")
                else:
                    await ctx.send("Saving cancelled")
            except asyncio.TimeoutError:
                await msg.delete()

    async def delete_module(self, ctx, key, gamemode):
        valid_custom_modules = await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower())
        if key == None:
            valid_elements = await api_requests.append_custom_modules(await self.config_get(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower()), gamemode)
            as_bytes = map(str.encode, valid_elements)
            modules = b"\n".join(as_bytes)
            await ctx.send("Valid modules", file=discord.File(BytesIO(modules), "modules.txt"))
        elif key not in valid_custom_modules.keys():
            as_bytes = map(str.encode, valid_custom_modules)
            modules = b"\n".join(as_bytes)
            await ctx.send(f"Module `{key}` does not exist. You can see all existing custom modules here: ", file=discord.File(BytesIO(modules), "custom_modules.txt"))
        else:
            del valid_custom_modules[key]
            await self.config_set(ctx.guild, gamemode.lower(), "custom_modules_" + gamemode.lower(), valid_custom_modules)
            await ctx.send(f"Custom module `{key}` successfully deleted.")

    @commands.group(name="module", aliases=["mod"])
    async def module(self, ctx):
        """Add/remove/reorder/create modules"""
        pass

    @module.command(name="add", aliases=["a"])
    async def module_add(self, ctx, gamemode, module: str = None, *, name: str = None):
        """Add an available module
        module: must be a valid key for the dict returned by the api
        name: will be displayed on the wallpaper
        To create a custom module, use "[p]module create"
        to show gamemode list:
            [p]gamemodes
        """
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.add_module(ctx, module, name, gamemode)

    @module.group(name="remove", aliases=["rm"])
    async def module_remove(self, ctx, gamemode, *, module: str = None):
        """Remove an enabled module
        Remove by display name or api identifier
        """
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.remove_module(ctx, module, gamemode)

    @module.command(name="sort", aliases=["s"])
    async def module_sort(self, ctx, gamemode):
        """Sort currently enabled bedwars modules
        Enter enabled modules in desired order
        Split modules by new line
        """
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.sort_module(ctx, gamemode)

    @module.command(name="create", aliases=["c"])
    async def module_create(self, ctx, gamemode, key: str, round_to: int, *,calculation: str):
        """Adds a custom module with a given calculation
        key: the modules unique identifier
        round: amount of decimal digits to be displayed
        calculation: calculates with valid bedwars elements
            valid operators: `+, -, *, /, **, //, %`
            round brackets are supported as well"""
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.create_module(ctx, key, round_to, calculation, gamemode)

    @module.command(name="delete")
    async def module_delete(self, ctx, gamemode, key: str = None):
        """Deletes a custom module
        This will remove the the entry of the module
        key and calculation will be deleted"""
        key_json = await general.read_json(str(bundled_data_path(self)) + "/hypixel_dict_keys.json")
        if gamemode.lower() not in key_json.keys():
            await ctx.send("Gamemode not available")
            embed = discord.Embed(color=discord.Color.blue(), title="Hypixel Gamemodes")
            embed.add_field(name="available:", value="\n".join(key_json.keys()), inline=True)
            await ctx.send(embed=embed)
        else:
            gamemode = key_json.get(gamemode.lower()).get("stats_key")
            await self.delete_module(ctx, key, gamemode)