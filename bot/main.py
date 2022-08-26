"""main.py

Discord bot runtime entry point.
"""

from tacocat import BOT_TOKEN, bot


def main() -> None:
    """Main driver function."""
    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
