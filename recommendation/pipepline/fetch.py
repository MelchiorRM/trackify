import os
import zipfile
import tarfile
import requests
from pathlib import Path
from tqdm import tqdm
from loguru import logger

#Paths
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MOVIES_DIR = RAW / "movies"
BOOKS_DIR = RAW / "books"
MUSIC_DIR = RAW / "music"

#Urls
DATASETS = {
    "movies": {
        "url": "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip",
        "dest": MOVIES_DIR / "ml-latest-small.zip",
        "extract_to": MOVIES_DIR
    },
    "books": {
        "files": {
            "books.csv": "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/books.csv",
            "ratings.csv": "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/ratings.csv",
            "book_tags.csv": "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/book_tags.csv",
            "tags.csv": "https://raw.githubusercontent.com/zygmuntz/goodbooks-10k/master/tags.csv"
        },
        "dest": BOOKS_DIR
    },
    "music": {
        "url": "https://mtg.upf.edu/static/datasets/lastfm/lastfm-dataset-360K.tar.gz",
        "dest": MUSIC_DIR / "lastfm-dataset-360K.tar.gz",
        "extract_to": MUSIC_DIR,
    },
}

#Helpers
def download_file(url: str, dest: Path, desc:str = "")-> bool:
    """Stream download a file from a URL to a destination path with a progress bar."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        logger.info(f"File already exists: {dest}. Skipping download.")
        return True
    try:
        logger.info(f"Downloading {desc} from {url} to {dest}")
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        with open(dest, "wb") as file, tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                bar.update(len(chunk))
        logger.success(f"Saved {desc} to {dest}")
        return True
    except Exception as e:
        logger.error(f"Error occurred while downloading {desc}: {e}")
        return False

def extract_zip(archive: Path, dest: Path) -> None:
    """Extract a zip archive to a destination."""
    logger.info(f"Extracting {archive.name} to {dest}")
    with zipfile.ZipFile(archive, 'r') as zip_ref:
        zip_ref.extractall(dest)
    logger.success(f"Extracted {archive.name} to {dest}")

def extract_tar(archive: Path, dest: Path) -> None:
    """Extract a tar archive to a destination."""
    logger.info(f"Extracting {archive.name} to {dest}")
    with tarfile.open(archive, 'r:gz') as tar_ref:
        tar_ref.extractall(dest)
    logger.success(f"Extracted {archive.name} to {dest}")

#domain fetchers
def fetch_movies() -> None:
    logger.info("Fetching movies dataset...")
    cfg = DATASETS["movies"]
    dest = cfg["dest"]
    if download_file(cfg["url"], dest, "Movies Dataset"):
        extract_zip(dest, cfg["extract_to"])

def fetch_books() -> None:
    logger.info("Fetching books dataset...")
    cfg = DATASETS["books"]
    cfg["dest"].mkdir(parents=True, exist_ok=True)
    for filename, url in cfg["files"].items():
        download_file(url, cfg["dest"] / filename, filename)

def fetch_music() -> None:
    logger.info("── MUSIC (Last.fm 360K) ──")
    cfg  = DATASETS["music"]
    dest = cfg["dest"]
    downloaded = download_file(cfg["url"], dest, "Last.fm 360K")
    extracted = False
    if downloaded and dest.exists() and dest.stat().st_size > 1_000:
        try:
            extract_tar(dest, cfg["extract_to"])
            extracted = True
        except tarfile.ReadError as e:
            logger.error(f"Downloaded file is not a valid tar.gz archive: {e}")
            dest.unlink(missing_ok=True)
    if not extracted:
        logger.warning(
            "Last.fm 360K could not be auto-downloaded (host restricted).\n"
            "Manual steps:\n"
            "  1. Visit http://ocelma.net/MusicRecommendationDataset/lastfm-360K.html\n"
            "  2. Download lastfm-dataset-360K.tar.gz\n"
            f"  3. Place it in {MUSIC_DIR}\n"
            "  4. Re-run this script — extraction will happen automatically."
        )

#verify downloads
def verify() -> None:
    expected = {
        "Movies": [
            MOVIES_DIR / "ml-latest-small" / "movies.csv",
            MOVIES_DIR / "ml-latest-small" / "ratings.csv",
            MOVIES_DIR / "ml-latest-small" / "tags.csv",
            MOVIES_DIR / "ml-latest-small" / "links.csv",
        ],
        "Books": [
            BOOKS_DIR / "books.csv",
            BOOKS_DIR / "ratings.csv",
            BOOKS_DIR / "book_tags.csv",
            BOOKS_DIR / "tags.csv",
        ],
        "Music": [
            MUSIC_DIR / "lastfm-dataset-360K" / "usersha1-artmbid-artname-plays.tsv",
        ],
    }
    print("\n── VERIFYING DATASETS ──")
    all_ok = True
    for domain, files in expected.items():
        for f in files:
            status = "✓" if f.exists() else "✗ MISSING"
            if not f.exists():
                all_ok = False
            print(f"  [{status}] {domain}: {f.name}")
    print()
    if all_ok:
        logger.success("All datasets ready.")
    else:
        logger.warning("Some files are missing — check the output above.")

#entry
if __name__ == "__main__":
    fetch_movies()
    fetch_books()
    fetch_music()
    verify()