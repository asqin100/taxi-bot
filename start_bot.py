"""Simple bot starter script to avoid path encoding issues."""
import subprocess
import sys
from pathlib import Path

# Get the directory where this script is located
bot_dir = Path(__file__).parent

# Run as module to ensure proper imports
subprocess.run([sys.executable, "-m", "bot.main"], cwd=bot_dir)
