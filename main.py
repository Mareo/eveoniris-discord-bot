from bot import Client, env
from bot.larpmanager import init_engine


def main():
    client = Client(
        host=env.get_string("MYSQL_HOST"),
        user=env.get_string("MYSQL_USER"),
        password=env.get_secret("MYSQL_PASSWORD"),
        database=env.get_string("MYSQL_DATABASE"),
    )
    client.run(env.get_secret("DISCORD_BOT_TOKEN"))


if __name__ == "__main__":
    main()
