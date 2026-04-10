import time

from ..api.cliente_clima import ClienteClima, COLUMNAS_DIARIAS, COLUMNAS_HORARIAS
from ..catalogo.gestor_ubicaciones import GestorUbicaciones
from ..config.gestor_argumentos import GestorArgumentos
from ..persistencia.cargador_sql_server import CargadorSqlServer
from ..transformacion.transformador_clima import TransformadorClima


class EtlClimaApp:
    def __init__(self) -> None:
        self.gestor_argumentos = GestorArgumentos()
        self.gestor_ubicaciones = GestorUbicaciones()
        self.cliente_clima = ClienteClima()
        self.transformador = TransformadorClima()

    def ejecutar(self) -> None:
        argumentos = self.gestor_argumentos.leer_argumentos()
        catalogo = self.gestor_ubicaciones.cargar_catalogo(argumentos.locations_file)

        if argumentos.list_locations:
            self.listar_ubicaciones(catalogo)
            return

        ubicaciones = self.gestor_ubicaciones.resolver_ubicaciones(argumentos, catalogo)
        cargador = CargadorSqlServer(argumentos, self.transformador)

        with cargador.abrir_conexion() as conexion:
            cursor = conexion.cursor()
            total_filas_diarias = 0
            total_filas_horarias = 0
            ubicaciones_procesadas: list[str] = []

            for indice, ubicacion in enumerate(ubicaciones, start=1):
                url = argumentos.url or self.cliente_clima.construir_url_api(
                    ubicacion,
                    argumentos.past_days,
                    argumentos.forecast_days,
                )
                payload = self.cliente_clima.obtener_payload(url)

                pais_id = cargador.obtener_o_crear_pais(cursor, ubicacion.pais)
                zona_horaria_id = cargador.obtener_o_crear_zona_horaria(
                    cursor,
                    str(payload.get("timezone", ubicacion.zona_horaria)),
                    str(payload.get("timezone_abbreviation", "")),
                )
                location_id = cargador.obtener_o_crear_ubicacion(
                    cursor,
                    payload,
                    ubicacion.ciudad,
                    pais_id,
                    zona_horaria_id,
                )

                cargador.actualizar_o_insertar_unidades(
                    cursor,
                    "DailyUnits",
                    payload.get("daily_units", {}),
                    COLUMNAS_DIARIAS,
                )
                cargador.actualizar_o_insertar_unidades(
                    cursor,
                    "HourlyUnits",
                    payload.get("hourly_units", {}),
                    COLUMNAS_HORARIAS,
                )

                filas_diarias = self.transformador.preparar_filas_diarias(location_id, payload)
                filas_horarias = self.transformador.preparar_filas_horarias(location_id, payload)

                cargador.reemplazar_filas_diarias(cursor, location_id, filas_diarias)
                cargador.reemplazar_filas_horarias(cursor, location_id, filas_horarias)

                total_filas_diarias += len(filas_diarias)
                total_filas_horarias += len(filas_horarias)
                ubicaciones_procesadas.append(
                    f"{ubicacion.ciudad}, {ubicacion.pais}"
                    f" [{payload.get('timezone', ubicacion.zona_horaria)}]"
                    f"(LocationID={location_id}, lat={payload['latitude']}, lon={payload['longitude']})"
                )

                if indice < len(ubicaciones) and argumentos.request_delay > 0:
                    time.sleep(argumentos.request_delay)

            conexion.commit()

        print(
            "Importacion completada. "
            f"Ubicaciones procesadas: {', '.join(ubicaciones_procesadas)}. "
            f"Filas diarias={total_filas_diarias}, filas horarias={total_filas_horarias}"
        )

    def listar_ubicaciones(self, catalogo: dict[str, dict]) -> None:
        print("Ubicaciones predefinidas disponibles:")
        for clave, datos in sorted(catalogo.items()):
            print(
                f"- {clave}: {datos['city']}, {datos['country']} "
                f"[{datos['timezone']}] ({datos['latitude']}, {datos['longitude']})"
            )
