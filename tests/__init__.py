from pathlib import Path
import sys


RUTA_SRC = Path(__file__).resolve().parent.parent / "src"
if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))
