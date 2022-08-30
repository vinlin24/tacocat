"""logger.py

Sets up the logging for the program. Exposes the logger as a variable
for imports as a shortcut to the boilerplate:
```python
import logging
from .config import PROJECT_NAME
log = logging.getLogger(PROJECT_NAME)
```
Usage:
```python
from .logger import log
```
"""

import logging

from .config import (BOT_MODE, DISCORD_LOG_PATH, LOG_ALERT_LEVEL,
                     PROGRAM_LOG_DATEFMT, PROGRAM_LOG_FMT, PROGRAM_LOG_PATH,
                     PROJECT_NAME, BotMode)

__all__ = (
    "log",
    "discord_handler",
)

# ==================== PROGRAM LOGGER ==================== #

# Expose program logger for imports
log = logging.getLogger(PROJECT_NAME)
"""Program logger singleton."""

# Custom logging level for important but non-error messages
logging.addLevelName(LOG_ALERT_LEVEL, "ALERT")

# Set up the program logger
_file_handler = logging.FileHandler(
    filename=PROGRAM_LOG_PATH,
    mode="at" if BOT_MODE is BotMode.PRODUCTION else "wt",
    encoding="utf-8"
)
_stream_handler = logging.StreamHandler()
_formatter = logging.Formatter(
    fmt=PROGRAM_LOG_FMT,
    datefmt=PROGRAM_LOG_DATEFMT
)

_file_handler.setFormatter(_formatter)
_stream_handler.setFormatter(_formatter)
log.addHandler(_file_handler)
log.addHandler(_stream_handler)

# By default, log everything
# You can use a custom /logs or online tools to parse the log files
log.setLevel(logging.DEBUG)
log.debug("Program logging configured.")


# ==================== discord.py LOGGER ==================== #

# Separate discord.py library logging into its own log file
discord_handler = logging.FileHandler(
    filename=DISCORD_LOG_PATH,
    mode="at" if BOT_MODE is BotMode.PRODUCTION else "wt",
    encoding="utf-8"
)
"""Handler to override discord.py's library logging."""

discord_handler.setLevel(logging.DEBUG)
log.debug("Discord logging configured.")
