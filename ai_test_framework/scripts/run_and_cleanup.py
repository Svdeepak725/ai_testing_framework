"""
Runner script to run test_demo with a unique locators filename and optionally archive or delete after run.
"""
import os
import uuid
import datetime
import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT
ARCHIVE_DIR = ROOT / 'locators_archive'


def generate_unique_filename(prefix='locators', ext='json'):
    ts = datetime.datetime.now(datetime.UTC).strftime('%Y%m%d_%H%M%S')
    runid = uuid.uuid4().hex[:6]
    return f"{prefix}_{ts}_{runid}.{ext}"


def run_test(script='test/test_demo.py', locators_output=None, email=None, password=None, expect='negative'):
    cmd = [sys.executable, script]
    if locators_output:
        cmd += ['--locators-output', str(locators_output)]
    cmd += ['--no-archive']
    if email:
        cmd += ['--email', email]
    if password:
        cmd += ['--password', password]
    if expect:
        cmd += ['--expect', expect]
    print('Running test:', ' '.join(cmd))
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode


def archive_file(src: Path, archive_dir: Path=ARCHIVE_DIR):
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / src.name
    shutil.move(str(src), str(dest))
    print('Archived', src, '->', dest)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run test_demo and archive locators output')
    parser.add_argument('--email', dest='email', default=None, help='Email to use for the login test')
    parser.add_argument('--password', dest='password', default=None, help='Password to use for the login test')
    parser.add_argument('--expect', dest='expect', choices=['positive', 'negative'], default='negative', help='Expected outcome for the login test')
    args = parser.parse_args()

    # Create a unique locators filename
    unique_file = DEFAULT_OUTPUT_DIR / generate_unique_filename()

    # Run test with this file
    rc = run_test(
        locators_output=str(unique_file),
        email=args.email,
        password=args.password,
        expect=args.expect,
    )

    # Clean up or archive
    if unique_file.exists():
        # Archive by default (safer)
        archive_file(unique_file)
    else:
        print('No locators file found to archive.')

    if rc != 0:
        print('Test run failed with exit code', rc)
    else:
        print('Test run completed; locators archived.')

    sys.exit(rc)
