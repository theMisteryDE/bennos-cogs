import discord
from discord.ext import commands, tasks
import json
import datetime
import random

class Birthday(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.birthday_channel = None
        self.load_birthdays.start()

    def cog_unload(self):
        self.load_birthdays.cancel()

    # This function is called when the bot is ready and connected to Discord.
    # It assigns the "birthday_channel" variable to the Discord channel with the ID "BIRTHDAY_CHANNEL_ID".
    # It's a good idea to check if "birthday_channel" is not None before using it.
    @commands.Cog.listener()
    async def on_ready(self):
        self.birthday_channel = self.client.get_channel(BIRTHDAY_CHANNEL_ID)
        if self.birthday_channel is not None:
            print(f"Logged in as {self.client.user.name}. Birthday channel set to {self.birthday_channel.name}")
        else:
            print(f"Logged in as {self.client.user.name}. Unable to find birthday channel")

    # This function loads the birthdays from the JSON file and sets them as the "birthdays" attribute of the class.
    # It also schedules the "announce_birthdays" function to run every day at 12:00 AM.
    @tasks.loop(hours=24)
    async def load_birthdays(self):
        with open("birthdays.json", "r") as f:
            birthdays = json.load(f)

        self.birthdays = {}
        for name, date_str in birthdays.items():
            date = datetime.datetime.strptime(date_str, "%m/%d/%Y").date()
            self.birthdays[name] = date

        self.announce_birthdays.start()

    # This function checks if a given string is a valid date in the format "MM/DD/YYYY".
    def is_valid_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, "%m/%d/%Y")
            return True
        except ValueError:
            return False

    # This function adds a birthday to the "birthdays" attribute of the class and saves it to the JSON file.
    @commands.command(name="addbirthday", aliases=["addbday"])
    async def add_birthday(self, ctx, name: str, date_str: str):
        if not self.is_valid_date(date_str):
            await ctx.send(f"Invalid date format. Please use MM/DD/YYYY.")
            return

        date = datetime.datetime.strptime(date_str, "%m/%d/%Y").date()

        if date > datetime.date.today():
            await ctx.send(f"Invalid date. Birthdays cannot be in the future.")
            return

        self.birthdays[name] = date

        with open("birthdays.json", "w") as f:
            json.dump(self.birthdays, f, indent=4)

        await ctx.send(f"Added {name}'s birthday on {date_str}.")

    # This function removes a birthday from the "birthdays" attribute of the class and saves it to the JSON file.
    @commands.command(name="removebirthday", aliases=["removebday"])
    async def remove_birthday(self, ctx, name: str):
        if name not in self.birthdays:
            await ctx.send(f"{name}'s birthday is not in the list.")
            return

        del self.birthdays[name]

        with open("birthdays.json", "w") as f:
            json.dump(self.birthdays, f, indent=4)

        await ctx.send(f"Removed {name}'s birthday.")

# This function selects a random birthday from the "birthdays" attribute of the class.
    def select_random_birthday(self):
        today = datetime.date.today()
        today_month = today.month
        today_day = today.day

        candidates = []
        for name, date in self.birthdays.items():
            # Calculate the number of days until the next occurrence of the birthday.
            # If the birthday already occurred this year, calculate the number of days until the next year's occurrence.
            if date.month > today_month or (date.month == today_month and date.day >= today_day):
                days_until_birthday = (datetime.date(today.year, date.month, date.day) - today).days
            else:
                days_until_birthday = (datetime.date(today.year+1, date.month, date.day) - today).days

            # If the birthday occurs within the next 7 days, add it to the list of candidates.
            if days_until_birthday <= 7:
                candidates.append((name, date, days_until_birthday))

        # If there are no candidates, return None.
        if not candidates:
            return None

        # Sort the candidates by the number of days until the birthday.
        candidates.sort(key=lambda x: x[2])

        # Return a random candidate with probability proportional to the number of days until the birthday.
        total_days = sum(x[2] for x in candidates)
        rand = random.uniform(0, total_days)
        for name, date, days_until_birthday in candidates:
            if rand < days_until_birthday:
                return name, date

            rand -= days_until_birthday

        # This should never happen, but just in case.
        return None
