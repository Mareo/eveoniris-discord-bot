import discord

from .env import get_secret

MEMBER_ROLES = {
    1413092231920746506: {
        198449809751932929: ["TEST"],
    }
}

MANAGED_ROLES = {
    1413092231920746506: ["TEST"],
}


class Client(discord.Client):
    async def on_ready(self) -> None:
        print(f"Logged on as {self.user}!")
        for guild in self.guilds:
            managed_roles = await self.resolve_managed_roles(
                guild, MANAGED_ROLES[guild.id]
            )
            member_roles = await self.resolve_member_roles(
                guild, MEMBER_ROLES[guild.id]
            )
            await self.sync_member_roles(guild, managed_roles, member_roles)

    async def resolve_managed_roles(
        self,
        guild: discord.Guild,
        managed_roles: list[str],
    ) -> list[discord.Role]:
        return [r for r in guild.roles if r.name in managed_roles]

    async def resolve_member_roles(
        self,
        guild: discord.Guild,
        member_roles: dict[int, list[str]],
    ) -> dict[discord.Member, list[discord.Role]]:
        resolved_member_roles: dict[discord.Member, list[discord.Role]] = {}
        for member_id, role_names in member_roles.items():
            member = guild.get_member(member_id)
            if member is not None:
                roles = [r for r in guild.roles if r.name in role_names]
                resolved_member_roles[member] = roles
        return resolved_member_roles

    async def sync_member_roles(
        self,
        guild: discord.Guild,
        managed_roles: list[discord.Role],
        member_roles: dict[discord.Member, list[discord.Role]],
        member: discord.Member | None = None,
    ) -> None:
        async for member in guild.fetch_members():
            if member == guild.me:
                continue
            print(f"Syncing roles for {member.name}")
            desired_roles = member_roles.get(member, [])
            current_roles = [r for r in member.roles if r.name in managed_roles]
            to_add = set(desired_roles).difference(set(current_roles))
            to_remove = set(current_roles).difference(set(desired_roles))
            print(f"\t{to_add=}", f"{to_remove=}")
            await member.add_roles(*to_add)
            await member.remove_roles(*to_remove)

    async def on_message(self, message: discord.Message) -> None:
        print(f"Message from {message.author}: {message.content}")
        if message.author == self.user:
            return


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = Client(intents=intents)
    client.run(get_secret("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    main()
