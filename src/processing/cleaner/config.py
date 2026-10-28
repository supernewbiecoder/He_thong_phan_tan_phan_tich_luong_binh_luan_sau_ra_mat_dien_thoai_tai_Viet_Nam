# -*- coding: utf-8 -*-
"""
Configuration file for data cleaning, teencode mapping, 
clause splitting conjunctions, and spam detection rules.
Empirically updated and verified against 109,344 real comments in comments.jsonl.
"""
import re

# 1. Comprehensive Teencode and abbreviation dictionary for Vietnamese tech comments
TEENCODE_DICT = {
    # --- CỤM TỪ CÔNG NGHỆ & LỖI THƯỜNG GẶP (MULTI-WORD PHRASES ƯU TIÊN MATCH TRƯỚC) ---
    "cam trc": "camera trước",
    "cam trước": "camera trước",
    "cam sau": "camera sau",
    "pin trau": "pin trâu",
    "pin trâu": "pin trâu",
    "sac nhanh": "sạc nhanh",
    "sạc nhanh": "sạc nhanh",
    "sac cham": "sạc chậm",
    "sạc chậm": "sạc chậm",
    "chai pin": "chai pin",
    "sap nguon": "sập nguồn",
    "sập nguồn": "sập nguồn",
    "lag giat": "lag giật",
    "lag giật": "lag giật",
    "giat lag": "lag giật",
    "giật lag": "lag giật",
    "drop fps": "tụt khung hình",
    "tut fps": "tụt khung hình",
    "soc man": "sọc màn",
    "sọc màn": "sọc màn",
    "am vang": "ám vàng",
    "ám vàng": "ám vàng",
    "am xanh": "ám xanh",
    "ám xanh": "ám xanh",
    "chay muc": "chảy mực",
    "chảy mực": "chảy mực",
    "chong nuoc": "chống nước",
    "chống nước": "chống nước",
    "can tay": "cấn tay",
    "cấn tay": "cấn tay",
    "van tay": "vân tay",
    "vân tay": "vân tay",
    "xach tay": "xách tay",
    "xách tay": "xách tay",
    "chinh hang": "chính hãng",
    "chính hãng": "chính hãng",
    "tam gia": "tầm giá",
    "tầm giá": "tầm giá",
    "gia re": "giá rẻ",
    "giá rẻ": "giá rẻ",
    "gia chat": "giá chát",
    "giá chát": "giá chát",
    "dang tien": "đáng tiền",
    "đáng tiền": "đáng tiền",
    "bao hanh": "bảo hành",
    "bảo hành": "bảo hành",
    "doi tra": "đổi trả",
    "đổi trả": "đổi trả",
    "man hinh": "màn hình",
    "màn hinh": "màn hình",
    "man oled": "màn hình oled",
    "man amoled": "màn hình amoled",
    "ung dung": "ứng dụng",
    "he dieu hanh": "hệ điều hành",
    "quay phim": "quay phim",
    "chup anh": "chụp ảnh",
    "chụp ảnh": "chụp ảnh",
    "xoa phong": "xóa phông",
    "xóa phông": "xóa phông",
    "chup dem": "chụp đêm",
    "chụp đêm": "chụp đêm",
    "chong rung": "chống rung",
    "chống rung": "chống rung",
    "goc rong": "góc rộng",
    "góc rộng": "góc rộng",
    "tan so quet": "tần số quét",
    "tần số quét": "tần số quét",
    "on screen": "on screen",
    "onscreen": "on screen",

    # --- CỤM TỪ GIAO TIẾP & KHẲNG ĐỊNH/PHỦ ĐỊNH ---
    "đúng r": "đúng rồi",
    "dung r": "đúng rồi",
    "đr": "đúng rồi",
    "dr": "đúng rồi",
    "k bit": "không biết",
    "k biet": "không biết",
    "ko bit": "không biết",
    "ko biet": "không biết",
    "kbt": "không biết",
    "kb": "không biết",
    "kbg": "không bao giờ",
    "ko bao gio": "không bao giờ",
    "chs": "chẳng hiểu sao",
    "chẳng hỉu": "chẳng hiểu",
    "k hiểu": "không hiểu",
    "ko hiểu": "không hiểu",
    "clgt": "cái gì thế",
    "như v": "như vậy",
    "như z": "như vậy",
    "thế v": "thế vậy",
    "thế z": "thế vậy",

    # --- TỪ PHỦ ĐỊNH / TRỢ TỪ ĐƠN LẺ ---
    "k": "không",
    "ko": "không",
    "kh": "không",
    "khg": "không",
    "kg": "không",
    "hok": "không",
    "hông": "không",
    "hong": "không",
    "hem": "không",
    "kô": "không",
    "đek": "không",
    "dek": "không",
    "đéo": "không",
    "đc": "được",
    "dc": "được",
    "đk": "được",
    "dk": "được",
    "ntn": "như thế nào",
    "tn": "thế nào",
    "sao": "sao",
    "s": "sao",
    "ms": "mới",
    "r": "rồi",
    "roi": "rồi",
    "rùi": "rồi",

    # --- ĐẠI TỪ XƯNG HÔ / TÁC GIẢ ---
    "mik": "mình",
    "mk": "mình",
    "mềnh": "mình",
    "ngta": "người ta",
    "ng": "người",
    "thg": "thằng",
    "ae": "anh em",
    "ace": "anh chị em",
    "mn": "mọi người",
    "mng": "mọi người",
    "ad": "admin",
    "qtv": "quản trị viên",
    "tui": "tôi",

    # --- LIÊN TỪ / TỪ NỐI / ĐẶC TÍNH / MỨC ĐỘ ---
    "vs": "với",
    "cx": "cũng",
    "nv": "như vậy",
    "tl": "trả lời",
    "cmt": "bình luận",
    "bl": "bình luận",
    "ns": "nói",
    "nx": "nhận xét",
    "ib": "inbox",
    "sp": "sản phẩm",
    "bh": "bây giờ",
    "bjo": "bây giờ",
    "h": "giờ",
    "z": "vậy",
    "v": "vậy",
    "vay": "vậy",
    "j": "gì",
    "ji": "gì",
    "thui": "thôi",
    "thik": "thích",
    "thix": "thích",
    "tot": "tốt",
    "bth": "bình thường",
    "bthg": "bình thường",
    "bt": "bình thường",
    "chi": "chỉ",
    "rat": "rất",
    "wa": "quá",
    "qua": "quá",
    "nhiu": "nhiều",
    "nhìu": "nhiều",
    "it": "ít",
    "luc": "lúc",
    "hon": "hơn",
    "lm": "làm",
    "vl": "rất nhiều",
    "vcl": "rất nhiều",
    "vkl": "rất nhiều",
    "vđ": "rất nhiều",
    "xài": "dùng",
    "xai": "dùng",

    # --- THIẾT BỊ / HÃNG / CÔNG NGHỆ ---
    "đt": "điện thoại",
    "dt": "điện thoại",
    "đth": "điện thoại",
    "dthoai": "điện thoại",
    "đthoai": "điện thoại",
    "cam": "camera",
    "cams": "camera",
    "mh": "màn hình",
    "man": "màn",
    "ip": "iphone",
    "ss": "samsung",
    "sam": "samsung",
    "prm": "pro max",
    "promax": "pro max",
    "plus": "plus",
    "ultra": "ultra",
    "trau": "trâu",
    "lac": "lag",
    "giat": "giật",
    "nong": "nóng",
    "sac": "sạc",
    "snap": "snapdragon",
    "exy": "exynos",
    "exynos": "exynos",
    "dimen": "dimensity",
    "dimensity": "dimensity",
    "app": "ứng dụng",
    "os": "hệ điều hành",
    "chíp": "chip",
    "rom": "rom",
    "ram": "ram",
    "pin": "pin",
    "update": "cập nhật",
    "up": "nâng cấp",
    "ok": "ổn",
    "oke": "ổn",
    "oki": "ổn",
    "okie": "ổn",
    "tks": "cảm ơn",
    "cảm ơn": "cảm ơn",
    "ty": "cảm ơn",
    "thx": "cảm ơn",
    "tgdd": "thế giới di động",
    "tggd": "thế giới di động",
    "fpt": "fpt shop",
    "cps": "cellphones",
}

