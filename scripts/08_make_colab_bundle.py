"""Step 8: package code + processed 15-min data + a notebook for training on Google Colab.

Usage: python scripts/08_make_colab_bundle.py
Writes colab/regime_15min_bundle.zip and colab/08_train_15min_colab.ipynb
"""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from regime.config import ROOT

BUNDLE = "regime_15min_bundle.zip"
OUTPUTS = "tuned_15min_outputs.zip"


def notebook() -> dict:
    def md(text):
        return {"cell_type": "markdown", "metadata": {}, "source": text}

    def code(text):
        return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": text}

    cells = [
        md("# Step 8 — train the selected Transformer on 15-minute Nifty 50 bars\n\n"
           "1. **Runtime → Change runtime type → T4 GPU**, then Save.\n"
           "2. **Runtime → Run all.**\n"
           "3. When cell 3 shows an upload button, choose `regime_15min_bundle.zip`.\n"
           "4. If Google Drive asks for permission, allow it. Files are kept in Drive, so a disconnect does not lose "
           "finished seeds; just Run all again and it resumes.\n"
           "5. The last cell downloads `tuned_15min_outputs.zip`. Put it in the `redo` folder on your laptop.\n\n"
           "Expected time on a T4: roughly 20–40 minutes for 5 seeds."),
        code("# 1. Check the GPU is attached (should print a Tesla T4 or similar)\n!nvidia-smi -L"),
        code("# 2. Keep files on Google Drive so a disconnect does not lose finished seeds\n"
             "USE_DRIVE = True\n"
             "import os\n"
             "if USE_DRIVE:\n"
             "    from google.colab import drive\n"
             "    drive.mount('/content/drive')\n"
             "    WORK = '/content/drive/MyDrive/nifty_regime_redo'\n"
             "else:\n"
             "    WORK = '/content/nifty_regime_redo'\n"
             "os.makedirs(WORK, exist_ok=True)\n"
             "print('working directory:', WORK)"),
        code("# 3. Upload the bundle once (skipped if it is already unpacked)\n"
             "import zipfile\n"
             "from google.colab import files\n"
             "if not os.path.exists(os.path.join(WORK, 'scripts', '08_train_15min.py')):\n"
             f"    uploaded = files.upload()   # choose {BUNDLE}\n"
             "    name = next(iter(uploaded))\n"
             "    with zipfile.ZipFile(name) as z:\n"
             "        z.extractall(WORK)\n"
             "os.chdir(WORK)\n"
             "print(sorted(os.listdir(WORK)))"),
        code("# 4. Dependencies (torch, pandas, numpy, scikit-learn are preinstalled on Colab)\n"
             "!pip -q install pyyaml pyarrow"),
        code("# 5. Train 5 seeds on GPU (resumes finished seeds)\n"
             "!python scripts/08_train_15min.py --device cuda"),
        code("# 6. Download the trained weights and validation report\n"
             f"out = '{OUTPUTS}'\n"
             "with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:\n"
             "    for folder in ['models/tuned_15min']:\n"
             "        for f in sorted(os.listdir(folder)):\n"
             "            z.write(os.path.join(folder, f))\n"
             "    for f in ['reports/08_15min_validation.json', 'reports/08_15min_validation.md']:\n"
             "        z.write(f)\n"
             "print(open('reports/08_15min_validation.md').read())\n"
             "files.download(out)"),
    ]
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"accelerator": "GPU", "colab": {"provenance": []},
                         "kernelspec": {"name": "python3", "display_name": "Python 3"},
                         "language_info": {"name": "python"}}}


def main() -> None:
    selected = json.loads((ROOT / "reports" / "07_selection.json").read_text())["selected"]
    files = (
        [ROOT / "config" / "config.yaml", ROOT / "scripts" / "08_train_15min.py",
         ROOT / "reports" / "07_selection.json", ROOT / "reports" / f"06_tuning_daily_{selected}.json"]
        + sorted((ROOT / "src" / "regime").glob("*.py"))
        + [ROOT / "data" / "processed" / f for f in
           ["features_15min_full.parquet", "labels_15min_full.parquet", "scaler_15min.json"]]
    )
    out = ROOT / "colab"
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(out / BUNDLE, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ROOT).as_posix())
    (out / "08_train_15min_colab.ipynb").write_text(json.dumps(notebook(), indent=1), encoding="utf-8")
    size = (out / BUNDLE).stat().st_size / 1e6
    print(f"wrote {out / BUNDLE} ({size:.1f} MB, {len(files)} files) and {out / '08_train_15min_colab.ipynb'}")


if __name__ == "__main__":
    main()
