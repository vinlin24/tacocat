"""main.py

Discord bot runtime entry point.
"""

from tacocat import bot, bot_run_kwargs


def main() -> None:
    """Main driver function."""
    bot.run(**bot_run_kwargs)  # Here we go!


if __name__ == "__main__":
    main()
