"""Chỉ cho PHÂN MỘT tiến trình ghi dữ liệu tại một thời điểm (khóa cấp hệ điều hành, tự nhả khi tiến trình chết).
Hai crawler cùng chạy là nguyên nhân gây 'database is locked' và ghi trùng comment."""
import os
from . import config

_HELD = []   # giữ tham chiếu để khóa không bị nhả sớm


def acquire(name="crawler"):
    path = config.DB_PATH.parent / f"{name}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a+b")
    if os.path.getsize(path) == 0:
        f.write(b"L")
        f.flush()
    try:
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.seek(1)
        pid = f.read().decode(errors="ignore").strip() or "?"
        raise SystemExit(f"Đã có một tiến trình khác đang ghi dữ liệu (PID {pid}). Tắt nó trước "
                         f"(Windows: Stop-Process -Id {pid}) rồi chạy lại. Chỉ được chạy MỘT crawler tại một thời điểm.")
    f.seek(1)
    f.truncate()
    f.write(str(os.getpid()).encode())
    f.flush()
    _HELD.append(f)
