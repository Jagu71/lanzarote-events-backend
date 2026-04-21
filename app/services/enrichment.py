from dataclasses import dataclass


@dataclass(frozen=True)
class GeoHint:
    municipality: str
    locality: str
    latitude: float
    longitude: float


LANZAROTE_PLACES: dict[str, GeoHint] = {
    "jameos del agua": GeoHint("Haria", "Jameos del Agua", 29.1576, -13.4302),
    "cueva de los verdes": GeoHint("Haria", "Cueva de los Verdes", 29.1565, -13.4316),
    "castillo de san jose": GeoHint("Arrecife", "Castillo de San Jose", 28.9726, -13.5366),
    "casa museo del campesino": GeoHint("San Bartolome", "Mozaga", 29.0038, -13.6413),
    "jardin de cactus": GeoHint("Teguise", "Guatiza", 29.0604, -13.4681),
    "el almacen": GeoHint("Arrecife", "Arrecife", 28.9605, -13.5493),
    "islote de fermina": GeoHint("Arrecife", "Arrecife", 28.9565, -13.5451),
    "auditorio de los jameos del agua": GeoHint("Haria", "Jameos del Agua", 29.1576, -13.4302),
}


def enrich_location(
    *,
    venue_name: str | None,
    venue_address: str | None,
    locality: str | None,
    municipality: str | None,
) -> dict[str, str | float | None]:
    haystack = " ".join(filter(None, [venue_name, venue_address, locality, municipality])).lower()
    for key, value in LANZAROTE_PLACES.items():
        if key in haystack:
            return {
                "municipality": municipality or value.municipality,
                "locality": locality or value.locality,
                "latitude": value.latitude,
                "longitude": value.longitude,
            }
    return {
        "municipality": municipality,
        "locality": locality,
        "latitude": None,
        "longitude": None,
    }
