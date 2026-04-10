import unittest

from dash_bi.catalogo.gestor_ubicaciones import GestorUbicaciones


class TestArgumentosCoordenadas(unittest.TestCase):
    def setUp(self) -> None:
        self.gestor = GestorUbicaciones()

    def test_parsear_coordenada_simple(self) -> None:
        ubicacion = self.gestor.crear_ubicacion_desde_coordenadas("9.9281,-84.0907", 1)

        self.assertEqual(ubicacion.ciudad, "Custom Location 1")
        self.assertEqual(ubicacion.pais, "Custom")
        self.assertEqual(ubicacion.zona_horaria, "auto")

    def test_parsear_coordenada_detallada(self) -> None:
        ubicacion = self.gestor.crear_ubicacion_desde_coordenadas(
            "lat=9.9281,lon=-84.0907,city=San Jose,country=Costa Rica,timezone=America/Costa_Rica",
            1,
        )

        self.assertEqual(ubicacion.ciudad, "San Jose")
        self.assertEqual(ubicacion.pais, "Costa Rica")
        self.assertEqual(ubicacion.zona_horaria, "America/Costa_Rica")
