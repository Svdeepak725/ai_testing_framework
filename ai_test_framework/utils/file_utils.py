import datetime
import shutil
import uuid
from pathlib import Path


def generate_unique_locators_filename(output_dir: Path | str | None = None, prefix: str = "locators", ext: str = "json") -> Path:
    """Generate a unique filename in the output directory (defaults to package root).

    Returns a fully-qualified Path to write.
    """
    if output_dir is None:
        # default to package root (two levels up from this file)
        base = Path(__file__).resolve().parents[1]
    else:
        base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    runid = uuid.uuid4().hex[:6]
    filename = f"{prefix}_{ts}_{runid}.{ext}"
    return base / filename


def archive_file(src: Path | str, archive_dir: Path | str | None = None) -> Path:
    src = Path(src)
    if archive_dir is None:
        archive_dir = src.parent / "locators_archive"
    archive_dir = Path(archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / src.name
    shutil.move(str(src), str(dest))
    return dest


def purge_older_files(archive_dir: Path | str, days: int = 30) -> int:
    archive_dir = Path(archive_dir)
    if not archive_dir.exists():
        return 0
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    removed = 0
    for file in archive_dir.glob("locators_*.json"):
        mtime = datetime.datetime.utcfromtimestamp(file.stat().st_mtime)
        if mtime < cutoff:
            try:
                file.unlink()
                removed += 1
            except Exception:
                # ignore removal errors
                pass
    return removed