# 2. Conjunctions for splitting clauses (Mệnh đề)
# Theo yêu cầu đề tài: tách theo dấu câu và từ nối ("nhưng", "mà", "còn", "tuy", ...)
CLAUSE_CONJUNCTIONS = [
    "nhưng mà",
    "thế nhưng",
    "nhưng",
    "cơ mà",
    "tuy nhiên",
    "mặc dù",
    "tuy",
    "dẫu",
    "song",
    "còn",
    "chứ còn",
    "chứ",
    "mà",
    "trong khi",
    "ngược lại",
    "thay vì",
    "bù lại",
    "đổi lại",
]

# 3. Punctuation regex for sentence / clause boundary
PUNCT_SPLIT_REGEX = re.compile(r'[\r\n\.\,\!\?\;\:\—\–\|]+')

# 4. Spam detection regex patterns
URL_REGEX = re.compile(
    r'(?:https?://|ftp://|www\.)[^\s/$.?#].[^\s]*|'
    r'\b(?:[a-zA-Z0-9-]+\.)+(?:com|vn|net|org|xyz|info|top|vip|club|me|cc|online|site|store|app|link|io)\b(?:/[^\s]*)?',
    re.IGNORECASE
)

PHONE_REGEX = re.compile(
    r'(?:\+?84|0)(?:3[2-9]|5[25689]|7[06-9]|8[1-9]|9[0-9])[\s\.\-]?(?:\d{3}[\s\.\-]?\d{3}|\d{4}[\s\.\-]?\d{3}|\d{7})\b|'
    r'\b\d{4}[\s\.\-]\d{3}[\s\.\-]\d{3}\b'
)

