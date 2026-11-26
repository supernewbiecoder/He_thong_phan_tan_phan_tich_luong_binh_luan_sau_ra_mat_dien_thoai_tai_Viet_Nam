"""Mục đích: Kiểm bộ nhãn chốt khớp contract v3, lấy mẫu A và xuất phiếu (src/labeling/sheet.py), kiểm và gộp phiếu (check_sheet.py), ước lượng mẫu A và đo luật (estimate.py), so luật với mô hình spam (src/models/spam/train.py); cập nhật lần cuối: 2026-11-26.

Chỉ dùng câu và dữ liệu tự soạn. Chạy: python -m pytest tests/test_labeling_sheet.py -q
"""

import json
import random

import pytest

from src.labeling import check_sheet as CS
from src.labeling import estimate as UL
from src.labeling import final_labels as FL
from src.labeling import sheet as SH
from src.labeling.sample import GOC, doc_csv

MA_MAY = {"s24u", "ip15prm", "s23u"}


# ---------------------------------------------------------------- bộ nhãn và contract

def test_contract_enums_match_the_finalized_label_set():
    schema = json.loads((GOC / "contracts" / "aspect-mention.schema.json").read_text(encoding="utf-8"))
    p = schema["properties"]
    assert p["schema_version"] == {"const": 3}
    assert p["aspect"]["enum"] == list(FL.DIM2_LABELS)
    assert p["sentiment"]["enum"] == list(FL.ATTITUDES)
    assert p["purposes"]["items"]["enum"] == list(FL.PURPOSES)
    assert [x for x in p["model_mention"]["enum"] if x] == list(FL.MODEL_MENTION)
    assert p["defect_type"] == {"type": "null", "description": p["defect_type"]["description"]}
    assert len(FL.ASPECTS) == 11 and "nhiet_do" not in FL.DIM2_LABELS and "am_thanh" not in FL.DIM2_LABELS
    for old in ("BATTERY", "DISPLAY", "PERFORMANCE", "WARRANTY", "pos", "neg"):
        assert old not in json.dumps(p["aspect"]) + json.dumps(p["sentiment"])


# ---------------------------------------------------------------- lấy mẫu, phiếu

def binh_luan(i, spam=False, viet=True, video=None, text=None):
    return {"comment_id": f"c{i:04d}", "video_id": video or f"v{i % 40:02d}", "model": "s24u", "parent_id": None,
            "parent_text": None, "text_clean": text or f"bình luận số {i} @Nguyen Van A pin trâu",
            "is_spam": spam, "is_vietnamese": viet, "spam_reasons": ["lien_ket"] if spam else [],
            "pipeline_version": "processing-2.0"}


@pytest.fixture()
def du_lieu(tmp_path):
    rng = random.Random(1)
    dong = [binh_luan(i, spam=i < 300, viet=not (300 <= i < 360)) for i in range(2000)]
    dong.append({**binh_luan(9999), "text_clean": "  "})   # rỗng: ngoài khung
    rng.shuffle(dong)
    vao = tmp_path / "comments.jsonl"
    vao.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in dong), encoding="utf-8")
    return vao


def test_sample_a_strata_weights_and_assignment(du_lieu, tmp_path):
    man = SH.chay(du_lieu, tmp_path / "labels", nguoi=[f"n{i:02d}" for i in range(1, 12)])
    assert man["nguon"]["so_binh_luan_rong"] == 1
    assert man["tang"] == {"A1": {"N_h": 300, "n_h": 150}, "A2": {"N_h": 60, "n_h": 60},
                           "A3": {"N_h": 1640, "n_h": 600}}   # A2 ít hơn cỡ mẫu: lấy hết
    mau = UL.doc_jsonl(tmp_path / "labels" / "mau_a.jsonl")
    assert len(mau) == 810 and len({m["comment_id"] for m in mau}) == 810
    hc = [m for m in mau if m["hieu_chinh"]]
    assert len(hc) == 50 and not any(m["nguoi_gan"] for m in hc)
    doi = [m for m in mau if m["gan_doi"]]
    assert len(doi) == pytest.approx(200, abs=2)
    assert all(len(set(m["nguoi_gan"])) == 2 for m in doi)
    assert all(len(m["nguoi_gan"]) == 1 for m in mau if not m["gan_doi"] and not m["hieu_chinh"])
    tai = [sum(n in m["nguoi_gan"] for m in mau) for n in man["nguoi_gan"]]
    assert max(tai) - min(tai) <= 1                                       # chia đều
    # chạy lại ra đúng mẫu đó (seed cố định)
    SH.chay(du_lieu, tmp_path / "lai", nguoi=man["nguoi_gan"])
    assert UL.doc_jsonl(tmp_path / "lai" / "mau_a.jsonl") == mau


