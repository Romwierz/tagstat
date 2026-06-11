"""Model danych pomiarowych RTLS."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    """Pojedynczy pomiar pozycji jednego taga w danej chwili.

    Pola pochodzą wprost z wiadomości MQTT silnika RTLS:
      tag_id     — `tag.id` z payloadu (identyfikator taga; w topicu jest engine!)
      x, y       — `location.position.x/y` (metry, lokalny układ mapy; pomijamy z)
      ts         — `timestamp` przeliczony z milisekund na sekundy (uniksowy, float)
      is_moving  — `is_moving` z payloadu; system sam klasyfikuje ruch
    """
    tag_id: str
    x: float
    y: float
    ts: float
    is_moving: bool = False


if __name__ == "__main__":
    # python -m tagstat.model
    a = Sample(tag_id="45306", x=62.6, y=53.75, ts=1781169530.643)
    b = Sample(tag_id="45306", x=62.7, y=53.70, ts=1781169531.0, is_moving=True)
    print("nieruchomy:", a, "| is_moving =", a.is_moving)
    print("w ruchu   :", b)
