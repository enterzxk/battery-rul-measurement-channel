# -*- coding: utf-8 -*-
"""E3a · Cache the ISU cells so the 18 replay processes do not each re-read 929 MB."""
import os
import pickle
import pandas as pd

import D_common as C

OUT = C.PROTO


def main():
    cells = C.load_isu()
    stress = C.load_stress()
    print("cells %d  stress conditions %d" % (len(cells), len(stress)))
    payload = dict(cells=cells, stress=stress)
    with open(os.path.join(OUT, "isu_cells_cache.pkl"), "wb") as f:
        pickle.dump(payload, f, protocol=4)
    print("wrote isu_cells_cache.pkl  (%.1f MB)" % (
        os.path.getsize(os.path.join(OUT, "isu_cells_cache.pkl")) / 1e6))


if __name__ == "__main__":
    main()
