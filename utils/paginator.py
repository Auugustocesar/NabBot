import asyncio

import discord
from discord import Message, Colour, Client, User, Reaction

from utils.discord import is_private
from utils.tibia import DRUID, SORCERER, PALADIN, KNIGHT


class CannotPaginate(Exception):
    pass


class Paginator:
    """Implements a paginator that queries the user for the
    pagination interface.

    Pages are 1-index based, not 0-index based.
    If the user does not reply within 2 minutes then the pagination
    interface exits automatically.

    Based on Rapptz' Paginator: https://github.com/Rapptz/RoboDanny/blob/master/cogs/utils/paginator.py
    Modified for Nab Bot's needs.

    Parameters
    ------------
    bot
        The bot instance.
    message
        The message that initiated this session.
    entries
        A list of entries to paginate.
    per_page
        How many entries show up per page.

    Attributes
    -----------
    embed: discord.Embed
        The embed object that is being used to send pagination info.
        Feel free to modify this externally. Only the description,
        footer fields, and colour are internally modified.
    permissions: discord.Permissions
        Our permissions for the channel.
    """
    Empty = discord.Embed.Empty

    def __init__(self, bot: Client, *, message: Message, entries, **kwargs):
        self.bot = bot
        self.entries = entries
        self.message = message
        self.author = message.author
        self.per_page = kwargs.get("per_page", 10)
        self.current_page = 1
        self.title = kwargs.get("title",None)
        self.numerate = kwargs.get("numerate", True)
        self.description = kwargs.get("description", "")
        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1
        self.maximum_pages = pages
        self.embed = discord.Embed()
        author = kwargs.get("author", None)
        if author is not None:
            self.embed.set_author(name=author, icon_url=kwargs.get("author_icon", discord.Embed.Empty),
                                  url=kwargs.get("author_url", discord.Embed.Empty))
        color = kwargs.get("color", None)
        if color is not None:
            self.embed.colour = color
        self.paginating = len(entries) > self.per_page
        self.reaction_emojis = [
            ('\N{BLACK LEFT-POINTING TRIANGLE}', self.previous_page),
            ('\N{BLACK RIGHT-POINTING TRIANGLE}', self.next_page),
            ('\U000023F9', self.stop_pages)
        ]
        guild = self.message.guild
        if guild is not None:
            self.permissions = self.message.channel.permissions_for(guild.me)
        else:
            self.permissions = discord.Permissions.all()

        if not self.permissions.embed_links:
            raise CannotPaginate('Bot does not have embed links permission.')

        if not self.permissions.add_reactions:
            raise CannotPaginate('Bot does not have add reactions permission.')

        if not self.permissions.read_message_history:
            raise CannotPaginate('Bot does not have read message history permission.')

    def get_page(self, page):
        base = (page - 1) * self.per_page
        return self.entries[base:base + self.per_page]

    async def show_page(self, page, *, first=False):
        self.current_page = page
        entries = self.get_page(page)
        p = []
        if self.numerate:
            for t in enumerate(entries, 1 + ((page - 1) * self.per_page)):
                p.append('%s. %s' % t)
        else:
            for t in entries:
                p.append(t)
        self.embed.set_footer(text='Page %s/%s (%s entries)' % (page, self.maximum_pages, len(self.entries)))
        if self.title:
            self.embed.title = self.title

        self.embed.description = self.description+"\n"+'\n'.join(p)
        if not self.paginating:
            return await self.message.channel.send(embed=self.embed)
            
        if not first:
            return await self.message.edit(embed=self.embed)

        # verify we can actually use the pagination session
        if not self.permissions.add_reactions:
            raise CannotPaginate('Bot does not have add reactions permission.')
        if not self.permissions.read_message_history:
            raise CannotPaginate("Bot does not have read message history permission.")

        self.message = await self.message.channel.send(embed=self.embed)
        for (reaction, _) in self.reaction_emojis:
            if self.maximum_pages == 2 and reaction in ('\u23ed', '\u23ee'):
                # no |<< or >>| buttons if we only have two pages
                # we can't forbid it if someone ends up using it but remove
                # it from the default set
                continue
            # Stop reaction doesn't work on PMs so do not add it
            if is_private(self.message.channel) and reaction == '\U000023F9':
                continue
            await self.message.add_reaction(reaction)

    async def checked_show_page(self, page):
        if page != 0 and page <= self.maximum_pages:
            await self.show_page(page)

    async def first_page(self):
        """goes to the first page"""
        await self.show_page(1)

    async def last_page(self):
        """goes to the last page"""
        await self.show_page(self.maximum_pages)

    async def next_page(self):
        """goes to the next page"""
        await self.checked_show_page(self.current_page + 1)

    async def previous_page(self):
        """goes to the previous page"""
        await self.checked_show_page(self.current_page - 1)

    async def show_current_page(self):
        if self.paginating:
            await self.show_page(self.current_page)

    async def stop_pages(self):
        """stops the interactive pagination session"""
        # await self.bot.delete_message(self.message)
        try:
            # Can't remove reactions in DMs, so don't even try
            if not is_private(self.message.channel):
                await self.message.clear_reactions()
        except:
            pass
        await self.show_page(1)
        self.paginating = False

    def react_check(self, reaction: Reaction, user: User):
        if reaction.message.id != self.message.id:
            return False

        if (not is_private(self.message.channel) and user.id != self.author.id) or user.id == self.bot.user.id:
            return False

        for (emoji, func) in self.reaction_emojis:
            if reaction.emoji == emoji:
                self.match = func
                return True
        return False

    async def paginate(self):
        """Actually paginate the entries and run the interactive loop if necessary."""
        await self.show_page(1, first=True)

        while self.paginating:
            try:
                react = await self.bot.wait_for("reaction_add", check=self.react_check, timeout=120.0)
                try:
                    # Can't remove other users reactions in DMs
                    if not is_private(self.message.channel):
                        await self.message.remove_reaction(react[0].emoji, react[1])
                except Exception as e:
                    pass
            except asyncio.TimeoutError:
                await self.first_page()
                self.paginating = False
                try:
                    # Can't remove other users reactions in DMs
                    if not is_private(self.message.channel):
                        await self.message.clear_reactions()
                except:
                    pass
                finally:
                    break

            await self.match()


