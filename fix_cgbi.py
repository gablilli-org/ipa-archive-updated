import glob
import pyipng
import os

DATA_DIR = './data'

def fix_iPNG(file_path):
    try:
        with open(file_path,'rb') as f:
            raw_bytes = f.read()
        fix_bytes = pyipng.convert(raw_bytes)
        with open(file_path,'wb') as f:
            f.write(fix_bytes)
            print(f'[FIXED] {file_path}')
    except ValueError:
        print(f'[SKIP] {file_path} doesn\'t need fixing')

for file in glob.glob(os.path.join(DATA_DIR, '*', '*.png')):
    fix_iPNG(file)
