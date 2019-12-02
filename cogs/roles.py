import logging

from discord.utils import get
from discord.ext.commands import Bot, Cog

from shared import config, rolesconfig

ROLE_EMOJI = rolesconfig['Roles']
ENTRY_EMOJI = rolesconfig['EntryRole']
ROLE_MESSAGE = int(rolesconfig['rolemessageid'])
ENTRY_MESSAGE = int(rolesconfig['entrymessageid'])
log = logging.getLogger('bot.' + __name__)


class Roles(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = config
        self.rolesconfig = rolesconfig

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        r_channel = self.bot.get_channel(payload.channel_id)
        r_guild = r_channel.guild
        r_user = self.bot.get_user(payload.user_id)
        r_member = r_guild.get_member(payload.user_id)

        if payload.user_id in self.config['ignore'] or r_user == self.bot.user:
            return

        if payload.message_id == ROLE_MESSAGE:
            if payload.emoji.name in ROLE_EMOJI:
                role = get(r_guild.roles, name=ROLE_EMOJI[payload.emoji.name])
            log.info(f'({r_channel}) <{r_user}> added role {role}')
            await r_member.add_roles(role)
        elif payload.message_id == ENTRY_MESSAGE:
            if payload.emoji.name in ENTRY_EMOJI:
                role = get(r_guild.roles, name=ENTRY_EMOJI[payload.emoji.name])
            log.info(f'({r_channel}) <{r_user}> added role {role}')
            await r_member.add_roles(role)
        else:
            return

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        r_channel = self.bot.get_channel(payload.channel_id)
        r_guild = r_channel.guild
        r_user = self.bot.get_user(payload.user_id)
        r_member = r_guild.get_member(payload.user_id)

        if payload.user_id in self.config['ignore'] or r_user == self.bot.user:
            return

        if payload.message_id == ROLE_MESSAGE:
            if payload.emoji.name in ROLE_EMOJI:
                role = get(r_guild.roles, name=ROLE_EMOJI[payload.emoji.name])
            log.info(f'({r_channel}) <{r_user}> removed role {role}')
            await r_member.remove_roles(role)
        elif payload.message_id == ENTRY_MESSAGE:
            if payload.emoji.name in ENTRY_EMOJI:
                role = get(r_guild.roles, name=ENTRY_EMOJI[payload.emoji.name])
            log.info(f'({r_channel}) <{r_user}> removed role {role}')
            await r_member.remove_roles(role)
        else:
            return