class VocationPaginator(Paginator):
    def __init__(self, bot: Client, *, message: Message, entries, vocations, **kwargs):
        super().__init__(bot, message=message, entries=entries, **kwargs)
        present_vocations = []
        # Only add vocation filters for the vocations present
        if any(v.lower() in DRUID for v in vocations):
            present_vocations.append(('\U00002744', self.filter_druids))
        if any(v.lower() in SORCERER for v in vocations):
            present_vocations.append(('\U0001F525', self.filter_sorcerers))
        if any(v.lower() in PALADIN for v in vocations):
            present_vocations.append(('\U0001F3F9', self.filter_paladins))
        if any(v.lower() in KNIGHT for v in vocations):
            present_vocations.append(('\U0001F6E1', self.filter_knights))

        # Only add filters if there's more than one different vocation
        if len(present_vocations) > 1:
            self.reaction_emojis.extend(present_vocations)

        # Copies the entry list without reference
        self.original_entries = entries[:]
        self.vocations = vocations
        self.filters = [DRUID, SORCERER, PALADIN, KNIGHT]
        self.current_filter = -1

    async def filter_druids(self):
        await self.filter_vocation(0)

    async def filter_knights(self):
        await self.filter_vocation(3)

    async def filter_paladins(self):
        await self.filter_vocation(2)

    async def filter_sorcerers(self):
        await self.filter_vocation(1)

    async def filter_vocation(self, vocation):
        if vocation != self.current_filter:
            self.current_filter = vocation
            self.entries = [c for c, v in zip(self.original_entries, self.vocations) if v.lower() in self.filters[vocation]]
        else:
            self.current_filter = -1
            self.entries = self.original_entries[:]
        pages, left_over = divmod(len(self.entries), self.per_page)
        if left_over:
            pages += 1
        self.maximum_pages = pages
        await self.show_page(1)

