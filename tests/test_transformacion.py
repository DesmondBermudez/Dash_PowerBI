import unittest

from dash_bi.transformacion.transformador_clima import TransformadorClima


class TestTransformacion(unittest.TestCase):
    def setUp(self) -> None:
        self.transformador = TransformadorClima()

    def test_preparar_filas_diarias(self) -> None:
        payload = {
            "daily": {
                "time": ["2026-04-10"],
                "uv_index_max": [10.0],
                "sunshine_duration": [36000],
                "precipitation_hours": [1.0],
                "uv_index_clear_sky_max": [11.0],
                "daylight_duration": [43200],
                "sunset": ["2026-04-10T17:45"],
                "sunrise": ["2026-04-10T05:32"],
                "precipitation_probability_max": [30.0],
                "precipitation_sum": [2.0],
                "snowfall_sum": [0.0],
                "showers_sum": [0.0],
                "rain_sum": [2.0],
            }
        }

        filas = self.transformador.preparar_filas_diarias(1, payload)

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0][0], 1)
