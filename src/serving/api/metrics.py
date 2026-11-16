"""Công thức duy nhất cho % khen, % chê, Net (docs/EDA_requirement.md mục 1.4).

DB chỉ lưu số đếm. Mọi tỷ lệ trên dashboard đi qua hàm `summarize` ở đây, để hai
biểu đồ không bao giờ ra hai con số khác nhau cho cùng một ô.
"""
from typing import Dict, Iterable, Mapping, Optional


def summarize(n_pos: int, n_neg: int, n_neu: int, min_opinionated: int = 30) -> Dict[str, object]:
    """Tỷ lệ từ số đếm. Trung tính không vào mẫu số; mẫu số bằng 0 thì trả None."""
    opinionated = n_pos + n_neg
    praise: Optional[float] = 100.0 * n_pos / opinionated if opinionated else None
    criticism: Optional[float] = 100.0 * n_neg / opinionated if opinionated else None
    return {
        "n_pos": n_pos, "n_neg": n_neg, "n_neu": n_neu,
        "n_total": n_pos + n_neg + n_neu, "n_opinionated": opinionated,
        "praise_pct": praise, "criticism_pct": criticism,
        "net": None if praise is None else praise - criticism,
        "low_data": opinionated < min_opinionated,
    }


def add_counts(rows: Iterable[Mapping[str, int]]) -> Dict[str, int]:
    """Cộng số đếm của nhiều dòng aggregates (cộng tử và mẫu, không lấy trung bình %)."""
    total = {"n_pos": 0, "n_neg": 0, "n_neu": 0}
    for row in rows:
        for key in total:
            total[key] += int(row.get(key) or 0)
    return total


def same_counts(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    return all(int(left.get(key) or 0) == int(right.get(key) or 0) for key in ("n_pos", "n_neg", "n_neu"))
