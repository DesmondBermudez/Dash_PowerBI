from datetime import datetime
from typing import Any, Iterable

from ..api.cliente_clima import COLUMNAS_DIARIAS, COLUMNAS_HORARIAS


class TransformadorClima:
    def a_datetime(self, valor: str | None) -> datetime | None:
        if not valor:
            return None
        return datetime.fromisoformat(valor)

    def a_date(self, valor: str | None):
        if not valor:
            return None
        return datetime.fromisoformat(valor).date()

    def dividir_en_lotes(self, items: list[Any], size: int) -> Iterable[list[Any]]:
        for indice in range(0, len(items), size):
            yield items[indice : indice + size]

    def preparar_filas_diarias(self, location_id: int, payload: dict[str, Any]) -> list[tuple[Any, ...]]:
        datos_diarios = payload["daily"]
        fechas = datos_diarios["time"]
        filas: list[tuple[Any, ...]] = []

        for indice, fecha_cruda in enumerate(fechas):
            fila = [location_id, self.a_date(fecha_cruda)]
            for columna in COLUMNAS_DIARIAS:
                valor = datos_diarios.get(columna, [None] * len(fechas))[indice]
                if columna in {"sunset", "sunrise"}:
                    fila.append(self.a_datetime(valor))
                else:
                    fila.append(valor)
            filas.append(tuple(fila))

        return filas

    def preparar_filas_horarias(self, location_id: int, payload: dict[str, Any]) -> list[tuple[Any, ...]]:
        datos_horarios = payload["hourly"]
        marcas_tiempo = datos_horarios["time"]
        filas: list[tuple[Any, ...]] = []

        for indice, tiempo_crudo in enumerate(marcas_tiempo):
            fila = [location_id, self.a_datetime(tiempo_crudo)]
            for columna in COLUMNAS_HORARIAS:
                fila.append(datos_horarios.get(columna, [None] * len(marcas_tiempo))[indice])
            filas.append(tuple(fila))

        return filas
