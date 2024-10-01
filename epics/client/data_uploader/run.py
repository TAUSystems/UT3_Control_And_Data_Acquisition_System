from __future__ import annotations

from data_uploader import DataUploader

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s", force=True)

def main():
    da = DataUploader()
    da.main()

if __name__ == "__main__":
    main()
