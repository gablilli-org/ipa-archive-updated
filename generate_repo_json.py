#!/usr/bin/env python3
import json
import plistlib
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

CACHE_DIR = Path(__file__).parent / 'data'

DEFAULT_BASE_URL = 'https://raw.githubusercontent.com/gablilli-org/ipa-archive-updated/refs/heads/main'

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
    try:
        with open(plist_path, 'rb') as fp:
            data = plistlib.load(fp)
        return {k: str(data[k]) for k in PRIVACY_KEYS if k in data}
    except (OSError, plistlib.InvalidFileException, KeyError, ValueError):
        return {}

def get_real_size(pk: int, default_size: int) -> int:
    """Return the IPA size from the plist if present, else default."""
    plist_path = CACHE_DIR / str(pk // 1000) / f'{pk}.plist'
    if plist_path.exists():
        try:
            with open(plist_path, 'rb') as f:
                info = plistlib.load(f)
                return int(info.get('FileSize', default_size))
        except Exception:
            return default_size
    return default_size

def build_app_entry(entry: list, url_map: dict, base_url: str) -> dict:
    pk, platform, min_os, title, bundle_id, version, base_url_id, path_name, size = entry
    base = url_map.get(str(base_url_id), '')
    download_url = f'{base}/{path_name}' if base else path_name
    icon_url = f'{base_url}/data/{pk // 1000}/{pk}.jpg'
    real_size = get_real_size(pk, size or 0)

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
        'size': real_size,
    }

def generate_repo(base_url: str, output_path: Path) -> None:
    ipa_json = CACHE_DIR / 'ipa.json'
    urls_json = CACHE_DIR / 'urls.json'

    if not ipa_json.exists() or not urls_json.exists():
        print('Error: Missing data/ipa.json or data/urls.json', file=sys.stderr)
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

        plist_path = CACHE_DIR / str(pk // 1000) / f'{pk}.plist'
        if plist_path.exists():
            privacy = load_privacy_from_plist(plist_path)
            if privacy and bundle_id:
                perm = permissions.setdefault(bundle_id, {'entitlements': [], 'privacy': {}})
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
    print(f'Done: {len(apps)} apps, {len(permissions)} permission entries, {size_mb:.1f} MB')

def main() -> None:
    parser = ArgumentParser(description='Generate a repo.json in IPA repo JSON format.')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL, metavar='URL', help='Base URL for hosted assets')
    parser.add_argument('--output', default=str(Path(__file__).parent / 'repo.json'), metavar='FILE', help='Output file path')
    args = parser.parse_args()
    generate_repo(args.base_url.rstrip('/'), Path(args.output))

if __name__ == '__main__':
    main()