def test_sheets_hide_strata_mask_names_and_carry_dropdowns(du_lieu, tmp_path):
    from openpyxl import load_workbook

    SH.chay(du_lieu, tmp_path / "labels", nguoi=["an", "binh"])
    phieu = tmp_path / "labels" / "phieu"
    dong = doc_csv(phieu / "mau_a_an.csv")
    assert list(dong[0]) == list(SH.COT_PHIEU)
    assert not {"tang", "trong_so", "is_spam", "author_hash", "author_name"} & set(dong[0])
    assert all("Nguyen" not in d["binh_luan"] and "@[người dùng]" in d["binh_luan"] for d in dong)
    assert {d["nguoi_gan"] for d in dong} == {"an"}
    wb = load_workbook(phieu / "mau_a_an.xlsx")
    assert wb.sheetnames == ["phieu", "danh_sach_nhan", "danh_muc_may"]
    ds = wb["phieu"].data_validations.dataValidation
    assert any('"D,N,B,L,X"' == v.formula1 for v in ds)
    assert any("danh_muc_may!" in v.formula1 and not v.showErrorMessage for v in ds)   # ten_may: gợi ý, không chặn
    nhan = doc_csv(phieu / "danh_sach_nhan.csv")
    assert {"pin_sac", "may_chung", "quang_cao", "tich_cuc"} <= {d["nhan"] for d in nhan}


def test_sheets_are_not_overwritten_once_someone_has_filled_them(du_lieu, tmp_path):
    SH.chay(du_lieu, tmp_path / "labels", nguoi=["an", "binh"])
    p = tmp_path / "labels" / "phieu" / "mau_a_an.csv"
    dong = doc_csv(p)
    dong[0]["lien_quan"] = "D"
    SH._ghi_csv(p, SH.COT_PHIEU, dong)
    with pytest.raises(SystemExit, match="đã có người điền"):
        SH.chay(du_lieu, tmp_path / "labels", nguoi=["an", "binh"])


# ---------------------------------------------------------------- đọc, kiểm phiếu

def phieu(**k):
    d = {"stt": "1", "comment_id": "c1", "nguoi_gan": "an", "tieng_viet": "co", "lien_quan": "D",
         "noi_ve_thai_do": "cam+", "muc_dich": "dg", "da_dung": "k", "may_nhac": "k", "ten_may": "",
         "chua_chac": "", "ghi_chu": ""}
    return {**d, **k}


def test_reads_abbreviations_full_names_models_and_comparisons():
    x, _ = CS.doc_dong(phieu(noi_ve_thai_do="cam+-, gia0", muc_dich="dg, hoi"), MA_MAY)
    assert x["noi_ve"] == [{"aspect": "camera", "thai_do": ["tich_cuc", "tieu_cuc"], "may": None, "so_voi": None,
                            "ben_hon": None},
                           {"aspect": "gia", "thai_do": ["khong_danh_gia"], "may": None, "so_voi": None, "ben_hon": None}]
    assert x["muc_dich"] == ["danh_gia", "hoi"] and x["tieng_viet"] is True
    x, _ = CS.doc_dong(phieu(noi_ve_thai_do="pin=@s24u>ip15prm, cam+@s24u", may_nhac="t", ten_may="s24u; ip15prm"),
                       MA_MAY)
    assert x["noi_ve"][0] == {"aspect": "pin_sac", "thai_do": ["so_sanh"], "may": "s24u", "so_voi": "ip15prm",
                              "ben_hon": "s24u"}
    x, _ = CS.doc_dong(phieu(noi_ve_thai_do="camera:tich_cuc", lien_quan="dien_thoai", muc_dich="danh_gia"), MA_MAY)
    assert x["noi_ve"][0]["aspect"] == "camera"


@pytest.mark.parametrize("sua, loi", [
    ({"tieng_viet": ""}, "tieng_viet"),
    ({"lien_quan": "N"}, "khác D thì để trống"),
    ({"noi_ve_thai_do": ""}, "phải có noi_ve_thai_do"),
    ({"noi_ve_thai_do": "cam"}, "không đọc được"),
    ({"noi_ve_thai_do": "nd+"}, "không phải nhãn chiều 2"),          # nhiet_do đã gộp vào hieu_nang
    ({"muc_dich": ""}, "muc_dich không được trống"),
    ({"may_nhac": "t"}, "phải ghi ten_may"),
    ({"ten_may": "s24u"}, "khác t thì để trống"),
    ({"noi_ve_thai_do": "cam+@s24u", "may_nhac": "t", "ten_may": "ip15prm"}, "phải có trong ten_may"),
    ({"noi_ve_thai_do": "cam+, pin-", "may_nhac": "t", "ten_may": "s24u;ip15prm"}, "phải ghi @mã máy"),
    ({"noi_ve_thai_do": "pin+@s24u>ip15prm", "may_nhac": "t", "ten_may": "s24u;ip15prm"}, "không phải so sánh"),
])
def test_self_check_rules_of_the_guideline(sua, loi):
    with pytest.raises(CS.LoiPhieu, match=loi):
        CS.doc_dong(phieu(**sua), MA_MAY)


def test_warnings_do_not_block():
    _, cb = CS.doc_dong(phieu(muc_dich="bl", may_nhac="t", ten_may="iphone 99", noi_ve_thai_do="pin-"), MA_MAY)
    assert any("không có trong danh mục" in c for c in cb) and any("bao_loi" in c for c in cb)


# ---------------------------------------------------------------- gộp, phân xử, ước lượng

