"""Nhận diện ngôn ngữ của bình luận, tách khỏi quyết định spam.

Trả về một trong ba giá trị, giống trường `lang` trong guideline gán nhãn:
  "vi"     có nội dung tiếng Việt (có dấu, không dấu, teencode)
  "other"  nội dung là ngôn ngữ khác
  "none"   không xác định được: emoji, dấu câu, số, tên máy, từ quốc tế

`is_vietnamese` trong dữ liệu = (lang == "vi").

Vì sao không dùng lại hàm của cleaner: tập VIETNAMESE_CHARS ở đó chứa cả nguyên âm
không dấu (a, e, i, o, u, y) nên mọi câu tiếng Anh có nguyên âm đều được coi là
tiếng Việt. Ở đây chỉ coi là bằng chứng tiếng Việt khi có ký tự mà riêng tiếng
Việt mới dùng, hoặc có từ tiếng Việt không dấu thông dụng.
"""
import re
import unicodedata
from typing import Set

# Ký tự chỉ tiếng Việt mới có (không tính à, á, é, ó… vì tiếng Pháp, Tây Ban Nha cũng dùng).
_VI_ONLY_CHARS = set(
    "ăằắẳẵặâầấẩẫậđêềếểễệôồốổỗộơờớởỡợưừứửữự"
    "ảãạẻẽẹỉĩịỏõọủũụỳỷỹỵ"
)
# Nguyên âm có dấu mà ngôn ngữ khác cũng dùng: chỉ là bằng chứng yếu.
_SHARED_ACCENTS = set("àáèéìíòóùúý")

_NON_LATIN = re.compile(
    "[Ѐ-ӿ֐-׿؀-ۿऀ-ॿ฀-๿"
    "぀-ヿ㐀-䶿一-鿿가-힯]"
)
_LATIN_WORD = re.compile(r"[a-zà-ỹđ]+", re.IGNORECASE)

# Từ tiếng Việt không dấu / teencode hay gặp và KHÔNG phải từ tiếng Anh thông dụng.
_VI_WORDS: Set[str] = set("""
khong ko kh hok hong k dc duoc đc la cua nhung nhug minh mik mk may tao toi tui em anh chi
ban bac ong chu co cung cx roi r nha nhe nhi vay vậy z gi j sao the thi nay kia day do
dien thoai dt đt man hinh pin sac cam chup anh gia tien trieu tr cu mua xai dung
tot dep xau ngon re dat nhanh cham muot giat nong lag hay qua wa lam rat nhieu nhiu it hon
nguoi ng ae mn moi biet bit thay thich thik nen neu vi vs voi ma con chua chac
oi a ah ạ uh uk vl vcl vkl đm dm deo đéo vãi
bao nhieu khi nao tai lam viec choi xem coi nghe noi hoi tra loi cam on thanks
nam thang ngay hom qua mai sau truoc tren duoi trong ngoai
""".split())
_VI_WORDS -= {"a", "the", "do", "may", "man", "cam", "pin", "it", "con", "tra", "mai", "lam", "nam",
              "sao", "hay", "thanks", "lag", "vs", "uh", "uk", "ah", "on", "day"}

# Từ tiếng Anh thông dụng và không trùng âm tiết tiếng Việt không dấu.
_EN_WORDS: Set[str] = set("""
and is are was were this that these those with without you your yours for of not but have has had
what when where why how very really good great best better worse bad love like phone phones thanks
thank please will would should could from they them their we our my be been by or as if all one
more most there here just about which who does did its much many some any only also too out get
got make made still now new old use used using buy bought nice awesome amazing cool hello review
video channel think know want need looks look looking better than then because subtitles english
it's i'm don't doesn't can't isn't that's
""".split())

# Từ không cho biết ngôn ngữ: tên hãng, tên máy, thuật ngữ, từ cảm thán quốc tế.
_NEUTRAL_WORDS: Set[str] = set("""
iphone ip ipad apple samsung ss galaxy note ultra pro max plus mini xiaomi mi redmi poco oppo vivo
realme huawei honor nokia sony lg google pixel oneplus android ios snapdragon exynos chip ram rom
gb hz mah fps oled amoled camera cam zoom ok oke okay okie wow haha hihi hehe huhu lol first top
like sub tks thx hi vip no yes youtube facebook fb zalo tiktok shopee lazada review unbox test
""".split())


def detect_language(text: str) -> str:
    """Phân loại ngôn ngữ của một bình luận: "vi", "other" hoặc "none"."""
    normalized = unicodedata.normalize("NFC", text or "").lower()
    if any(char in _VI_ONLY_CHARS for char in normalized):
        return "vi"

    words = _LATIN_WORD.findall(normalized)
    non_latin = len(_NON_LATIN.findall(normalized))
    vi_hits = sum(1 for word in words if word in _VI_WORDS)
    en_hits = sum(1 for word in words if word in _EN_WORDS)
    if any(char in _SHARED_ACCENTS for char in normalized) and en_hits == 0:
        # "quá", "màn", "giá"… đứng một mình: gần như chắc là tiếng Việt trong dữ liệu này.
        vi_hits += 1

    if vi_hits and vi_hits >= en_hits:
        return "vi"
    if non_latin >= 2 and non_latin >= len(words):
        return "other"
    if en_hits >= 2 or (en_hits == 1 and len(words) <= 3 and not vi_hits):
        return "other"

    informative = [word for word in words if word not in _NEUTRAL_WORDS and len(word) > 1]
    if not informative:
        return "none"
    # Chữ Latin không dấu, không khớp từ điển nào. Trong dữ liệu bình luận video
    # tiếng Việt, khả năng cao là tiếng Việt không dấu; nghiêng về "vi" để không
    # loại nhầm ý kiến thật (nguyên tắc ưu tiên precision khi loại bỏ).
    return "vi" if len(informative) >= 2 else "none"


def is_vietnamese(text: str) -> bool:
    return detect_language(text) == "vi"
