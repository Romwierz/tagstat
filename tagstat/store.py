"""Magazyn próbek — interfejs + implementacja w pamięci.

Rdzeń (stats, cli, api) zależy tylko od interfejsu `Store`, więc późniejsza
wymiana na SQLite to podmiana jednej klasy, bez ruszania reszty kodu.
"""
from __future__ import annotations
from typing import Protocol
import bisect
from .model import Sample


class Store(Protocol):
    """Kontrakt magazynu — minimalny zestaw operacji potrzebny reszcie."""

    def add(self, sample: Sample) -> None: ...

    def query(self, tag_id: str | None = None,
              since: float | None = None,
              until: float | None = None) -> list[Sample]: ...

    def tag_ids(self) -> list[str]: ...


class MemoryStore:
    """Trzyma próbki w pamięci, per tag, posortowane rosnąco po `ts`.

    Sortowanie pozwala szybko wyciąć okno czasowe (bisect) zamiast
    przeglądać całość liniowo.
    """

    def __init__(self) -> None:
        self._by_tag: dict[str, list[Sample]] = {}

    def add(self, sample: Sample) -> None:
        seq = self._by_tag.setdefault(sample.tag_id, [])
        # dane mogą przyjść lekko nieuporządkowane — wstawiamy w odpowiednie miejsce
        i = bisect.bisect_right([s.ts for s in seq], sample.ts)
        seq.insert(i, sample)

    def query(self, tag_id: str | None = None,
              since: float | None = None,
              until: float | None = None) -> list[Sample]:
        tags = [tag_id] if tag_id is not None else list(self._by_tag)
        out: list[Sample] = []
        for t in tags:
            seq = self._by_tag.get(t, [])
            ts = [s.ts for s in seq]
            # granice okna wyznaczamy bisectem na posortowanych ts
            lo = bisect.bisect_left(ts, since) if since is not None else 0
            hi = bisect.bisect_right(ts, until) if until is not None else len(seq)
            out.extend(seq[lo:hi])
        return out

    def tag_ids(self) -> list[str]:
        return list(self._by_tag)

if __name__ == "__main__":
    # python -m tagstat.store
    # Add sample show sample from time window
    st = MemoryStore()
    for i in range(5):
        st.add(Sample("A", x=float(i), y=0.0, ts=1000 + i))   # ts: 1000..1004
    st.add(Sample("B", x=9.0, y=9.0, ts=1002))

    print("tagi              :", st.tag_ids())
    print("A całość (x)      :", [s.x for s in st.query("A")])
    print("A okno 1001..1003 :", [s.x for s in st.query("A", since=1001, until=1003)])
    print("wszystko od 1002  :", [(s.tag_id, s.x) for s in st.query(since=1002)])
