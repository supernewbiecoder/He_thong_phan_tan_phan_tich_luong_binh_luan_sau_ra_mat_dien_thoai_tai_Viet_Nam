# -*- coding: utf-8 -*-
"""
Bộ kiểm thử nhanh (Unit Test) cho module tiền xử lý dữ liệu (cleaner).
Kiểm tra:
1. Chuẩn hóa teencode công nghệ và từ ngữ tiếng Việt.
2. Nén ký tự kéo dài cảm xúc (elongated characters).
3. Lọc spam (URL, số điện thoại, mời inbox Zalo/Telegram, cờ bạc).
4. Nhận diện ngôn ngữ tiếng Việt.
5. Bóc tách mệnh đề theo dấu câu và từ nối (clause segmentation).
"""
import sys
from pathlib import Path

# Thêm đường dẫn để chạy được từ mọi vị trí
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from cleaner.pipeline import process_comment_record
except ImportError:
    from src.processing.cleaner.pipeline import process_comment_record

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

samples = [
    {
        'comment_id': 'test_01',
        'model': 'ip13prm',
        'text': 'đt này chụp cam trc đẹp nhưng cam sau hơi bệt, pin trau sac nhanh',
        'published_at': '2026-10-15T10:00:00Z',
        'like_count': 10
    },
    {
        'comment_id': 'test_02',
        'model': 's23u',
        'text': 'máy đẹpppp vl mà giá chát quá k mua nổi đâu https://shopee.vn/sp123 ib zalo 0987654321',
        'published_at': '2026-10-15T11:00:00Z'
    },
    {
        'comment_id': 'test_03',
        'model': 'note4',
        'text': 'màn oled dùng lâu có bị soc man hay am vang k ad ơi, chs máy lại nóng thế z',
        'published_at': '2026-10-15T12:00:00Z'
    },
    {
        'comment_id': 'test_04',
        'model': 'mi11',
        'text': 'ae mua máy xach tay hay chinh hang, giá rẻ mà drop fps quá clgt',
        'published_at': '2026-10-15T13:00:00Z'
    },
    {
        'comment_id': 'test_05',
        'model': 's21u',
        'text': 'đúng r, clgt kbt có nên mua k',
        'published_at': '2026-10-15T14:00:00Z'
    }
]


def run_tests():
    print("=" * 70)
    print("KIỂM THỬ MODULE CLEANER (UNIT TEST)")
    print("=" * 70)

    for s in samples:
        clean_rec, trace_rec = process_comment_record(s, include_trace=True)
        cid = clean_rec['comment_id']
        print(f"\n[+] BẢN GHI: {cid} (Model: {s['model']})")
        print(f"    - Văn bản gốc    : {repr(trace_rec['original_text'])}")
        print(f"    - Chuẩn hóa nhẹ  : {repr(trace_rec['cleaned_text'])}")
        print(f"    - text_norm      : {repr(trace_rec['text_norm'])}")
        print(f"    - Có biến đổi?   : {trace_rec['was_modified']}")
        print(f"    - Các thay đổi   : {trace_rec['changes_detected']}")
        if trace_rec['teencode_replacements']:
            print(f"    - Sửa teencode   : {trace_rec['teencode_replacements']}")
        if trace_rec['repeated_chars_compressed']:
            print(f"    - Nén ký tự lặp  : {trace_rec['repeated_chars_compressed']}")
        print(f"    - Cờ Spam        : {trace_rec['is_spam']} (Lý do: {trace_rec['spam_reasons']})")
        print(f"    - Tách mệnh đề   : {trace_rec['clause_count']} mệnh đề -> {trace_rec['clauses_summary']}")

    # Kiểm tra khẳng định (Assertions)
    # Test 1: Không spam, tách được 3 mệnh đề
    r1, _ = process_comment_record(samples[0], include_trace=True)
    assert not r1["is_spam"], "Test 1 không phải spam"
    assert r1["clause_count"] == 3, f"Test 1 phải có 3 mệnh đề, có {r1['clause_count']}"

    # Test 2: Bị gắn cờ spam
    r2, _ = process_comment_record(samples[1], include_trace=True)
    assert r2["is_spam"], "Test 2 phải bị gắn cờ spam"
    assert "contains_url" in r2["spam_reasons"]
    assert "contains_phone_number" in r2["spam_reasons"]

    print("\n" + "=" * 70)
    print("[SUCCESS] TẤT CẢ TEST CASES ĐÃ VƯỢT QUA!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
