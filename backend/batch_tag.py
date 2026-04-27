#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path
import sys
from PIL import Image
from tqdm import tqdm
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from parser import parse
from analyzer import rule_analyze
from database import insert_song, _connect


def extract_title(maidata_path: Path) -> str:
    with open(maidata_path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if line.startswith('&title='):
                return line[7:].strip()
    return maidata_path.parent.name


def iter_song_dirs(charts_dir: Path):
    """Yield every song directory (the folder containing maidata.txt).

    Handles both flat and one-level-nested layouts:
      flat:   charts_dir/SongName/maidata.txt
      nested: charts_dir/VersionFolder/SongName/maidata.txt
    """
    for entry in sorted(charts_dir.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / 'maidata.txt').exists():
            yield entry
        else:
            for sub in sorted(entry.iterdir()):
                if sub.is_dir() and (sub / 'maidata.txt').exists():
                    yield sub


def main():
    parser_cli = argparse.ArgumentParser(description='Batch-tag maimai charts and populate db.sqlite')
    parser_cli.add_argument('--charts-dir', required=True, help='Path to folder of chart subdirectories')
    parser_cli.add_argument('--clear', action='store_true', help='Clear existing songs before ingesting')
    args = parser_cli.parse_args()

    charts_dir = Path(args.charts_dir)
    if not charts_dir.is_dir():
        print(f"Error: --charts-dir '{charts_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    covers_dir = Path(__file__).parent / 'static' / 'covers'
    covers_dir.mkdir(parents=True, exist_ok=True)

    if args.clear:
        conn = _connect()
        conn.execute("DELETE FROM songs")
        conn.commit()
        conn.close()
        print("Cleared existing songs.")

    song_dirs = list(iter_song_dirs(charts_dir))
    ok_count = 0
    skip_count = 0

    bar = tqdm(song_dirs, unit="song", ncols=80)
    for song_dir in bar:
        # Skip 宴会铺面 — folder names start with [kanji]
        if song_dir.name.startswith('['):
            skip_count += 1
            bar.set_postfix(ok=ok_count, skip=skip_count)
            continue

        maidata = song_dir / 'maidata.txt'

        try:
            features = parse(str(maidata))
            result = rule_analyze(features)
            tags = result.get('tags', ['Balanced'])
            difficulty = result.get('difficulty')
            name = extract_title(maidata)

            bg_image_url = None
            bg_src = next(
                (song_dir / f for f in ('bg.jpg', 'bg.png', 'BG.jpg', 'BG.png')
                 if (song_dir / f).exists()),
                None,
            )
            if bg_src is not None:
                song_id = f"{ok_count + 1:04d}"
                dest = covers_dir / f"{song_id}.jpg"
                try:
                    with Image.open(bg_src) as im:
                        im = im.convert("RGB")
                        im.thumbnail((256, 256), Image.LANCZOS)
                        im.save(dest, "JPEG", quality=75, optimize=True)
                except Exception:
                    shutil.copy2(bg_src, dest)
                bg_image_url = f"/static/covers/{song_id}.jpg"

            insert_song(name, tags, difficulty, None, bg_image_url)
            ok_count += 1
            bar.set_postfix(ok=ok_count, skip=skip_count, song=name[:20])

        except Exception as e:
            tqdm.write(f"[SKIP] {song_dir.name} — {e}")
            skip_count += 1
            bar.set_postfix(ok=ok_count, skip=skip_count)

    print(f"\nDone: {ok_count} songs ingested, {skip_count} skipped.")


if __name__ == '__main__':
    main()
