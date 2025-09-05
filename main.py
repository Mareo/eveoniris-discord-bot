import discord

from bot import Client, get_secret


def main():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    client = Client(intents=intents)
    client.run(get_secret("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    main()
