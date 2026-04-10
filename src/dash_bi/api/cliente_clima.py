import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from ..modelos.ubicacion_consulta import UbicacionConsulta


BASE_API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

COLUMNAS_DIARIAS = [
    "uv_index_max",
    "sunshine_duration",
    "precipitation_hours",
    "uv_index_clear_sky_max",
    "daylight_duration",
    "sunset",
    "sunrise",
    "precipitation_probability_max",
    "precipitation_sum",
    "snowfall_sum",
    "showers_sum",
    "rain_sum",
]

COLUMNAS_HORARIAS = [
    "temperature_2m",
    "pressure_msl",
    "relative_humidity_2m",
    "soil_temperature_0cm",
    "soil_temperature_6cm",
    "soil_temperature_18cm",
    "rain",
    "precipitation",
    "apparent_temperature",
    "precipitation_probability",
    "dew_point_2m",
    "visibility",
    "showers",
    "snowfall",
    "snow_depth",
    "wind_speed_10m",
    "wind_speed_80m",
    "wind_speed_120m",
    "wind_speed_180m",
    "wind_direction_10m",
    "wind_direction_80m",
    "wind_direction_120m",
    "wind_direction_180m",
    "wind_gusts_10m",
    "temperature_80m",
    "temperature_120m",
    "soil_temperature_54cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm",
    "soil_moisture_9_to_27cm",
    "soil_moisture_27_to_81cm",
    "temperature_180m",
]


class ClienteClima:
    def construir_url_api(
        self,
        ubicacion: UbicacionConsulta,
        dias_pasados: int,
        dias_futuros: int,
    ) -> str:
        query = {
            "latitude": ubicacion.latitud,
            "longitude": ubicacion.longitud,
            "timezone": ubicacion.zona_horaria,
            "daily": ",".join(COLUMNAS_DIARIAS),
            "hourly": ",".join(COLUMNAS_HORARIAS),
            "past_days": dias_pasados,
            "forecast_days": dias_futuros,
        }
        return f"{BASE_API_URL}?{urlencode(query)}"

    def obtener_payload(self, url: str) -> dict:
        try:
            with urlopen(url) as respuesta:
                return json.load(respuesta)
        except HTTPError as exc:
            raise RuntimeError(f"Error HTTP al consultar la API: {exc.code} {exc.reason}") from exc
        except URLError as exc:
            raise RuntimeError(f"No se pudo acceder a la API: {exc.reason}") from exc
