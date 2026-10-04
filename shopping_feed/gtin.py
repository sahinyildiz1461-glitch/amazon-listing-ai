"""GTIN (EAN/UPC/ISBN) kontrol hanesi doğrulaması."""


def is_valid_gtin(value: str) -> bool:
    digits = (value or "").strip()
    if not digits.isdigit() or len(digits) not in (8, 12, 13, 14):
        return False
    if set(digits) == {"0"}:
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check
