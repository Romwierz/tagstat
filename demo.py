"""Phase 1 Demo — calculate statistics on arbitrary data without MQTT broker.

Run:  python demo.py
"""
from tagstat.model import Sample
from tagstat.store import MemoryStore
from tagstat.stats import compute_stats
from tagstat.parse import parse_message

# --- 1. Parsowanie prawdziwej wiadomości z silnika -------------------------
RAW = ('{"is_moving":false,"location":{"position":'
       '{"x":62.6,"y":53.75,"z":0.06},"strategy":"uwb_tdoa"},'
       '"tag":{"id":"45306","mac":"d8150e79b0fa"},"timestamp":1781169530643}')
s = parse_message(RAW)
print("Sparsowana wiadomość:", s)
print()

# --- 2. Ręczne dane dla kilku tagów ----------------------------------------
store = MemoryStore()

# tag stabilny: ciasny rozrzut wokół (10, 5)
for i, (dx, dy) in enumerate([(0.01, -0.01), (-0.02, 0.01),
                              (0.00, 0.02), (-0.01, -0.01)]):
    store.add(Sample("tag-stable", 10 + dx, 5 + dy, ts=1000 + i))

# tag zaszumiony: ten sam środek, ale dużo większy rozrzut
for i, (dx, dy) in enumerate([(0.5, -0.4), (-0.6, 0.3),
                              (0.2, 0.7), (-0.3, -0.5)]):
    store.add(Sample("tag-noisy", 10 + dx, 5 + dy, ts=1000 + i))

# tag w ruchu: pozycja dryfuje, system oznacza is_moving=True
for i in range(4):
    store.add(Sample("tag-moving", 20 + i, 30 + 2 * i, ts=1000 + i, is_moving=True))

# --- 3. Statystyki ----------------------------------------------------------
# referencja tylko dla taga stabilnego — znamy jego rzeczywistą pozycję
refs = {"tag-stable": (10.0, 5.0)}

print(f"{'tag':12} {'n':>2} {'mean':>16} {'std(x,y)':>16} "
      f"{'rms':>6} {'err':>6} {'moving':>7}")
for tag in store.tag_ids():
    st = compute_stats(tag, store.query(tag), ref=refs.get(tag))
    mean = f"({st.mean[0]:.2f},{st.mean[1]:.2f})"
    std = f"({st.std[0]:.3f},{st.std[1]:.3f})"
    err = f"{st.error:.3f}" if st.error is not None else "  -  "
    print(f"{tag:12} {st.count:>2} {mean:>16} {std:>16} "
          f"{st.rms:>6.3f} {err:>6} {st.moving_fraction:>6.0%}")
