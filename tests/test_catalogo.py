import json
import unittest
from pathlib import Path

from dash_bi.catalogo.gestor_ubicaciones import GestorUbicaciones


class TestCatalogo(unittest.TestCase):
    def test_cargar_catalogo_valido(self) -> None:
        ruta = Path("tests") / "_catalogo_prueba.json"
        try:
            ruta.write_text(
                json.dumps(
                    {
                        "san_jose_cr": {
                            "city": "San Jose",
                            "country": "Costa Rica",
                            "timezone": "America/Costa_Rica",
                            "latitude": 9.9281,
                            "longitude": -84.0907,
                        }
                    }
                ),
                encoding="utf-8",
            )

            catalogo = GestorUbicaciones().cargar_catalogo(str(ruta))
        finally:
            if ruta.exists():
                ruta.unlink()

        self.assertIn("san_jose_cr", catalogo)
        self.assertEqual(catalogo["san_jose_cr"]["country"], "Costa Rica")
