import unittest

from dash_bi.api.cliente_clima import ClienteClima
from dash_bi.modelos.ubicacion_consulta import UbicacionConsulta


class TestEtl(unittest.TestCase):
    def test_construir_url_con_zona_horaria(self) -> None:
        cliente = ClienteClima()
        ubicacion = UbicacionConsulta(
            clave="san_jose_cr",
            ciudad="San Jose",
            pais="Costa Rica",
            zona_horaria="America/Costa_Rica",
            latitud=9.9281,
            longitud=-84.0907,
        )

        url = cliente.construir_url_api(ubicacion, 30, 7)

        self.assertIn("timezone=America%2FCosta_Rica", url)
        self.assertIn("latitude=9.9281", url)
