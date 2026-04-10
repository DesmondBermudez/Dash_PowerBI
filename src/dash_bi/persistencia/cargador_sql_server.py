from typing import Any

import pyodbc

from ..api.cliente_clima import COLUMNAS_DIARIAS, COLUMNAS_HORARIAS
from ..transformacion.transformador_clima import TransformadorClima


class CargadorSqlServer:
    def __init__(self, argumentos: Any, transformador: TransformadorClima) -> None:
        self.argumentos = argumentos
        self.transformador = transformador

    def construir_cadena_conexion(self) -> str:
        partes = [
            f"DRIVER={{{self.argumentos.driver}}}",
            f"SERVER={self.argumentos.server}",
            f"DATABASE={self.argumentos.database}",
            "TrustServerCertificate=yes",
        ]

        if self.argumentos.username and self.argumentos.password:
            partes.append(f"UID={self.argumentos.username}")
            partes.append(f"PWD={self.argumentos.password}")
        else:
            partes.append("Trusted_Connection=yes")

        return ";".join(partes)

    def abrir_conexion(self) -> pyodbc.Connection:
        return pyodbc.connect(self.construir_cadena_conexion())

    def obtener_o_crear_pais(self, cursor: pyodbc.Cursor, nombre_pais: str) -> int:
        cursor.execute(
            """
            SELECT CountryID
            FROM Country
            WHERE CountryName = ?
            """,
            nombre_pais,
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
            nombre_pais,
        )
        return cursor.fetchone()[0]

    def obtener_o_crear_zona_horaria(
        self,
        cursor: pyodbc.Cursor,
        nombre_zona_horaria: str,
        abreviacion_zona_horaria: str,
    ) -> int:
        cursor.execute(
            """
            SELECT TimezoneID
            FROM Timezone
            WHERE TimezoneName = ?
            """,
            nombre_zona_horaria,
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                UPDATE Timezone
                SET TimezoneAbbreviation = ?
                WHERE TimezoneID = ?
                """,
                abreviacion_zona_horaria,
                row[0],
            )
            return row[0]

        cursor.execute(
            """
            INSERT INTO Timezone (TimezoneName, TimezoneAbbreviation)
            OUTPUT INSERTED.TimezoneID
            VALUES (?, ?)
            """,
            nombre_zona_horaria,
            abreviacion_zona_horaria,
        )
        return cursor.fetchone()[0]

    def obtener_o_crear_ubicacion(
        self,
        cursor: pyodbc.Cursor,
        payload: dict[str, Any],
        ciudad: str,
        pais_id: int,
        zona_horaria_id: int,
    ) -> int:
        latitud = payload["latitude"]
        longitud = payload["longitude"]

        cursor.execute(
            """
            SELECT LocationID
            FROM Location
            WHERE Latitude = ? AND Longitude = ?
            """,
            latitud,
            longitud,
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
                ciudad,
                pais_id,
                zona_horaria_id,
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
            ciudad,
            pais_id,
            zona_horaria_id,
            latitud,
            longitud,
            payload.get("generationtime_ms"),
            payload.get("elevation"),
        )
        return cursor.fetchone()[0]

    def actualizar_o_insertar_unidades(
        self,
        cursor: pyodbc.Cursor,
        nombre_tabla: str,
        unidades: dict[str, str],
        columnas: list[str],
    ) -> None:
        existentes = {
            row.FieldName: row.UnitSymbol
            for row in cursor.execute(f"SELECT FieldName, UnitSymbol FROM {nombre_tabla}")
        }

        for campo in columnas:
            simbolo = unidades.get(campo)
            if not simbolo:
                continue
            if campo in existentes:
                if existentes[campo] != simbolo:
                    cursor.execute(
                        f"UPDATE {nombre_tabla} SET UnitSymbol = ? WHERE FieldName = ?",
                        simbolo,
                        campo,
                    )
            else:
                cursor.execute(
                    f"INSERT INTO {nombre_tabla} (FieldName, UnitSymbol) VALUES (?, ?)",
                    campo,
                    simbolo,
                )

    def reemplazar_filas_diarias(
        self,
        cursor: pyodbc.Cursor,
        location_id: int,
        filas: list[tuple[Any, ...]],
    ) -> None:
        if not filas:
            return

        fechas = sorted({fila[1] for fila in filas if fila[1] is not None})
        for lote in self.transformador.dividir_en_lotes(fechas, 200):
            placeholders = ",".join("?" for _ in lote)
            cursor.execute(
                f"DELETE FROM DailyWeather WHERE LocationID = ? AND Date IN ({placeholders})",
                location_id,
                *lote,
            )

        sql = f"""
            INSERT INTO DailyWeather (
                LocationID, Date, {", ".join(COLUMNAS_DIARIAS)}
            )
            VALUES ({", ".join("?" for _ in range(2 + len(COLUMNAS_DIARIAS)))})
        """
        cursor.fast_executemany = True
        cursor.executemany(sql, filas)

    def reemplazar_filas_horarias(
        self,
        cursor: pyodbc.Cursor,
        location_id: int,
        filas: list[tuple[Any, ...]],
    ) -> None:
        if not filas:
            return

        marcas_tiempo = sorted({fila[1] for fila in filas if fila[1] is not None})
        for lote in self.transformador.dividir_en_lotes(marcas_tiempo, 200):
            placeholders = ",".join("?" for _ in lote)
            cursor.execute(
                f"DELETE FROM HourlyWeather WHERE LocationID = ? AND Timestamp IN ({placeholders})",
                location_id,
                *lote,
            )

        sql = f"""
            INSERT INTO HourlyWeather (
                LocationID, Timestamp, {", ".join(COLUMNAS_HORARIAS)}
            )
            VALUES ({", ".join("?" for _ in range(2 + len(COLUMNAS_HORARIAS)))})
        """
        cursor.fast_executemany = True
        cursor.executemany(sql, filas)
