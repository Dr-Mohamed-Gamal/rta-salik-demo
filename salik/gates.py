"""The eight Salik gantries currently in operation across Dubai."""

from enum import Enum


class Gate(str, Enum):
    AL_BARSHA = "Al Barsha"
    AL_GARHOUD = "Al Garhoud Bridge"
    AIRPORT_TUNNEL = "Airport Tunnel"
    AL_MAKTOUM = "Al Maktoum Bridge"
    AL_MAMZAR_NORTH = "Al Mamzar North"
    AL_MAMZAR_SOUTH = "Al Mamzar South"
    JEBEL_ALI = "Jebel Ali"
    BUSINESS_BAY = "Business Bay Crossing"
