"""Mục đích: Các công thức thống kê của bước khám phá nhãn: xác suất gặp nhãn hiếm, cỡ mẫu, khoảng tin cậy Wilson, quy tắc ba, kappa, đồng ý dương, bootstrap theo cụm video, precision@N (docs/3-gan-nhan/dac-ta-kham-pha-nhan.md mục 3.3, 4.4, 7, 8); cập nhật lần cuối: 2026-11-22.

Chỉ dùng thư viện chuẩn của Python, để chạy được ở mọi môi trường.
"""

from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from typing import Hashable, Sequence

Z95 = 1.96


def xac_suat_gap(p: float, n: int) -> float:
    """Xác suất một nhãn có tỷ lệ thật p xuất hiện ít nhất một lần trong n bình luận ngẫu nhiên: 1 − (1 − p)^n."""
    return 1 - (1 - p) ** n


def co_mau_can(sai_so: float, p: float = 0.5, z: float = Z95) -> int:
    """Cỡ mẫu để nửa độ rộng khoảng tin cậy không quá `sai_so`: n = z²·p·(1−p)/E², làm tròn lên."""
    return math.ceil(z * z * p * (1 - p) / (sai_so * sai_so))


def wilson(x: int, n: int, z: float = Z95) -> tuple[float, float, float]:
    """(tỷ lệ x/n, cận dưới, cận trên) theo khoảng Wilson."""
    if n <= 0:
        raise ValueError("n phải dương")
    tam = (x + z * z / 2) / (n + z * z)
    nua = z / (n + z * z) * math.sqrt(x * (n - x) / n + z * z / 4)
    return x / n, max(0.0, tam - nua), min(1.0, tam + nua)


def quy_tac_ba(n: int) -> float:
    """Cận trên 95% của tỷ lệ khi nhãn không xuất hiện lần nào trong n bình luận: ≈ 3/n."""
    return 3 / n


def kappa(a: Sequence[Hashable], b: Sequence[Hashable]) -> float:
    """Cohen's kappa của hai người gán cùng một danh sách: (p_o − p_e) / (1 − p_e)."""
    if len(a) != len(b) or not a:
        raise ValueError("hai danh sách phải cùng độ dài và không rỗng")
    n = len(a)
    p_o = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    p_e = sum(ca[k] * cb[k] for k in ca) / (n * n)
    if p_e == 1:
        return 1.0   # cả hai luôn gán cùng một nhãn duy nhất: không đo được, coi là đồng ý hoàn toàn
    return (p_o - p_e) / (1 - p_e)


def dong_y_duong(a: Sequence[bool], b: Sequence[bool]) -> float | None:
    """Tỷ lệ đồng ý dương 2a/(2a + b + c) cho một nhãn có/không; None nếu không ai gán nhãn đó."""
    ca = sum(1 for x, y in zip(a, b) if x and y)
    lech = sum(1 for x, y in zip(a, b) if x != y)
    return None if ca + lech == 0 else 2 * ca / (2 * ca + lech)


def bootstrap_theo_cum(co_nhan: Sequence[bool], cum: Sequence[Hashable], so_lan: int = 2000,
                       seed: int = 20261122) -> tuple[float, float, float]:
    """(tỷ lệ, cận dưới, cận trên) 95%: lấy lại có hoàn lại các cụm (video) có trong mẫu, phân vị 2,5% và 97,5%."""
    if len(co_nhan) != len(cum) or not co_nhan:
        raise ValueError("hai danh sách phải cùng độ dài và không rỗng")
    theo_cum: dict[Hashable, list[int]] = defaultdict(lambda: [0, 0])   # cụm -> [số có nhãn, số bình luận]
    for x, c in zip(co_nhan, cum):
        theo_cum[c][0] += bool(x)
        theo_cum[c][1] += 1
    cac_cum = list(theo_cum.values())
    rng = random.Random(seed)
    ty_le = []
    for _ in range(so_lan):
        chon = [cac_cum[rng.randrange(len(cac_cum))] for _ in cac_cum]
        ty_le.append(sum(c[0] for c in chon) / sum(c[1] for c in chon))
    ty_le.sort()
    return sum(co_nhan) / len(co_nhan), ty_le[int(0.025 * so_lan)], ty_le[min(so_lan - 1, int(0.975 * so_lan))]


def he_so_thiet_ke(nua_bootstrap: float, nua_wilson: float) -> float:
    """deff ≈ (nửa độ rộng bootstrap / nửa độ rộng Wilson)²."""
    return (nua_bootstrap / nua_wilson) ** 2 if nua_wilson > 0 else float("nan")


def precision_at_n(dung: Sequence[bool], n: int) -> float:
    """Tỷ lệ ứng viên đúng trong n hạng đầu (danh sách đã xếp theo hạng)."""
    if n <= 0 or n > len(dung):
        raise ValueError("n phải trong khoảng 1..độ dài danh sách")
    return sum(bool(x) for x in dung[:n]) / n
