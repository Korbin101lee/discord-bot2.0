import discord
from discord.ext import commands
import asyncio
import random
import datetime
import os


def convert(time):
    pos = ["s", "m", "h", "d", "w"]
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 3600 * 24, "w": 3600 * 24 * 7}
    unit = time[-1]

    if unit not in pos:
        return -1
    try:
        val = int(time[:-1])
    except:
        return -2

    return val * time_dict[unit]

class Giveaway(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx):
        embedq1 = await ctx.send(f"What discord channel should we host the Giveaway. **Example**: ``#General``")
        embedq2 = await ctx.send(f"How long should it last? ``<s|m|h|d|w>`` **Example**: ``1d``")
        embedq3 = await ctx.send(f"What is the prize the winner will receive? **Example**: ``NITRO``")
        questions = [embedq1,
                     embedq2,
                     embedq3]

        answers = []

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for i in questions:


            try:
                msg = await self.bot.wait_for('message', timeout=60, check=check)
            except asyncio.TimeoutError:
                embed = discord.Embed(title=":gift: **Giveaway Setup Wizard**",
                                      description=":x: You didn't answer in time!")
                await ctx.send(embed=embed)
                return
            else:
                answers.append(msg.content)

        try:
            c_id = int(answers[0][2: -1])
        except:
            embed = discord.Embed(title=":gift: **Giveaway Setup Wizard**",
                                  description=":x: You didn't specify a channel correctly!")
            await ctx.send(embed=embed)
            return

        channel = self.bot.get_channel(c_id)

        time = convert(answers[1])
        if time == -1:
            embed = discord.Embed(title=":gift: **Giveaway Setup Wizard**",
                                  description=":x: You didn't set a proper time unit!")
            await ctx.send(embed=embed)
            return
        elif time == -2:
            embed = discord.Embed(title=":gift: **Giveaway Setup Wizard**",
                                  description=":x: Time unit **MUST** be an integer")
            await ctx.send(embed=embed)
            return
        prize = answers[2]

        embed = discord.Embed(title=":gift: **Giveaway Setup Wizard**",
                              description="Okay, all set. The Giveaway will now begin!")
        embed.add_field(name="Hosted Channel:", value=f"{channel.mention}")
        embed.add_field(name="Time:", value=f"{answers[1]}")
        embed.add_field(name="Prize:", value=prize)
        await ctx.send(embed=embed)
        print(
            f"New Giveaway Started! Hosted By: {ctx.author.mention} | Hosted Channel: {channel.mention} | Time: {answers[1]} | Prize: {prize}")
        print("------")
        embed = discord.Embed(title=f":gift: **GIVEAWAY FOR: {prize}**",
                              description=f"React With 🎉 To Participate!")
        embed.add_field(name="Lasts:", value=answers[1])
        embed.add_field(name=f"Hosted By:", value=ctx.author.mention)
        msg = await channel.send(embed=embed)

        await msg.add_reaction("🎉")
        await asyncio.sleep(time)

        new_msg = await channel.fetch_message(msg.id)
        users = [user async for user in new_msg.reactions[0].users()]
        users.pop(users.index(self.bot.user))

        winner = random.choice(users)
        await channel.send(f":tada: Congratulations {winner.mention}! You won the **{prize}**!")
        print(f"New Winner! User: {winner.mention} | Prize: {prize}")
        print("------")

        embed2 = discord.Embed(title=f":gift: **GIVEAWAY FOR: {prize}**",
                               description=f":trophy: **Winner:** {winner.mention}")
        embed2.set_footer(text="Giveaway Has Ended")
        await msg.edit(embed=embed2)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def reroll(self, ctx, channel: discord.TextChannel, id_: int):
        try:
            new_msg = await channel.fetch_message(id_)
            #users = await new_msg.reactions[0].users().flatten()
            users = [user async for user in new_msg.reactions[0].users()]        
            users.pop(users.index(self.bot.user))
            winner = random.choice(users)
            await ctx.channel.send(f":tada: The new winner is: {winner.mention}!")
        except:
            prefix = "!"
            await ctx.send(
                f":x: There was an error! \n`{prefix}reroll <Channel that hosted the giveaway> <messageID of the giveaway message>` ")

    @reroll.error
    async def reroll_error(self, ctx):
            await ctx.send(f":x: There was an error! \n`!reroll <Channel that hosted the giveaway> <messageID of the giveaway message>` ")

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