CONTACT_INVITE_REGEX = re.compile(
    r'\b(?:zalo|telegram|tele|inbox|ib\s+cho|nhắn\s+tin|liên\s+hệ|add\s+zalo|kết\s+bạn\s+zalo|hotline|qua\s+zalo)\b',
    re.IGNORECASE
)

COMMERCIAL_SPAM_REGEX = re.compile(
    r'\b(?:shopee|lazada|tiki|mã\s+giảm\s+giá|voucher|kiếm\s+tiền\s+online|hoa\s+hồng|hoa\s+hông|'
    r'tài\s+xỉu|kubet|thabet|nohu|nổ\s+hũ|baccarat|casino|nhận\s+kèo|đầu\s+tư\s+sinh\s+lời|'
    r'chiết\s+khấu|link\s+mua|link\s+dưới\s+mô\s+tả|săn\s+sale|bán\s+hàng\s+online)\b',
    re.IGNORECASE
)

REPETITIVE_CHAR_REGEX = re.compile(r'([^\s])\1{5,}')
REPETITIVE_WORD_REGEX = re.compile(r'\b(\w+)(?:\s+\1){3,}\b', re.IGNORECASE)

# 5. Vietnamese alphabet and diacritics for language verification
VIETNAMESE_CHARS = set(
    "aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵđ"
    "AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬEÈÉẺẼẸÊỀẾỂỄỆIÌÍỈĨỊOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢUÙÚỦŨỤƯỪỨỬỮỰYỲÝỶỸỴĐ"
)

COMMON_VIETNAMESE_WORDS = {
    "anh", "em", "ban", "bac", "ong", "ba", "may", "tao", "minh", "chung", "to",
    "khong", "co", "la", "va", "nhung", "thi", "ma", "de", "nguoi", "nha", "dien",
    "thoai", "pin", "man", "hinh", "camera", "gia", "tien", "mua", "dung", "xai",
    "tot", "dep", "xau", "trau", "lag", "giat", "do", "nhieu", "it", "hon", "qua",
    "duoc", "biet", "thay", "noi", "nghe", "xem", "video", "kenh", "review", "unbox",
    "chip", "sac", "ram", "rom", "nang", "nhe", "re", "dat", "cung", "nhu", "the"
}

# 6. Aspect list according to the project specification
ASPECT_CATEGORIES = [
    "PERFORMANCE",
    "BATTERY",
    "DISPLAY",
    "CAMERA",
    "DESIGN",
    "SOFTWARE",
    "HARDWARE_OTHER",
    "PRICE",
    "AFTER_SALES",
    "GENERAL"
]
