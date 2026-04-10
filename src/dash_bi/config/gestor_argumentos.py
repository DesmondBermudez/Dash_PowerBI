import argparse
import os


DEFAULT_PAST_DAYS = 92
DEFAULT_FORECAST_DAYS = 16
DEFAULT_REQUEST_DELAY_SECONDS = 1.5
DEFAULT_LOCATIONS_FILE = "locations.json"


class GestorArgumentos:
    def crear_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Descarga datos climaticos de Open-Meteo e inserta en WeatherBD."
        )
        parser.add_argument(
            "--url",
            help="URL completa del endpoint JSON. Si se indica, tiene prioridad sobre las coordenadas.",
        )
        parser.add_argument(
            "--location",
            action="append",
            default=[],
            help="Nombre de ubicacion predefinida. Puede repetirse o ir separada por comas.",
        )
        parser.add_argument(
            "--coordinates",
            action="append",
            default=[],
            help=(
                'Coordenadas en formato "lat,lon" o detallado '
                '"lat=...,lon=...,city=...,country=...,timezone=...". '
                'Puede repetirse o agruparse con ";"'
            ),
        )
        parser.add_argument(
            "--all-locations",
            action="store_true",
            help="Procesa todas las ubicaciones predefinidas.",
        )
        parser.add_argument(
            "--past-days",
            type=int,
            default=DEFAULT_PAST_DAYS,
            help="Cantidad de dias historicos a consultar.",
        )
        parser.add_argument(
            "--forecast-days",
            type=int,
            default=DEFAULT_FORECAST_DAYS,
            help="Cantidad de dias futuros a consultar.",
        )
        parser.add_argument(
            "--list-locations",
            action="store_true",
            help="Muestra las ubicaciones predefinidas disponibles y termina.",
        )
        parser.add_argument(
            "--locations-file",
            default=DEFAULT_LOCATIONS_FILE,
            help="Archivo JSON con el catalogo de ubicaciones.",
        )
        parser.add_argument(
            "--server",
            default=os.getenv("DB_SERVER", "localhost"),
            help="Servidor SQL Server local o remoto. Ej: localhost o .\\SQLEXPRESS",
        )
        parser.add_argument(
            "--database",
            default=os.getenv("DB_NAME", "WeatherBD"),
            help="Nombre de la base de datos.",
        )
        parser.add_argument(
            "--username",
            default=os.getenv("DB_USER"),
            help="Usuario SQL Server. Si se omite, usa autenticacion integrada.",
        )
        parser.add_argument(
            "--password",
            default=os.getenv("DB_PASSWORD"),
            help="Contrasena SQL Server.",
        )
        parser.add_argument(
            "--driver",
            default=os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
            help="Driver ODBC instalado.",
        )
        parser.add_argument(
            "--request-delay",
            type=float,
            default=DEFAULT_REQUEST_DELAY_SECONDS,
            help="Segundos de espera entre peticiones al API.",
        )
        return parser

    def leer_argumentos(self) -> argparse.Namespace:
        return self.crear_parser().parse_args()
