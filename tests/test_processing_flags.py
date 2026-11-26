"""Mục đích: Kiểm bước 2.4 – gắn cờ tiếng Việt và spam (src/processing/flags.py, docs/2-tien-xu-ly/dac-ta-gan-co.md); cập nhật lần cuối: 2026-11-20.

Chỉ dùng câu tự soạn. Chạy: python -m unittest tests.test_processing_flags
"""

import unittest

from src.processing import flags as F


class TiengViet(unittest.TestCase):
    def test_co_dau_la_tieng_viet(self):
        for s in ["Pin trâu quá", "đẹp", "Máy này ok", "đẹp 很好"]:
            self.assertEqual(F.nhan_tieng_viet(s), (True, F.CO_DAU), s)

    def test_khong_dau_van_la_tieng_viet(self):
        for s in ["pin trau qua", "may nay dung ngon lam", "iphone dep qua", "ko dc j het", "camera chup dem dep"]:
            self.assertEqual(F.nhan_tieng_viet(s), (True, F.KHONG_DAU), s)

    def test_tieng_nuoc_ngoai(self):
        for s in ["nice phone bro", "the best phone ever", "great phone man"]:
            self.assertEqual(F.nhan_tieng_viet(s), (False, F.NGOAI_NGU), s)
        for s in ["这个手机很好", "отличный телефон", "좋은 폰"]:
            self.assertEqual(F.nhan_tieng_viet(s), (False, F.CHU_KHAC_LATIN), s)

    def test_khong_du_chu_thi_khong_ket_luan_la_nuoc_ngoai(self):
        for s in ["", "😂😂😂", "iPhone 17 Pro Max", "wow", "ip17prm", "<url>"]:
            self.assertEqual(F.nhan_tieng_viet(s), (True, F.KHONG_DU_CHU), s)


class Spam(unittest.TestCase):
    def test_tung_ly_do(self):
        ca = {
            "xem thêm tại https://abc.xyz/khuyen-mai": [F.LIEN_KET],
            "link rút gọn bit.ly/abc nhé": [F.LIEN_KET],
            "liên hệ 0912 345 678 để mua": [F.SO_DIEN_THOAI],
            "ib cho mình nhé, add zalo để nhận quà": [F.MOI_LIEN_HE],
            "zalo: 0912345678": [F.SO_DIEN_THOAI, F.MOI_LIEN_HE],
            "chơi tài xỉu uy tín, nhà cái số 1": [F.CO_BAC_LUA_DAO],
            "kiem tien online moi ngay": [F.CO_BAC_LUA_DAO],
        }
        for s, ly_do in ca.items():
            self.assertEqual(F.ly_do_spam(s), ly_do, s)
            self.assertTrue(F.gan_co(s)["is_spam"], s)

    def test_khong_phai_spam(self):
        for s in ["mua ở tgdd.vn rẻ hơn", "pin trâu, camera đẹp", "zalo bị lag trên máy này", "camera tele chụp xa tốt",
                  "đẹp quáaaaaa 😍😍😍", "nice phone bro", "", "giá 30.990.000 đồng"]:
            co = F.gan_co(s)
            self.assertEqual((co["is_spam"], co["spam_reasons"]), (False, []), s)

    def test_hai_co_tach_rieng(self):
        co = F.gan_co("nice phone bro")
        self.assertEqual((co["is_vietnamese"], co["is_spam"]), (False, False))
        co = F.gan_co("liên hệ zalo 0912345678")
        self.assertEqual((co["is_vietnamese"], co["is_spam"]), (True, True))


if __name__ == "__main__":
    unittest.main()
