"""Rdzeń statystyk — czyste funkcje liczące jakość/stabilność danych taga.

„Czyste" = wchodzi lista próbek, wychodzi wynik; brak we/wy, brak stanu.
Dzięki temu łatwo to testować na ręcznych danych i wołać z CLI/API tak samo.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import fmean, stdev
import math
from .model import Sample

Point = tuple[float, float]   # (x, y) — system 2D


@dataclass
class TagStats:
    tag_id: str
    count: int                 # liczba próbek w oknie
    t_start: float | None      # ts najstarszej próbki w oknie
    t_end: float | None        # ts najnowszej próbki w oknie
    mean: Point                # centroid = średnia pozycja
    std: Point                 # odchylenie standardowe per oś (x, y)
    rms: float                 # promień rozrzutu: RMS odległości od centroidu
    ref: Point | None          # znana pozycja referencyjna (jeśli podana)
    error: float | None        # ‖mean − ref‖ — błąd kalibracji względem referencji
    moving_fraction: float     # udział próbek oznaczonych is_moving=True (0..1)


def _std(values: list[float]) -> float:
    # stdev wymaga ≥2 wartości; dla 1 próbki rozrzut = 0
    return stdev(values) if len(values) >= 2 else 0.0


def compute_stats(tag_id: str, samples: list[Sample],
                  ref: Point | None = None) -> TagStats:
    """Liczy statystyki dla jednego taga z podanej listy próbek (już z okna)."""
    if not samples:
        return TagStats(tag_id, 0, None, None, (0.0, 0.0), (0.0, 0.0),
                        0.0, ref, None, 0.0)

    xs = [s.x for s in samples]
    ys = [s.y for s in samples]

    mean = (fmean(xs), fmean(ys))
    std = (_std(xs), _std(ys))

    # rozrzut przestrzenny: RMS odległości euklidesowej każdej próbki od centroidu
    sq = [(s.x - mean[0]) ** 2 + (s.y - mean[1]) ** 2 for s in samples]
    rms = math.sqrt(fmean(sq))

    # błąd kalibracji: odległość średniej pozycji od znanej referencji
    error = math.dist(mean, ref) if ref is not None else None

    moving_fraction = sum(1 for s in samples if s.is_moving) / len(samples)

    ts = [s.ts for s in samples]
    return TagStats(tag_id, len(samples), min(ts), max(ts),
                    mean, std, rms, ref, error, moving_fraction)

if __name__ == "__main__":
    # python -m tagstat.stats
    # Compare stable vs noisy tag
    stable = [Sample("S", 10 + dx, 5 + dy, ts=1000 + i) for i, (dx, dy) in
              enumerate([(0.01, -0.01), (-0.02, 0.01), (0.0, 0.02), (-0.01, -0.01)])]
    noisy  = [Sample("N", 10 + dx, 5 + dy, ts=1000 + i) for i, (dx, dy) in
              enumerate([(0.5, -0.4), (-0.6, 0.3), (0.2, 0.7), (-0.3, -0.5)])]

    for name, data in [("stabilny ", stable), ("zaszumiony", noisy)]:
        s = compute_stats(data[0].tag_id, data, ref=(10.0, 5.0))
        print(f"{name}: std=({s.std[0]:.3f},{s.std[1]:.3f})  "
              f"rms={s.rms:.3f}  błąd_od_ref={s.error:.3f}")
