from pathlib import Path
import sys


RUTA_SRC = Path(__file__).resolve().parent / "src"
if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from dash_bi.aplicacion.etl_clima_app import EtlClimaApp


if __name__ == "__main__":
    EtlClimaApp().ejecutar()
