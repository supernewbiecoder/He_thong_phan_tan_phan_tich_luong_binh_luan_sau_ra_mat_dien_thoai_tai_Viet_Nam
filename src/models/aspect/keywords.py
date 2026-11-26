"""Mục đích: Bộ từ khóa cho 11 khía cạnh của bộ nhãn chốt và hàm tìm khía cạnh được nhắc trong một đoạn chữ; dùng chung cho luật mốc của bước suy luận (src/models/run.py) và notebook 3_aspect_keywords (docs/4-mo-hinh/dac-ta-suy-luan.md mục 3); cập nhật lần cuối: 2026-11-26.

Từ khóa của rule-v1 chuyển sang mã khía cạnh chốt (src/labeling/final_labels.py): tách "thiết kế & độ bền" thành
`thiet_ke` và `do_ben`; tách "bảo hành & hậu mãi" thành `bao_hanh_sua_chua` và `mua_ban` (chính hãng, xách tay, cửa
hàng, trả góp, lên đời, ý định mua); "trả góp" chuyển từ giá sang `mua_ban` (hướng dẫn gán chính thức mục 2).
Luật không đoán `may_chung`, `hang_nguoi_dung`, `khac`: các nhãn này không có từ khóa đủ rõ.
So khớp trên `text_clean` (giữ chữ hoa, vì "AI" khác "ai"), không phân biệt hoa thường trừ chỗ ghi (?-i:...).
Đây là ước lượng bằng từ khóa, không phải nhãn: bỏ sót cách nói không có từ khóa ("máy đẹp") và có thể bắt nhầm.
"""

from __future__ import annotations

import re

from src.labeling.final_labels import ASPECTS, NAMES

MA_KHIA_CANH = ASPECTS
TEN_KHIA_CANH = {ma: NAMES[ma] for ma in ASPECTS}

