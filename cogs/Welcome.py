import os
import platform

import discord
from discord.ext import commands

class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")
        print(f"Discord.py API version: {discord.__version__}")
        print(f"Python version: {platform.python_version()}")
        print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
        print("-------------------")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.get_channel(883145817576333344).send(f"**IF YOU RECEIVED A DM FROM ALTIDENTIFIER, PLEASE ANSWER THAT FIRST** \n\nHey {member.mention}, welcome to Pro-Life! Before you get access to the rest of the channels, we would like you to answer a few questions. Please post them below and wait for an admin to approve you, which will happen within 12 hours, depending on your timezone. Please read the <#883145817576333345> as well. \n\n**DO NOT PING ADMINS OR OWNERS!**\n\nQuestions:\n1-Are you Pro-Life?\n2-If yes to #1, what exceptions may you consider (life of the mother, rape, etc.)?\n3-Where did you learn of this server?\n4-Do you agree to the rules?\n\nHave a good time!")


    @commands.command(name="verify")
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    async def verify(self, ctx, member: discord.Member):
        await member.remove_roles(member.guild.get_role(918220652639576154))
        await member.add_roles(member.guild.get_role(883145816158650453))
        await ctx.send(f"Welcome to the server, {member.display_name}! you can get roles in <#883145817576333346>")

async def setup(bot):
    await bot.add_cog(Welcome(bot))