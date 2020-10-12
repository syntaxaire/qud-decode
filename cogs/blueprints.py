"""Commands for querying the Caves of Qud object tree."""
import asyncio
import concurrent.futures
import logging
from functools import partial

from discord import Embed
from discord.ext.commands import Bot, BucketType, Cog, CommandOnCooldown, Context, command, cooldown
from fuzzywuzzy import process
from helpers.blueprint_search import find_closest_blueprint, find_exact_blueprint

from shared import qindex

log = logging.getLogger('bot.' + __name__)


class BlueprintQuery(Cog):
    """Query Caves of Qud game blueprints."""

    def __init__(self, bot: Bot):
        """Build a cache of object IDs and display names for faster searching."""
        self.bot = bot
        self.ids = [qid for qid in qindex]
        self.displaynames = [qobject.displayname for qobject in qindex.values()]

    @command()
    async def blueprint(self, ctx: Context, *args):
        """Search both blueprint names and display names with at least two characters."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        if query == '' or str.isspace(query) or len(query) < 2:
            return await ctx.send_help(ctx.command)
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            call = partial(process.extract, query, self.ids, limit=5)
            id_matches_raw = await loop.run_in_executor(pool, call)
        id_matches = [match[0] for match in id_matches_raw]
        id_indices = [self.ids.index(match) for match in id_matches]
        with concurrent.futures.ThreadPoolExecutor() as pool:
            call = partial(process.extract, query, self.displaynames, limit=5)
            displayname_matches_raw = await loop.run_in_executor(pool, call)
        displayname_matches = [match[0] for match in displayname_matches_raw]
        displayname_indices = [self.displaynames.index(match) for match in displayname_matches]
        embed = Embed(description="Matches:")
        # build embed field for ID matches
        field = []
        for index in id_indices:
            field.append(f"`{self.ids[index]}` ('{self.displaynames[index]}')")
        embed.add_field(name='Blueprint names (and display name):',
                        value='\n'.join(field),
                        inline=True)
        # build embed field for display name matches
        field = []
        for index in displayname_indices:
            field.append(f"'{self.displaynames[index]}' (`{self.ids[index]}`)")
        embed.add_field(name='Display names (and blueprint name):',
                        value='\n'.join(field),
                        inline=True)
        await ctx.send(embed=embed)

    @command()
    @cooldown(1, 10, BucketType.user)
    async def xml(self, ctx: Context, *args):
        """Send the source XML for a Qud blueprint to the channel."""
        log.info(f'({ctx.message.channel}) <{ctx.message.author}> {ctx.message.content}')
        query = ' '.join(args)
        obj = find_exact_blueprint(query)
        if obj is None:
            # no matching blueprint name
            # but, is there a blueprint with a matching displayname?
            for blueprint, qobject in qindex.items():
                if qobject.displayname.lower() == query.lower():
                    obj = qobject
        if obj is None:
            nearest = await find_closest_blueprint(query)
            msg = "Sorry, nothing matching that name was found. The closest blueprint name is" \
                  f" `{nearest[0]}`."
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(msg)
        # object was found
        msg = f'```xml\n{obj.source}\n```'
        await ctx.send(msg)

    @xml.error
    async def xml_error(self, ctx, error):
        """Handle errors for the xml command."""
        if isinstance(error, CommandOnCooldown):
            msg = f'Please wait another {error.retry_after:.0f} seconds before ' \
                  'using this command again.'
            await ctx.send(msg)
        else:
            raise error
