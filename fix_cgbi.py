import glob
import os
from PIL import Image

DATA_DIR = './data'

def fix_iPNG(file_path):
    try:
        im = Image.open(file_path)

        im.save(file_path, format='PNG')
        print(f'[FIXED] {file_path}')

    except Exception as e:
        print(f'[ERROR] {file_path}: {e}')


if __name__ == "__main__":
    for file in glob.glob(os.path.join(DATA_DIR, '*', '*.png')):
        fix_iPNG(file)
