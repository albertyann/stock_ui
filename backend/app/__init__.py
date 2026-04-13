import sys
from pathlib import Path

parent_dir = Path(__file__).resolve().parent.parent.parent
trading_dir = parent_dir.parent

sys.path.insert(0, str(trading_dir))
