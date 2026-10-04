"""Yüzük ölçüsü dönüşümleri.

Temel birim parmak çevresidir (mm). Avrupa/ISO ölçüsü doğrudan çevreye eşittir,
Türk ölçüsü çevre - 40'tır, ABD ölçüsü yaklaşık 36.5 + 2.55 * US formülüyle
çevreye çevrilir.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

TR_OFFSET = 40.0
US_BASE = 36.5
US_STEP = 2.55

_PATTERN = re.compile(r"^\s*(TR|EU|ISO|US)?\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*(TR|EU|ISO|US|MM)?\s*$", re.I)


@dataclass(frozen=True)
class RingSize:
    circumference_mm: float

    @property
    def eu(self) -> float:
        return round(self.circumference_mm * 2) / 2

    @property
    def tr(self) -> float:
        return round((self.circumference_mm - TR_OFFSET) * 2) / 2

    @property
    def us(self) -> float:
        return round((self.circumference_mm - US_BASE) / US_STEP * 2) / 2

    @property
    def diameter_mm(self) -> float:
        return round(self.circumference_mm / math.pi, 1)

    def label(self) -> str:
        return f"TR {_fmt(self.tr)} / EU {_fmt(self.eu)} / US {_fmt(self.us)}"


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else f"{value:g}"


def parse_ring_size(text: str, default_system: str = "auto") -> RingSize:
    """'TR 20', 'EU 60', 'US 9', '60' gibi değerleri çözümler.

    Sistem belirtilmemişse: 30 ve üzeri EU (çevre), 14'ten küçükler US,
    aradakiler TR kabul edilir.
    """
    match = _PATTERN.match(text or "")
    if not match:
        raise ValueError(f"Yüzük ölçüsü anlaşılamadı: {text!r}")
    system = (match.group(1) or match.group(3) or default_system).upper()
    value = float(match.group(2).replace(",", "."))
    if system == "AUTO":
        system = "EU" if value >= 30 else "US" if value < 14 else "TR"
    if system in ("EU", "ISO", "MM"):
        circ = value
    elif system == "TR":
        circ = value + TR_OFFSET
    else:
        circ = US_BASE + US_STEP * value
    if not 40 <= circ <= 80:
        raise ValueError(f"Yüzük ölçüsü makul aralıkta değil: {text!r}")
    return RingSize(circ)
