import discord
from discord.ext.commands import Bot, command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .larpmanager import SecondaryGroup, User, init_engine

TEST_DISCORD_GUILD_ID = 1413092231920746506

TEST_USER_MAPPING = {
    7: 198449809751932929,  # mareo
    8: 166629986818588683,  # gectou4
}

MANAGED_ROLES = {
    TEST_DISCORD_GUILD_ID: ["TEST"],
}

ROLE_MAPPING = {
    (TEST_DISCORD_GUILD_ID, "Admin"): ["ROLE_ADMIN"],
    (TEST_DISCORD_GUILD_ID, "Orga"): ["ROLE_ORGA"],
    (TEST_DISCORD_GUILD_ID, "User"): ["ROLE_USER"],
}

SECONDARY_GROUP_MAPPING = {
    (TEST_DISCORD_GUILD_ID, "SG-1"): [1],
    (TEST_DISCORD_GUILD_ID, "SG-2"): [2],
    (TEST_DISCORD_GUILD_ID, "SG-3"): [3],
}

GROUP_MAPPING = {
    (TEST_DISCORD_GUILD_ID, "G-1"): [1],
    (TEST_DISCORD_GUILD_ID, "G-2"): [2],
    (TEST_DISCORD_GUILD_ID, "G-3"): [3],
}


class Client(Bot):
    def __init__(self, host: str, user: str, password: str, database: str, **kwargs):
        self.desired = {}
        self.mysql_host = host
        self.mysql_user = user
        self.mysql_password = password
        self.mysql_database = database
        intents = kwargs.pop("intents", discord.Intents.default())
        intents.message_content = True
        intents.members = True
        super().__init__("!", intents=intents, **kwargs)

    async def setup_hook(self):
        host, port, *_ = self.mysql_host.split(":", 1) + [""]
        self.engine = await init_engine(
            host=host,
            port=int(port) if port else None,
            user=self.mysql_user,
            password=self.mysql_password,
            database=self.mysql_database,
        )

        await self.refresh_desired()

    async def user_to_discord_user_id(self, user: User) -> int | None:
        return TEST_USER_MAPPING.get(user.id)

    async def refresh_desired(self):
        self.desired = {}
        cache = {}
        async with AsyncSession(self.engine) as session:
            cache["roles"] = {}
            for user in (await session.execute(select(User))).scalars():
                for role in user.roles:
                    discord_user_id = await self.user_to_discord_user_id(user)
                    if discord_user_id is None:
                        continue
                    cache["roles"].setdefault(role, []).append(discord_user_id)
            for (guild_id, role_name), user_roles in ROLE_MAPPING.items():
                for user_role in user_roles:
                    self.desired.setdefault(guild_id, {}).setdefault(
                        role_name, []
                    ).extend(cache["roles"].get(user_role, []))
            cache["secondary_groups"] = {}
            for secondary_group in (
                await session.execute(select(SecondaryGroup))
            ).scalars():
                for character in secondary_group.members:
                    if not character.vivant:
                        # We don't consider dead characters
                        continue
                    if character.user is None:
                        # We don't consider character not linked to a user
                        continue
                    elif character.user.personnage_id is None:
                        # TODO: If the user has no main character, we only
                        # process its last played character.
                        pass
                    elif character.user.personnage_id != character.id:
                        # We only consider characters which are the user main's
                        # character
                        continue
                    discord_user_id = await self.user_to_discord_user_id(character.user)
                    if discord_user_id is None:
                        continue
                    cache["secondary_groups"].setdefault(secondary_group.id, []).append(
                        discord_user_id
                    )
            for (
                guild_id,
                role_name,
            ), secondary_groups in SECONDARY_GROUP_MAPPING.items():
                for secondary_group_id in secondary_groups:
                    self.desired.setdefault(guild_id, {}).setdefault(
                        role_name, []
                    ).extend(cache["secondary_groups"].get(secondary_group_id, []))

    async def on_ready(self) -> None:
        print(f"Logged on as {self.user}!")
        await self.apply_desired()

    async def resolve_roles(
        self,
        guild: discord.Guild,
        names: list[str],
    ) -> dict[str, discord.Role]:
        roles = {}
        for role in guild.roles:
            if role.name in names:
                roles[role.name] = role
        return roles

    async def resolve_members(
        self,
        guild: discord.Guild,
        user_ids: list[int],
    ) -> list[discord.Member]:
        members = []
        for user_id in user_ids:
            member = guild.get_member(user_id) or guild.fetch_member(user_id)
            if member is not None:
                members.append(member)
        return members

    async def apply_desired(self):
        for guild in self.guilds:
            to_add: dict[discord.Member, list[discord.Role]] = {}
            to_remove: dict[discord.Member, list[discord.Role]] = {}
            desired = self.desired.get(guild.id, {})
            roles = await self.resolve_roles(
                guild, list(self.desired.get(guild.id, {}).keys())
            )
            for role, user_list in desired.items():
                role = roles[role]
                current_members = set(role.members)
                desired_members = set(await self.resolve_members(guild, user_list))
                for member in current_members - desired_members:
                    to_remove.setdefault(member, []).append(role)
                for member in desired_members - current_members:
                    to_add.setdefault(member, []).append(role)
            for member, roles in to_add.items():
                await member.add_roles(*roles)
            for member, roles in to_remove.items():
                await member.remove_roles(*roles)

    async def send_desired(self, guild: discord.Guild, channel):
        roles: dict[str, discord.Role] = await self.resolve_roles(
            guild, list(self.desired.get(guild.id, {}).keys())
        )
        content = []
        for role, user_list in self.desired.get(guild.id, {}).items():
            content.append(
                f"{roles[role].mention} -> "
                + ", ".join(
                    member.mention
                    for member in await self.resolve_members(guild, user_list)
                )
            )
        await channel.send("\n".join(content))

    async def on_message(self, message: discord.Message) -> None:
        print(f"Message from {message.author}: {message.content}")
        if message.author == self.user:
            return
        if message.content == "!desired" and message.guild is not None:
            await self.send_desired(message.guild, message.channel)
