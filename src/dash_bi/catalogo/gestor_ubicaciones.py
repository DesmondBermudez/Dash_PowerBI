import json
from pathlib import Path
from typing import Any

from ..modelos.ubicacion_consulta import UbicacionConsulta


class GestorUbicaciones:
    def cargar_catalogo(self, ruta_archivo: str) -> dict[str, dict[str, Any]]:
        ruta_catalogo = Path(ruta_archivo)
        if not ruta_catalogo.is_absolute():
            ruta_catalogo = Path(__file__).resolve().parents[3] / ruta_catalogo

        if not ruta_catalogo.exists():
            raise FileNotFoundError(f"No existe el archivo de ubicaciones: {ruta_catalogo}")

        with ruta_catalogo.open("r", encoding="utf-8") as archivo:
            catalogo_crudo = json.load(archivo)

        if not isinstance(catalogo_crudo, dict):
            raise ValueError("El archivo de ubicaciones debe contener un objeto JSON de primer nivel.")

        return self.validar_catalogo(catalogo_crudo)

    def validar_catalogo(self, catalogo: dict[str, Any]) -> dict[str, dict[str, Any]]:
        catalogo_validado: dict[str, dict[str, Any]] = {}
        campos_requeridos = {"city", "country", "timezone", "latitude", "longitude"}

        for clave, valor in catalogo.items():
            if not isinstance(valor, dict):
                raise ValueError(f"La ubicacion '{clave}' debe ser un objeto JSON.")

            campos_faltantes = campos_requeridos.difference(valor.keys())
            if campos_faltantes:
                faltantes = ", ".join(sorted(campos_faltantes))
                raise ValueError(f"La ubicacion '{clave}' no tiene los campos requeridos: {faltantes}")

            catalogo_validado[clave.lower()] = {
                "city": str(valor["city"]),
                "country": str(valor["country"]),
                "timezone": str(valor["timezone"]),
                "latitude": float(valor["latitude"]),
                "longitude": float(valor["longitude"]),
            }

        return catalogo_validado

    def expandir_ubicaciones(self, ubicaciones_crudas: list[str]) -> list[str]:
        ubicaciones: list[str] = []
        for valor_crudo in ubicaciones_crudas:
            for item in valor_crudo.split(","):
                item_limpio = item.strip()
                if item_limpio:
                    ubicaciones.append(item_limpio)
        return ubicaciones

    def expandir_coordenadas(self, coordenadas_crudas: list[str]) -> list[str]:
        coordenadas: list[str] = []
        for valor_crudo in coordenadas_crudas:
            for item in valor_crudo.split(";"):
                item_limpio = item.strip()
                if item_limpio:
                    coordenadas.append(item_limpio)
        return coordenadas

    def parsear_coordenada_simple(self, valor_crudo: str) -> tuple[float, float]:
        partes = [parte.strip() for parte in valor_crudo.split(",")]
        if len(partes) != 2:
            raise ValueError(
                f'Coordenadas invalidas "{valor_crudo}". Usa el formato latitud,longitud.'
            )
        return float(partes[0]), float(partes[1])

    def parsear_coordenada_detallada(self, valor_crudo: str, indice: int) -> UbicacionConsulta:
        partes = [parte.strip() for parte in valor_crudo.split(",") if parte.strip()]
        valores: dict[str, str] = {}
        for parte in partes:
            if "=" not in parte:
                raise ValueError(
                    f'Coordenadas invalidas "{valor_crudo}". Usa pares clave=valor o el formato latitud,longitud.'
                )
            clave, valor = parte.split("=", 1)
            valores[clave.strip().lower()] = valor.strip()

        if "lat" not in valores or "lon" not in valores:
            raise ValueError(
                f'Coordenadas invalidas "{valor_crudo}". Los campos lat y lon son obligatorios.'
            )

        return UbicacionConsulta(
            clave=f"custom_{indice}",
            ciudad=valores.get("city", f"Custom Location {indice}"),
            pais=valores.get("country", "Custom"),
            zona_horaria=valores.get("timezone", "auto"),
            latitud=float(valores["lat"]),
            longitud=float(valores["lon"]),
        )

    def crear_ubicacion_desde_catalogo(
        self,
        clave: str,
        datos: dict[str, Any],
    ) -> UbicacionConsulta:
        return UbicacionConsulta(
            clave=clave,
            ciudad=str(datos["city"]),
            pais=str(datos["country"]),
            zona_horaria=str(datos["timezone"]),
            latitud=float(datos["latitude"]),
            longitud=float(datos["longitude"]),
        )

    def crear_ubicacion_desde_coordenadas(self, valor_crudo: str, indice: int) -> UbicacionConsulta:
        if "=" in valor_crudo:
            return self.parsear_coordenada_detallada(valor_crudo, indice)

        latitud, longitud = self.parsear_coordenada_simple(valor_crudo)
        return UbicacionConsulta(
            clave=f"custom_{indice}",
            ciudad=f"Custom Location {indice}",
            pais="Custom",
            zona_horaria="auto",
            latitud=latitud,
            longitud=longitud,
        )

    def resolver_ubicaciones(
        self,
        argumentos: Any,
        catalogo: dict[str, dict[str, Any]],
    ) -> list[UbicacionConsulta]:
        if argumentos.url:
            return [
                UbicacionConsulta(
                    clave="custom_url",
                    ciudad="Custom URL Location",
                    pais="Unknown",
                    zona_horaria="GMT",
                    latitud=0.0,
                    longitud=0.0,
                )
            ]

        ubicaciones_resueltas: list[UbicacionConsulta] = []
        ubicaciones_solicitadas = self.expandir_ubicaciones(argumentos.location)
        coordenadas_solicitadas = self.expandir_coordenadas(argumentos.coordinates)

        if argumentos.all_locations or (not ubicaciones_solicitadas and not coordenadas_solicitadas):
            ubicaciones_solicitadas = sorted(catalogo.keys())

        for clave_ubicacion in ubicaciones_solicitadas:
            clave = clave_ubicacion.strip().lower()
            if clave not in catalogo:
                opciones = ", ".join(sorted(catalogo))
                raise ValueError(
                    f'La ubicacion "{clave_ubicacion}" no existe. Opciones disponibles: {opciones}'
                )
            ubicaciones_resueltas.append(self.crear_ubicacion_desde_catalogo(clave, catalogo[clave]))

        for indice, valor_crudo in enumerate(coordenadas_solicitadas, start=1):
            ubicaciones_resueltas.append(self.crear_ubicacion_desde_coordenadas(valor_crudo, indice))

        return ubicaciones_resueltas
