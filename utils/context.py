import asyncio
import re
from typing import Union, Optional

import discord
from discord.ext import commands

from utils.config import config
from utils.database import get_server_property

YES_NO_REACTIONS = ("🇾", "🇳")
CHECK_REACTIONS = ("✅", "❌")
_mention = re.compile(r'<@!?([0-9]{1,19})>')


class NabCtx(commands.Context):
    guild: discord.Guild
    message: discord.Message
    channel: discord.TextChannel
    author: Union[discord.User, discord.Member]
    me: Union[discord.Member, discord.ClientUser]
    command: commands.Command

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Properties
    @property
    def author_permissions(self) -> discord.Permissions:
        """Shortcut to check the command author's permission to the current channel.

        :return: The permissions for the author in the current channel.
        :rtype: discord.Permissions
        """
        return self.channel.permissions_for(self.author)

    @property
    def ask_channel_name(self) -> Optional[str]:
        """Gets the name of the ask channel for the current server.

        :return: The name of the ask channel if applicable
        :rtype: str or None"""
        if self.guild is None:
            return None
        ask_channel_id = get_server_property(self.guild.id, "ask_channel", is_int=True)
        ask_channel = self.guild.get_channel(ask_channel_id)
        if ask_channel is None:
            return config.ask_channel_name
        return ask_channel.name

    @property
    def bot_permissions(self) -> discord.Permissions:
        """Shortcut to check the bot's permission to the current channel.

        :return: The permissions for the author in the current channel.
        :rtype: discord.Permissions"""
        return self.channel.permissions_for(self.me)

    @property
    def clean_prefix(self) -> str:
        """Gets the clean prefix used in the command invocation.

        This is used to clean mentions into plain text."""
        m = _mention.match(self.prefix)
        if m:
            user = self.bot.get_user(int(m.group(1)))
            if user:
                return f'@{user.name} '
        return self.prefix

    @property
    def is_askchannel(self):
        """Checks if the current channel is the command channel"""
        ask_channel_id = get_server_property(self.guild.id, "ask_channel", is_int=True)
        ask_channel = self.guild.get_channel(ask_channel_id)
        if ask_channel is None:
            return self.channel.name == config.ask_channel_name
        return ask_channel == self.channel

    @property
    def long(self) -> bool:
        """Whether the current context allows long replies or not

        Private messages and command channels allow long replies.
        """
        if self.guild is None:
            return True
        return self.is_askchannel

    @property
    def usage(self) -> str:
        """Shows the parameters signature of the invoked command"""
        if self.command.usage:
            return self.command.usage
        else:
            params = self.command.clean_params
            if not params:
                return ''
            result = []
            for name, param in params.items():
                if param.default is not param.empty:
                    # We don't want None or '' to trigger the [name=value] case and instead it should
                    # do [name] since [name=None] or [name=] are not exactly useful for the user.
                    should_print = param.default if isinstance(param.default, str) else param.default is not None
                    if should_print:
                        result.append(f'[{name}={param.default!r}]')
                    else:
                        result.append(f'[{name}]')
                elif param.kind == param.VAR_POSITIONAL:
                    result.append(f'[{name}...]')
                else:
                    result.append(f'<{name}>')

            return ' '.join(result)

    @property
    def world(self) -> Optional[str]:
        """Check the world that is currently being tracked by the guild

        :return: The world that the server is tracking.
        :rtype: str | None
        """
        if self.guild is None:
            return None
        else:
            return self.bot.tracked_worlds.get(self.guild.id, None)

    async def input(self, *, timeout=60.0, clean=False, delete_response=False) \
            -> Optional[str]:
        """Waits for text input from the author.

        :param timeout: Maximum time to wait for a message.
        :param clean: Whether the content should be cleaned or not.
        :param delete_response: Whether to delete the author's message after.
        :return: The content of the message replied by the author
        """
        def check(_message):
            return _message.channel == self.channel and _message.author == self.author

        try:
            value = await self.bot.wait_for("message", timeout=timeout, check=check)
            if clean:
                ret = value.clean_content
            else:
                ret = value.content
            if delete_response:
                try:
                    await value.delete()
                except discord.HTTPException:
                    pass
            return ret
        except asyncio.TimeoutError:
            return None

    async def react_confirm(self, message: discord.Message, *, timeout=60.0, delete_after=False,
                            use_checkmark=False):
        """Waits for the command author to reply with a Y or N reaction.

        Returns True if the user reacted with Y
        Returns False if the user reacted with N
        Returns None if the user didn't react at all

        :param message: The message that will contain the reactions.
        :param timeout: The maximum time to wait for reactions
        :param delete_after: Whether to delete or not the message after finishing.
        :param use_checkmark: Whether to use or not checkmarks instead of Y/N
        :return: True if reacted with Y, False if reacted with N, None if timeout.
        """
        if not self.channel.permissions_for(self.me).add_reactions:
            raise RuntimeError('Bot does not have Add Reactions permission.')

        reactions = CHECK_REACTIONS if use_checkmark else YES_NO_REACTIONS
        for emoji in reactions:
            await message.add_reaction(emoji)

        def check_react(reaction: discord.Reaction, user: discord.User):
            if reaction.message.id != message.id:
                return False
            if user.id != self.author.id:
                return False
            if reaction.emoji not in reactions:
                return False
            return True
        try:
            react = await self.bot.wait_for("reaction_add", timeout=timeout, check=check_react)
            if react[0].emoji == reactions[1]:
                return False
        except asyncio.TimeoutError:
            return None
        finally:
            if delete_after:
                await message.delete()
            elif self.guild is not None:
                try:
                    await message.clear_reactions()
                except discord.Forbidden:
                    pass
        return True

    @staticmethod
    def tick(value: bool = True, label: str = None) -> str:
        """Displays a checkmark or a cross depending on the value.

        :param value: The value to evaluate
        :param label: An optional label to display
        :return: A checkmark or cross
        """
        emoji = CHECK_REACTIONS[int(not value)]
        if label:
            return emoji + label
        return emoji