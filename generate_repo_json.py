#!/usr/bin/env python3
"""Generate an IPA repo JSON from the existing archive data.

Usage:
    python3 generate_repo_json.py [--base-url URL] [--output FILE]

The generated repo.json follows the IPA repo JSON format compatible with
iOS app distribution tools.
"""

import json
import plistlib
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

CACHE_DIR = Path(__file__).parent / 'data'

# Default base URL for hosted assets (icon images)
DEFAULT_BASE_URL = 'https://gablilli-org.github.io/ipa-archive-updated'

# NS* privacy usage description keys found in Info.plist files
PRIVACY_KEYS = [
    'NSAppleEventsUsageDescription',
    'NSBluetoothAlwaysUsageDescription',
    'NSBluetoothPeripheralUsageDescription',
    'NSCalendarsUsageDescription',
    'NSCameraUsageDescription',
    'NSContactsUsageDescription',
    'NSFaceIDUsageDescription',
    'NSHealthShareUsageDescription',
    'NSHealthUpdateUsageDescription',
    'NSHomeKitUsageDescription',
    'NSLocationAlwaysAndWhenInUseUsageDescription',
    'NSLocationAlwaysUsageDescription',
    'NSLocationUsageDescription',
    'NSLocationWhenInUseUsageDescription',
    'NSMicrophoneUsageDescription',
    'NSMotionUsageDescription',
    'NSPhotoLibraryAddUsageDescription',
    'NSPhotoLibraryUsageDescription',
    'NSRemindersUsageDescription',
    'NSSpeechRecognitionUsageDescription',
    'NSUserTrackingUsageDescription',
]


def load_privacy_from_plist(plist_path: Path) -> dict:
    """Extract NS* privacy usage descriptions from an Info.plist file."""
    try:
        with open(plist_path, 'rb') as fp:
            data = plistlib.load(fp)
        return {k: str(data[k]) for k in PRIVACY_KEYS if k in data}
    except (OSError, plistlib.InvalidFileException, KeyError, ValueError):
        return {}


def build_app_entry(entry: list, url_map: dict, base_url: str) -> dict:
    """Build a single app entry in IPA repo JSON format from a raw DB row.

    Entry format: [pk, platform, minOS, title, bundleId, version,
                   baseUrlId, pathName, size]
    """
    pk, platform, min_os, title, bundle_id, version, base_url_id, path_name, size = entry

    base = url_map.get(str(base_url_id), '')
    download_url = f'{base}/{path_name}' if base else path_name
    icon_url = f'{base_url}/data/{pk // 1000}/{pk}.jpg'

    return {
        'name': title or '',
        'developerName': '',
        'bundleID': bundle_id or '',
        'caption': '',
        'description': '',
        'downloadURL': download_url,
        'iconURL': icon_url,
        'version': version or '',
        'date': '',
        'size': size or 0,
    }


def generate_repo(base_url: str, output_path: Path) -> None:
    """Read existing archive data and write a repo.json file."""
    ipa_json = CACHE_DIR / 'ipa.json'
    urls_json = CACHE_DIR / 'urls.json'

    if not ipa_json.exists():
        print(f'Error: {ipa_json} not found', file=sys.stderr)
        sys.exit(1)
    if not urls_json.exists():
        print(f'Error: {urls_json} not found', file=sys.stderr)
        sys.exit(1)

    print('Loading data/ipa.json ...')
    with open(ipa_json) as fp:
        ipa_data = json.load(fp)

    print('Loading data/urls.json ...')
    with open(urls_json) as fp:
        url_map = json.load(fp)

    apps = []
    permissions = {}
    total = len(ipa_data)

    print(f'Processing {total} entries ...')
    for i, entry in enumerate(ipa_data):
        if i % 5000 == 0:
            print(f'\r  [{i}/{total}]', end='', flush=True)

        pk = entry[0]
        bundle_id = entry[4]

        app = build_app_entry(entry, url_map, base_url)
        apps.append(app)

        # Extract privacy descriptions from the cached Info.plist
        plist_path = CACHE_DIR / str(pk // 1000) / f'{pk}.plist'
        if plist_path.exists():
            privacy = load_privacy_from_plist(plist_path)
            if privacy and bundle_id:
                perm = permissions.setdefault(bundle_id, {
                    'entitlements': [],
                    'privacy': {},
                })
                perm['privacy'].update(privacy)

    print(f'\r  done.{" " * 20}')

    repo = {
        'name': 'IPA Archive',
        'identifier': 'org.gablilli.ipa-archive',
        'iconURL': f'{base_url}/apple-touch-icon.png',
        'caption': 'A searchable archive of iOS IPA files from archive.org',
        'description': (
            'A searchable and filterable index for .ipa files. '
            'None of the linked files are hosted here; they are all sourced '
            'from Archive.org collections.'
        ),
        'apps': apps,
        'permissions': permissions,
    }

    print(f'Writing {output_path} ...')
    with open(output_path, 'w') as fp:
        json.dump(repo, fp, separators=(',', ':'), ensure_ascii=False)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(
        f'Done: {len(apps)} apps, {len(permissions)} permission entries, '
        f'{size_mb:.1f} MB'
    )


def main() -> None:
    parser = ArgumentParser(
        description='Generate a repo.json in IPA repo JSON format from the archive data.',
    )
    parser.add_argument(
        '--base-url',
        default=DEFAULT_BASE_URL,
        metavar='URL',
        help=(
            f'Base URL for hosted assets such as app icons '
            f'(default: {DEFAULT_BASE_URL})'
        ),
    )
    parser.add_argument(
        '--output',
        default=str(Path(__file__).parent / 'repo.json'),
        metavar='FILE',
        help='Output file path (default: repo.json)',
    )
    args = parser.parse_args()
    generate_repo(args.base_url.rstrip('/'), Path(args.output))


if __name__ == '__main__':
    main()
