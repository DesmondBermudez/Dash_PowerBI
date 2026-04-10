import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pyodbc


BASE_API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

DAILY_COLUMNS = [
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

HOURLY_COLUMNS = [
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

DEFAULT_PAST_DAYS = 92
DEFAULT_FORECAST_DAYS = 16
DEFAULT_REQUEST_DELAY_SECONDS = 1.5
DEFAULT_LOCATIONS_FILE = "locations.json"


def build_api_url(
    latitude: float,
    longitude: float,
    timezone_name: str,
    past_days: int,
    forecast_days: int,
) -> str:
    query = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone_name,
        "daily": ",".join(DAILY_COLUMNS),
        "hourly": ",".join(HOURLY_COLUMNS),
        "past_days": past_days,
        "forecast_days": forecast_days,
    }
    return f"{BASE_API_URL}?{urlencode(query)}"


def parse_args() -> argparse.Namespace:
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
        help='Coordenadas directas en formato "lat,lon". Puede repetirse o agruparse con ";"',
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
    return parser.parse_args()


def parse_coordinate_pair(raw_value: str) -> tuple[float, float]:
    parts = [part.strip() for part in raw_value.split(",")]
    if len(parts) != 2:
        raise ValueError(
            f'Coordenadas invalidas "{raw_value}". Usa el formato latitud,longitud.'
        )
    return float(parts[0]), float(parts[1])


def expand_location_arguments(raw_locations: list[str]) -> list[str]:
    expanded: list[str] = []
    for raw_value in raw_locations:
        for item in raw_value.split(","):
            clean_item = item.strip()
            if clean_item:
                expanded.append(clean_item)
    return expanded


def expand_coordinate_arguments(raw_coordinates: list[str]) -> list[str]:
    expanded: list[str] = []
    for raw_value in raw_coordinates:
        for item in raw_value.split(";"):
            clean_item = item.strip()
            if clean_item:
                expanded.append(clean_item)
    return expanded


def load_locations_catalog(file_path: str) -> dict[str, dict[str, Any]]:
    catalog_path = Path(file_path)
    if not catalog_path.is_absolute():
        catalog_path = Path(__file__).resolve().parent / catalog_path

    if not catalog_path.exists():
        raise FileNotFoundError(f"No existe el archivo de ubicaciones: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as file:
        raw_catalog = json.load(file)

    if not isinstance(raw_catalog, dict):
        raise ValueError("El archivo de ubicaciones debe contener un objeto JSON de primer nivel.")

    validated_catalog: dict[str, dict[str, Any]] = {}
    required_fields = {"city", "country", "timezone", "latitude", "longitude"}
    for key, value in raw_catalog.items():
        if not isinstance(value, dict):
            raise ValueError(f"La ubicacion '{key}' debe ser un objeto JSON.")
        missing_fields = required_fields.difference(value.keys())
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"La ubicacion '{key}' no tiene los campos requeridos: {missing}")
        validated_catalog[key.lower()] = {
            "city": str(value["city"]),
            "country": str(value["country"]),
            "timezone": str(value["timezone"]),
            "latitude": float(value["latitude"]),
            "longitude": float(value["longitude"]),
        }

    return validated_catalog


def resolve_requested_locations(
    args: argparse.Namespace,
    preset_locations: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if args.url:
        return [
            {
                "key": "custom_url",
                "city": "Custom URL Location",
                "country": "Unknown",
                "timezone": "GMT",
                "latitude": 0.0,
                "longitude": 0.0,
                "api_url": args.url,
            }
        ]

    resolved_locations: list[dict[str, Any]] = []
    location_names = expand_location_arguments(args.location)
    coordinate_values = expand_coordinate_arguments(args.coordinates)

    if args.all_locations or (not location_names and not coordinate_values):
        location_names = sorted(preset_locations.keys())

    for location_name in location_names:
        key = location_name.strip().lower()
        if key not in preset_locations:
            valid_names = ", ".join(sorted(preset_locations))
            raise ValueError(
                f'La ubicacion "{location_name}" no existe. Opciones disponibles: {valid_names}'
            )
        location_info = preset_locations[key]
        city_name = str(location_info["city"])
        country_name = str(location_info["country"])
        timezone_name = str(location_info["timezone"])
        latitude = float(location_info["latitude"])
        longitude = float(location_info["longitude"])
        resolved_locations.append(
            {
                "key": key,
                "city": city_name,
                "country": country_name,
                "timezone": timezone_name,
                "latitude": latitude,
                "longitude": longitude,
                "api_url": build_api_url(
                    latitude,
                    longitude,
                    timezone_name,
                    args.past_days,
                    args.forecast_days,
                ),
            }
        )

    for index, raw_coordinates in enumerate(coordinate_values, start=1):
        latitude, longitude = parse_coordinate_pair(raw_coordinates)
        resolved_locations.append(
            {
                "key": f"custom_{index}",
                "city": f"Custom Location {index}",
                "country": "Custom",
                "timezone": "auto",
                "latitude": latitude,
                "longitude": longitude,
                "api_url": build_api_url(
                    latitude,
                    longitude,
                    "auto",
                    args.past_days,
                    args.forecast_days,
                ),
            }
        )

    return resolved_locations


def fetch_payload(url: str) -> dict[str, Any]:
    try:
        with urlopen(url) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Error HTTP al consultar la API: {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"No se pudo acceder a la API: {exc.reason}") from exc


def build_connection_string(args: argparse.Namespace) -> str:
    parts = [
        f"DRIVER={{{args.driver}}}",
        f"SERVER={args.server}",
        f"DATABASE={args.database}",
        "TrustServerCertificate=yes",
    ]

    if args.username and args.password:
        parts.append(f"UID={args.username}")
        parts.append(f"PWD={args.password}")
    else:
        parts.append("Trusted_Connection=yes")

    return ";".join(parts)


def to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def to_date(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value).date()


def chunked(items: list[Any], size: int) -> Iterable[list[Any]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def get_or_create_country(cursor: pyodbc.Cursor, country_name: str) -> int:
    cursor.execute(
        """
        SELECT CountryID
        FROM Country
        WHERE CountryName = ?
        """,
        country_name,
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        """
        INSERT INTO Country (CountryName)
        OUTPUT INSERTED.CountryID
        VALUES (?)
        """,
        country_name,
    )
    return cursor.fetchone()[0]


def get_or_create_timezone(
    cursor: pyodbc.Cursor,
    timezone_name: str,
    timezone_abbreviation: str,
) -> int:
    cursor.execute(
        """
        SELECT TimezoneID
        FROM Timezone
        WHERE TimezoneName = ?
        """,
        timezone_name,
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            """
            UPDATE Timezone
            SET TimezoneAbbreviation = ?
            WHERE TimezoneID = ?
            """,
            timezone_abbreviation,
            row[0],
        )
        return row[0]

    cursor.execute(
        """
        INSERT INTO Timezone (TimezoneName, TimezoneAbbreviation)
        OUTPUT INSERTED.TimezoneID
        VALUES (?, ?)
        """,
        timezone_name,
        timezone_abbreviation,
    )
    return cursor.fetchone()[0]


def get_or_create_location(
    cursor: pyodbc.Cursor,
    payload: dict[str, Any],
    city_name: str,
    country_id: int,
    timezone_id: int,
) -> int:
    latitude = payload["latitude"]
    longitude = payload["longitude"]

    cursor.execute(
        """
        SELECT LocationID
        FROM Location
        WHERE Latitude = ? AND Longitude = ?
        """,
        latitude,
        longitude,
    )
    row = cursor.fetchone()
    if row:
        cursor.execute(
            """
            UPDATE Location
            SET CityName = ?,
                CountryID = ?,
                TimezoneID = ?,
                GenerationTimeMs = ?,
                Elevation = ?
            WHERE LocationID = ?
            """,
            city_name,
            country_id,
            timezone_id,
            payload.get("generationtime_ms"),
            payload.get("elevation"),
            row[0],
        )
        return row[0]

    cursor.execute(
        """
        INSERT INTO Location (
            CityName, CountryID, TimezoneID, Latitude, Longitude, GenerationTimeMs, Elevation
        )
        OUTPUT INSERTED.LocationID
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        city_name,
        country_id,
        timezone_id,
        latitude,
        longitude,
        payload.get("generationtime_ms"),
        payload.get("elevation"),
    )
    return cursor.fetchone()[0]


def upsert_units(cursor: pyodbc.Cursor, table_name: str, units: dict[str, str], columns: list[str]) -> None:
    existing = {
        row.FieldName: row.UnitSymbol
        for row in cursor.execute(f"SELECT FieldName, UnitSymbol FROM {table_name}")
    }

    for field in columns:
        symbol = units.get(field)
        if not symbol:
            continue
        if field in existing:
            if existing[field] != symbol:
                cursor.execute(
                    f"UPDATE {table_name} SET UnitSymbol = ? WHERE FieldName = ?",
                    symbol,
                    field,
                )
        else:
            cursor.execute(
                f"INSERT INTO {table_name} (FieldName, UnitSymbol) VALUES (?, ?)",
                field,
                symbol,
            )


def prepare_daily_rows(location_id: int, payload: dict[str, Any]) -> list[tuple[Any, ...]]:
    daily = payload["daily"]
    dates = daily["time"]
    rows: list[tuple[Any, ...]] = []

    for idx, raw_date in enumerate(dates):
        row = [location_id, to_date(raw_date)]
        for column in DAILY_COLUMNS:
            value = daily.get(column, [None] * len(dates))[idx]
            if column in {"sunset", "sunrise"}:
                row.append(to_datetime(value))
            else:
                row.append(value)
        rows.append(tuple(row))

    return rows


def prepare_hourly_rows(location_id: int, payload: dict[str, Any]) -> list[tuple[Any, ...]]:
    hourly = payload["hourly"]
    timestamps = hourly["time"]
    rows: list[tuple[Any, ...]] = []

    for idx, raw_timestamp in enumerate(timestamps):
        row = [location_id, to_datetime(raw_timestamp)]
        for column in HOURLY_COLUMNS:
            row.append(hourly.get(column, [None] * len(timestamps))[idx])
        rows.append(tuple(row))

    return rows


def replace_daily_rows(cursor: pyodbc.Cursor, location_id: int, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return

    dates = sorted({row[1] for row in rows if row[1] is not None})
    for batch in chunked(dates, 200):
        placeholders = ",".join("?" for _ in batch)
        cursor.execute(
            f"DELETE FROM DailyWeather WHERE LocationID = ? AND Date IN ({placeholders})",
            location_id,
            *batch,
        )

    sql = f"""
        INSERT INTO DailyWeather (
            LocationID, Date, {", ".join(DAILY_COLUMNS)}
        )
        VALUES ({", ".join("?" for _ in range(2 + len(DAILY_COLUMNS)))})
    """
    cursor.fast_executemany = True
    cursor.executemany(sql, rows)


def replace_hourly_rows(cursor: pyodbc.Cursor, location_id: int, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return

    timestamps = sorted({row[1] for row in rows if row[1] is not None})
    for batch in chunked(timestamps, 200):
        placeholders = ",".join("?" for _ in batch)
        cursor.execute(
            f"DELETE FROM HourlyWeather WHERE LocationID = ? AND Timestamp IN ({placeholders})",
            location_id,
            *batch,
        )

    sql = f"""
        INSERT INTO HourlyWeather (
            LocationID, Timestamp, {", ".join(HOURLY_COLUMNS)}
        )
        VALUES ({", ".join("?" for _ in range(2 + len(HOURLY_COLUMNS)))})
    """
    cursor.fast_executemany = True
    cursor.executemany(sql, rows)


def main() -> None:
    args = parse_args()
    preset_locations = load_locations_catalog(args.locations_file)

    if args.list_locations:
        print("Ubicaciones predefinidas disponibles:")
        for key, location_info in sorted(preset_locations.items()):
            print(
                f"- {key}: {location_info['city']}, {location_info['country']} "
                f"[{location_info['timezone']}] "
                f"({location_info['latitude']}, {location_info['longitude']})"
            )
        return

    requested_locations = resolve_requested_locations(args, preset_locations)
    connection_string = build_connection_string(args)

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()
        total_daily_rows = 0
        total_hourly_rows = 0
        processed_locations: list[str] = []

        for index, location_info in enumerate(requested_locations, start=1):
            payload = fetch_payload(location_info["api_url"])
            country_id = get_or_create_country(cursor, location_info["country"])
            timezone_id = get_or_create_timezone(
                cursor,
                str(payload.get("timezone", location_info["timezone"])),
                str(payload.get("timezone_abbreviation", "")),
            )
            location_id = get_or_create_location(
                cursor,
                payload,
                location_info["city"],
                country_id,
                timezone_id,
            )
            upsert_units(cursor, "DailyUnits", payload.get("daily_units", {}), DAILY_COLUMNS)
            upsert_units(cursor, "HourlyUnits", payload.get("hourly_units", {}), HOURLY_COLUMNS)

            daily_rows = prepare_daily_rows(location_id, payload)
            hourly_rows = prepare_hourly_rows(location_id, payload)

            replace_daily_rows(cursor, location_id, daily_rows)
            replace_hourly_rows(cursor, location_id, hourly_rows)

            total_daily_rows += len(daily_rows)
            total_hourly_rows += len(hourly_rows)
            processed_locations.append(
                f"{location_info['city']}, {location_info['country']}"
                f" [{payload.get('timezone', location_info['timezone'])}]"
                f"(LocationID={location_id}, lat={payload['latitude']}, lon={payload['longitude']})"
            )

            if index < len(requested_locations) and args.request_delay > 0:
                time.sleep(args.request_delay)

        connection.commit()

    print(
        "Importacion completada. "
        f"Ubicaciones procesadas: {', '.join(processed_locations)}. "
        f"Filas diarias={total_daily_rows}, filas horarias={total_hourly_rows}"
    )


if __name__ == "__main__":
    main()
