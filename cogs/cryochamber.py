"""Commands for preserving Discord messages in another channel."""
import re

from discord import Embed, Colour
from discord.ext.commands import (Cog, CommandError, MessageConverter,
                                  TextChannelConverter, group, check)


class Cryochamber(Cog):
    def __init__(self, _):
        self.ongoing_preservations = set()

    async def can_manage_messages(ctx):
        get_channel = TextChannelConverter().convert
        arg = ctx.message.content
        exp = r'(?P<source_specifier>.*?) in (?P<destination_channel_specifier>.*?)'
        command_match = re.fullmatch(exp, arg)
        dest_channel = await get_channel(ctx,
                                         command_match.group('destination_channel_specifier'))
        if not dest_channel.permissions_for(ctx.author).manage_messages:
            return False
        else:
            return True

    """Main preserve function. Things in [] are optional arguments, stuff in () are variables.
    The user must be able to manage messages in order to invoke these functions.

       ?preserve (message link) in (destination channel)
           Message link can be gotten by enabling developer commands on Discord and
           selecting "Copy Link".

       ?preserve [future|no more] pins from (original channel) in (destination channel)
           Embeds all messages pinned in the specified channel and reposts them in order or pinned,
           earliest first.

           future  | **NOT FULLY IMPLEMENTED** 
                     any future pins in that channel will be immeadiately reposted to the
                     destination. All current channels tagged with this can be checked
                     using ?preserve what
           no more | cancel a previous command that uses future.

       ?preserve what **NOT FULLY IMPLEMENTED** 
           Returns all original channel - destination channels tagged as future pins as a set."""
    @group(invoke_without_command=True)
    @check(can_manage_messages)
    async def preserve(self, context, *, arg):
        get_channel = TextChannelConverter().convert
        get_message = MessageConverter().convert
        exp = r'(?P<source_specifier>.*?) in (?P<destination_channel_specifier>.*?)'
        command_match = re.fullmatch(exp, arg)

        if command_match is None:
            raise CommandError('wrong syntax: ' + arg)

        dest_channel = await get_channel(context,
                                         command_match.group('destination_channel_specifier'))

        exp = r'(?:(?P<temporal_modifier>future|no more) )' \
              r'?pins from (?P<source_channel_specifier>.*?)'
        source_channel_match = re.fullmatch(exp,
                                            command_match.group('source_specifier'))

        if source_channel_match is None:
            source_message = await get_message(context, command_match.group('source_specifier'))
            await self._preserve_message(source_message, dest_channel)
        else:
            src_channel = await get_channel(context,
                                            source_channel_match.group('source_channel_specifier'))
            temporal_modifier = source_channel_match.group('temporal_modifier')

            if temporal_modifier is None:
                for pin in sorted(await src_channel.pins(), key=lambda message: message.created_at):
                    await self._preserve_message(pin, dest_channel)
            elif temporal_modifier == 'future':
                self.ongoing_preservations.add((src_channel.name, dest_channel.name))
            elif temporal_modifier == 'no more':
                self.ongoing_preservations.remove((src_channel.name, dest_channel.name))
            else:
                raise ValueError('unknown temporal modifier: ' + temporal_modifier)

    """Returns which channels the bot is currently watching for future pins,
    and where it's reposting to."""
    @preserve.command()
    async def what(self, context):
        await context.send(self.ongoing_preservations)

    """Formats the embedded message. It returns the original message with a link back to the
    original message as well as denoting how many attachments there are. It will only embed the
    first image included."""
    async def _preserve_message(self, message, channel):
        attach_str = ""
        if len(message.attachments) > 0:
            attach_str = "" + str(len(message.attachments)) + " attachment" +\
                         ("s" if len(message.attachments) > 1 else "") + ""

        embedded_msg = Embed(colour=Colour(0xf403f),
                             description=message.content,
                             timestamp=message.created_at)
        embedded_msg.set_author(name=message.author.name + '#' + message.author.discriminator +
                                ", aka " + message.author.display_name,
                                icon_url=str(message.author.avatar_url))
        embedded_msg.add_field(name="__              __",
                               value=attach_str + " [(original)](" + message.jump_url + ")")
        embedded_msg.set_footer(text="in #" + message.channel.name)
        for attach in message.attachments:
            if attach.width is not None and attach.height is not None:
                embedded_msg.set_image(url=attach.url)
        await channel.send(embed=embedded_msg)
