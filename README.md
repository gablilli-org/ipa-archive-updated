# the grand ipa archive - in json

forked from [stuffed18's ipa-archive-updated](https://github.com/stuffed18/ipa-archive-updated) and converted to altstore/sidestore/feather (not tested) format. some images are missing due to png metadata issues during windows conversion to jpg. an update is coming to restore around 30% of the missing images, though the browser may not display all pngs correctly.

**no apps are hosted on this site.**

this project provides a searchable and filterable index for .ipa files. all linked files belong to their respective owners, and i have no involvement with the referenced projects beyond maintaining this fork and index. the ipa files are indexed from various [archive.org](https://archive.org) collections, which can be found in [data/urls.json](data/urls.json).

## development

### requirements

- `ipa_archive.py` requires [remotezip](https://github.com/gtsystem/python-remotezip) (`pip install remotezip`)
- `image_optim.sh` uses [imageoptim](https://github.com/ImageOptim/ImageOptim) (requires mac)
- `convert_plist.sh` uses plistbuddy (likely requires mac)


### database schema

the `done` column is encoded as follows:
- `0` - queued, needs processing
- `1` - done
- `3` - error, possibly fixable, needs attention
- `4` - error, unfixable, ignore in export


### general workflow

to add files to the archive, follow these steps:

1. `python3 ipa_archive.py add URL`
2. `python3 ipa_archive.py run`
3. if any urls failed, check if they can be fixed (most broken ipa-zip files cannot):
    - if fixable: `python3 ipa_archive.py err reset` (sets all errors to done=0 and reprints errors)
    - if unfixable: `python3 ipa_archive.py set err ID1 ID2` (marks ids as done=4)
4. `./tools/image_optim.sh` (converts all .png files to .jpg)
5. `python3 ipa_archive.py export json`


to update the archive:
- `python3 ipa_archive.py update` (checks all links if not recently updated)
- `python3 ipa_archive.py update [url|base_url_id]` (forces update)
- then run the same steps as after adding a url


### useful helpers

- `./tools/check_error_no_plist.sh` - verifies no plist exists for done=4 entries
- `./tools/check_missing_img.sh` - verifies each .plist has a corresponding .jpg
- `./tools/convert_plist.sh 21968` - converts json-like format to xml
- `./ipa_archive.py get url 21968` - prints url of entry
- `./ipa_archive.py get img 21968` - forces re-download of .png image
- `./ipa_archive.py get ipa 21968` - downloads ipa file for debugging