TU_KHOA = {   # mã khía cạnh -> [(nhãn từ khóa, regex)], so khớp không phân biệt hoa thường
    "pin_sac": [
        ("pin", r"\bpin\b"),
        ("sạc", r"\bsạc\b|\bsac (?:nhanh|không dây|khong day)\b"),
        ("mAh, số W", r"\d\s?mah\b|\bmah\b|\b\d{2,3}\s?w\b"),
        ("trâu (trừ trẻ trâu)", r"(?<!trẻ )\btrâu\b"),
        ("thời lượng pin, SOT", r"\bthời lượng (?:pin|sử dụng|dùng)\b|\bsot\b"),
    ],
    "man_hinh": [
        ("màn hình", r"\bmàn hình\b|\bman hinh\b"),
        ("màn (viết tắt)", r"\bmàn\b(?! hình| ra mắt| trình diễn)"),
        ("tấm nền", r"\b(?:oled|amoled|lcd|ltpo)\b|\btấm nền\b"),
        ("tần số quét, Hz", r"\b\d{2,3}\s?hz\b|\btần số quét\b"),
        ("độ sáng, nit", r"\bđộ sáng\b|\b\d+\s?nits?\b"),
        ("độ phân giải", r"\bđộ phân giải\b|\b(?:2k|qhd|fhd)\b"),
        ("tai thỏ, đục lỗ", r"\btai thỏ\b|\bdynamic island\b|\bđục lỗ\b|\bnốt ruồi\b"),
    ],
    "hieu_nang": [
        ("hiệu năng", r"\bhiệu năng\b|\bhieu nang\b|\bhiệu suất\b"),
        ("chip", r"\bchip\b|\bchíp\b|\bcpu\b|\bgpu\b|\bsnapdragon\b|\bsnap\b|\bexynos\b|\bdimensity\b|\bhelio\b"
                 r"|\btensor\b|\bkirin\b|\bbionic\b|\ba1\d (?:pro|bionic)\b|\b8 gen \d\b|\b8 elite\b"),
        ("RAM", r"\bram\b"),
        ("lag, mượt", r"\blag\b|\bkhựng\b|\btreo máy\b|\bđơ máy\b|\bmượt\b"),
        ("game", r"\bgame\b|\bfps\b|\bpubg\b|\bliên quân\b|\bgenshin\b"),
        ("điểm hiệu năng", r"\bantutu\b|\bgeekbench\b|\bbenchmark\b"),
        ("nóng máy", r"\bnóng máy\b|\bmáy nóng\b|\bnóng quá\b|\bhơi nóng\b|\bbị nóng\b|\bnóng ran\b"
                     r"|\bnhiệt độ\b|\btản nhiệt\b|\bquá nhiệt\b"),
    ],
    "camera": [
        ("camera, cam", r"\bcamera\b|(?<!màu )(?<!quả )\bcam\b(?!\s*(?:ơn|on|thấy|thay|giác|giac|xúc|xuc)\b)"),
        ("chụp", r"\bchụp\b|\bchup\b"),
        ("quay video", r"\bquay (?:phim|video|chậm|4k|8k|đêm)\b"),
        ("zoom, ống kính", r"\bzoom\b|\btele\b|\btelephoto\b|\bgóc rộng\b|\bsiêu rộng\b|\bống kính\b|\bcảm biến\b"),
        ("selfie", r"\bselfie\b"),
        ("số MP", r"\d\s?mp\b|\bmegapixel\b"),
        ("ảnh", r"\bảnh (?:chụp|đẹp|xấu|nét|mờ)\b|\bbức ảnh\b|\bchất lượng ảnh\b"),
        ("chống rung", r"\bchống rung\b|\bois\b"),
    ],
    "thiet_ke": [
        ("thiết kế, ngoại hình", r"\bthiết kế\b|\bthiet ke\b|\bngoại hình\b|\bkiểu dáng\b"),
        ("chất liệu", r"\btitan\b|\btitanium\b|\bnhôm\b|\bkhung viền\b|\bmặt lưng\b|\bkính lưng\b|\bgorilla\b"),
        ("cầm, mỏng, trọng lượng", r"\bcầm\b|\bmỏng\b|\btrọng lượng\b|\bnặng tay\b|\bmáy nặng\b"),
        ("màu máy", r"\bmàu (?:cam|xanh|đen|trắng|tím|hồng|vàng|bạc|xám|titan)\b"),
    ],
    "do_ben": [
        ("độ bền, rơi vỡ", r"\bđộ bền\b|(?<!pin )\bbền\b|\b(?:làm rơi|bị rơi|rơi vỡ|rơi xuống)\b|\bvỡ\b(?! mộng)"
                           r"|\bnứt\b|\btrầy\b|\bxước\b|\bmóp\b"),
        ("chống nước", r"\bchống nước\b|\bkháng nước\b|\bip6[78]\b"),
    ],
    "phan_mem": [
        ("phần mềm, hệ điều hành", r"\bphần mềm\b|\bphan mem\b|\bhệ điều hành\b"),
        ("iOS, Android", r"\bios\b|\bandroid\b"),
        ("giao diện của hãng", r"\bone ?ui\b|\bhyper ?os\b|\bmiui\b|\bcolor ?os\b|\borigin ?os\b|\bfuntouch\b"
                               r"|\bmagic ?os\b|\bemui\b|\bharmony ?os\b"),
        ("cập nhật", r"\bcập nhật\b|\bcap nhat\b|\bupdate\b"),
        ("giao diện, tính năng, ứng dụng", r"\bgiao diện\b|\btính năng\b|\bứng dụng\b|\bapp\b"),
        ("AI", r"(?-i:\bAI\b)|\bgalaxy ai\b|\bapple intelligence\b|\btrí tuệ nhân tạo\b"),
    ],
    "phan_cung_khac": [
        ("loa, âm thanh", r"\bloa\b|\bâm thanh\b|\bam thanh\b"),
        ("rung", r"(?<!chống )\brung\b|\bhaptic\b"),
        ("vân tay, Face ID", r"\bvân tay\b|\bvan tay\b|\bface ?id\b|\bmở khóa\b"),
        ("sóng, kết nối", r"(?<!lên )(?<!phát )\bsóng\b|\bwi-?fi\b|\bbluetooth\b|\b[45]g\b|\bgps\b|\bnfc\b|\be?sim\b"),
        ("bộ nhớ", r"\bbộ nhớ\b|\brom\b|\b\d+\s?(?:gb|tb)\b"),
        ("bút", r"\bs ?pen\b|\bbút\b"),
        ("cổng, nút", r"\bcổng sạc\b|\btype-?c\b|\busb\b|\blightning\b|\bjack 3[.,]5\b|\btai nghe\b"
                      r"|\bnút (?:nguồn|âm lượng|bấm|chụp)\b|\bcamera control\b|\baction button\b"),
    ],
    "gia": [
        ("giá", r"\bgiá\b(?! như| mà)|\bgia (?:re|cao|ban)\b"),
        ("tiền, triệu", r"\btiền\b|\btriệu\b|\b\d+(?:[.,]\d+)?\s?(?:tr|củ)\b|\b\d{2,}k\b|\bvn[dđ]\b"),
        ("đắt, rẻ", r"\bđắt\b|\brẻ\b|\bchát\b|\bmắc quá\b"),
        ("đáng tiền, giữ giá", r"\bđáng (?:tiền|mua|đồng tiền)\b|\bgiữ giá\b|\bmất giá\b|\bp/p\b"),
        ("khuyến mãi", r"\bkhuyến mãi\b|\bgiảm giá\b|\bsale\b"),
    ],
    "bao_hanh_sua_chua": [
        ("bảo hành, hậu mãi", r"\bbảo hành\b|\bbao hanh\b|\bttbh\b|\bhậu mãi\b"),
        ("sửa chữa, đổi trả", r"\bsửa chữa\b|\bđi sửa\b|\bthay (?:màn|pin|main)\b|\b1 đổi 1\b|\bmột đổi một\b|\bđổi trả\b"),
        ("dịch vụ, CSKH", r"\bdịch vụ\b|\bchăm sóc khách hàng\b|\bcskh\b"),
    ],
    "mua_ban": [
        ("chính hãng, xách tay", r"\bchính hãng\b|\bchinh hang\b|\bxách tay\b|\bxach tay\b|\bhàng dựng\b"
                                 r"|\b(?:bản|máy|hàng) lock\b|\bbản quốc tế\b"),
        ("cửa hàng", r"\bcửa hàng\b|\bshop\b|\btgdđ\b|\bthế giới di động\b|\bcellphones\b|\bhoàng hà\b"
                     r"|\bdi động việt\b|\bshopdunk\b|\btopzone\b"),
        ("trả góp", r"\btrả góp\b|\btra gop\b"),
        ("lên đời, đổi máy", r"\blên đời\b|\bđổi máy\b|\btrade(?:-| )?in\b|\bthu cũ\b|\bbán lại\b"),
        ("mua ở đâu, ý định mua", r"\bmua (?:ở|chỗ|tại) (?:đâu|nào)\b|\bchỗ mua\b|\bnên mua\b|\bđịnh mua\b|\bchờ mua\b"
                                  r"|\bđợi (?:giảm giá|giá giảm|hạ giá)\b|\bđặt (?:trước|hàng)\b"),
    ],
}

_MAU = {ma: re.compile("|".join(f"(?:{mau})" for _, mau in TU_KHOA[ma]), re.IGNORECASE) for ma in MA_KHIA_CANH}


def khia_canh(text: str) -> list[str]:
    """Các mã khía cạnh có từ khóa trong `text`, theo thứ tự ASPECTS (src/labeling/final_labels.py)."""
    if not text:
        return []
    return [ma for ma in MA_KHIA_CANH if _MAU[ma].search(text)]
