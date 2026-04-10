from dataclasses import dataclass


@dataclass(frozen=True)
class UbicacionConsulta:
    clave: str
    ciudad: str
    pais: str
    zona_horaria: str
    latitud: float
    longitud: float
