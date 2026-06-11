"""Parser surowej wiadomości MQTT silnika RTLS → Sample.

Trzymamy parsowanie osobno od modelu i magazynu: jeśli format wiadomości
się zmieni, ruszamy tylko ten plik.
"""
from __future__ import annotations
import json
from .model import Sample


def parse_message(payload: str | bytes | dict) -> Sample:
    """Zamienia jedną wiadomość `.../positions` na Sample.

    Akceptuje surowy JSON (str/bytes) albo już zdekodowany słownik.
    Rzuca ValueError, gdy brakuje wymaganych pól pozycji — wołający
    (kolektor) decyduje, czy taką wiadomość pominąć.
    """
    data = payload if isinstance(payload, dict) else json.loads(payload)

    try:
        pos = data["location"]["position"]
        return Sample(
            tag_id=str(data["tag"]["id"]),
            x=float(pos["x"]),
            y=float(pos["y"]),
            ts=float(data["timestamp"]) / 1000.0,   # ms -> s
            is_moving=bool(data.get("is_moving", False)),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Wiadomość bez poprawnej pozycji: {e}") from e

if __name__ == "__main__":
    # python -m tagstat.parse  ['{...raw JSON...}']
    import sys
    RAW = ('{"is_moving":false,"location":{"position":'
                                         '{"x":62.6,"y":53.75,"z":0.06}},'
           '"tag":{"id":"45306"},"timestamp":1781169530643}')
    raw = sys.argv[1] if len(sys.argv) > 1 else RAW
    print("Wejście:", raw)
    print("Sample :", parse_message(raw))
