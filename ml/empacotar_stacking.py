# -*- coding: utf-8 -*-
"""
empacotar_stacking.py — converte os modelos do desafio de ML (FakeRecogna 2.0 + Fake.br) no
pacote unico que o backend carrega (backend/models/stacking.joblib).

Os modelos de origem sao os salvos por `modelos/avaliar_externo.py --salvar --treino-externo 0.5`
no repositorio do desafio de ML: uma pasta com baseline/svm/nb/char/gbm.joblib e stacking_meta.joblib.

Uso:
    python ml/empacotar_stacking.py --origem /caminho/modelos_salvos/FakeRecogna2_extrativa_casada_com_fakebr

IMPORTANTE: rode com o MESMO Python e scikit-learn do backend (ver backend/Dockerfile e
backend/requirements.txt); o StackingClassifier recusa carregar se as versoes divergirem.
"""
import argparse
import sys
from pathlib import Path

import joblib
import sklearn

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_PATH = REPO_ROOT / "backend" / "models" / "stacking.joblib"
BASE_MODELS = ["baseline", "svm", "nb", "char", "gbm"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origem", required=True, help="pasta com os .joblib do desafio de ML")
    ap.add_argument("--saida", default=str(DEFAULT_OUT_PATH))
    a = ap.parse_args()

    origem = Path(a.origem)
    meta = joblib.load(origem / "stacking_meta.joblib")
    if list(meta["ordem"]) != BASE_MODELS:
        sys.exit(f"Ordem dos modelos inesperada: {meta['ordem']} (esperado {BASE_MODELS})")
    pacote = {
        "version": 1,
        "input": "noticia",
        "input_preprocessing": "lowercase; remove none; collapse whitespace; full text",
        "base_models": list(meta["ordem"]),
        "models": {n: joblib.load(origem / f"{n}.joblib") for n in meta["ordem"]},
        "meta_model": meta["meta"],
        "sklearn_version": sklearn.__version__,
        "python_version": sys.version.split()[0],
        "training_rows": "FakeRecogna 2.0 extrativa casada + metade dos pares do Fake.br",
        "training_split": origem.name,
    }
    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pacote, saida, compress=3)
    print(f"Salvo em {saida} ({saida.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