def dien(p, theo_id):
    dong = doc_csv(p)
    for d in dong:
        d.update(theo_id(d))
    SH._ghi_csv(p, SH.COT_PHIEU, dong)


def nhan_that(i_so):
    """Nhãn 'thật' tự đặt: bình luận số chia hết cho 7 là spam, 300–359 là ngoại ngữ."""
    spam = i_so % 7 == 0
    return {"tieng_viet": "khong" if 300 <= i_so < 360 else "co", "lien_quan": "N" if spam else "D",
            "noi_ve_thai_do": "" if spam else "pin+", "muc_dich": "qc" if spam else "dg", "da_dung": "k",
            "may_nhac": "k", "ten_may": ""}


def test_merge_agreements_disagreements_and_adjudication(du_lieu, tmp_path, monkeypatch):
    ra = tmp_path / "labels"
    SH.chay(du_lieu, ra, nguoi=["an", "binh", "chi"])
    phieu_dir = ra / "phieu"
    for p in phieu_dir.glob("mau_a_*.csv"):
        ten = p.stem.split("_")[-1]

        def gan(d, ten=ten):
            x = nhan_that(int(d["comment_id"][1:]))
            if ten == "chi" and int(d["stt"]) % 5 == 0:
                x["muc_dich"] = "dg, hoi"                       # chi lệch ở một số dòng
            return x
        dien(p, gan)
        p.with_suffix(".xlsx").unlink()                         # chỉ còn CSV đã điền
    dien(phieu_dir / "hieu_chinh_50.csv", lambda d: {**nhan_that(int(d["comment_id"][1:])), "nguoi_gan": "ca_nhom"})
    (phieu_dir / "hieu_chinh_50.xlsx").unlink()
    danh_muc = tmp_path / "pipeline.yaml"
    danh_muc.write_text("models:\n  - name: s24u\n    title: Samsung Galaxy S24 Ultra\n    launch_date: '2024-01-31'\n",
                        encoding="utf-8")
    kq = CS.gop(phieu_dir, ra, danh_muc)
    assert kq["so_ca_lech_chua_phan_xu"] > 0
    assert kq["so_nhan_chuan"] + kq["so_ca_lech_chua_phan_xu"] == kq["so_binh_luan_co_nhan"] == 810
    so_px = doc_csv(ra / "so_phan_xu.csv")
    for d in so_px:                                              # người thứ ba quyết
        d.update({f"px_{k}": v for k, v in nhan_that(int(d["comment_id"][1:])).items()}, px_nguoi_phan_xu="dung")
    SH._ghi_csv(ra / "so_phan_xu.csv", CS.COT_PX, so_px)
    kq = CS.gop(phieu_dir, ra, danh_muc)
    assert kq["so_ca_lech_chua_phan_xu"] == 0 and kq["so_nhan_chuan"] == 810
    assert kq["dong_thuan"]["lien_quan"]["dong_y_tho"] == 1.0
    nhan = UL.doc_jsonl(ra / "nhan_binh_luan.jsonl")
    assert all(x["label_source"] == "human" for x in nhan) and any(x["phan_xu"] for x in nhan)

    kq = UL.uoc_luong(UL.doc_jsonl(ra / "mau_a.jsonl"), nhan)
    that_spam = sum(1 for i in range(2000) if i % 7 == 0) / 2000
    assert kq["ty_le"]["spam"]["ktc95"][0] <= that_spam <= kq["ty_le"]["spam"]["ktc95"][1]
    assert kq["ty_le"]["khong_phai_tieng_viet"]["uoc_luong"] == pytest.approx(60 / 2000)
    luat = kq["luat_spam"]["quy_ve_ca_du_lieu"]
    # luật gắn 300 bình luận đầu; spam thật là số chia hết cho 7 => precision ≈ 43/300
    assert luat["precision"] == pytest.approx(sum(1 for i in range(300) if i % 7 == 0) / 300, abs=0.05)
    assert kq["luat_tieng_viet"]["quy_ve_ca_du_lieu"]["precision"] == 1.0


def test_spam_model_refuses_to_train_without_enough_human_spam(tmp_path, monkeypatch):
    from src.models.spam import train as TR

    monkeypatch.setattr(TR, "RA", tmp_path)
    (tmp_path / "mau_a.jsonl").write_text(json.dumps({"stt": 1, "comment_id": "c1", "video_id": "v1", "tang": "A3",
                                                      "N_h": 10, "is_spam": False, "is_vietnamese": True}) + "\n",
                                          encoding="utf-8")
    (tmp_path / "nhan_binh_luan.jsonl").write_text(json.dumps({"comment_id": "c1", "tieng_viet": True, "lien_quan": "D",
                                                               "noi_ve": [], "muc_dich": ["dg"]}) + "\n",
                                                   encoding="utf-8")
    monkeypatch.setattr(TR, "doc_jsonl", lambda p: UL.doc_jsonl(tmp_path / p.name))
    vao = tmp_path / "comments.jsonl"
    vao.write_text(json.dumps(binh_luan(1) | {"comment_id": "c1"}) + "\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="Chưa huấn luyện"):
        TR.chay(vao)
