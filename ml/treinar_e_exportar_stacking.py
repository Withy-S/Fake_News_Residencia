# -*- coding: utf-8 -*-
"""
treinar_e_exportar_stacking.py — treina e persiste o classificador de produção (RF10)
=======================================================================================
Baseado nos scripts de treino de Mayara/Rayssa/Rafaella no desafio paralelo de ML
("Challenge: Fake News"), cujo protocolo completo está documentado em
modelos/README.md e modelos_outputs/stacking/decisao_modelo.md daquele desafio
(resumo também em ml/README.md). Este script NÃO escolhe nem re-avalia modelos — a
escolha já foi feita pelo time de dados por protocolo pré-registrado (validação
cruzada de 5 folds, IC95% por bootstrap, teste de ganho consistente). A única
tarefa daqui é reproduzir o FIT FINAL de cada modelo (no conjunto de desenvolvimento
inteiro, sem CV) e persistir os artefatos treinados.

Stacking de **5 modelos clássicos** (sem BERTopic — ver "Histórico" em ml/README.md
para o porquê: menor peso no meta-modelo, pior performance individual, e quebrou em
produção por incompatibilidade de versão do Python no pickle do BERTopic/numba).

Os hiperparâmetros de cada modelo são EXATAMENTE os hiperparâmetros finais escolhidos
pelo time de dados (não há busca de hiperparâmetro aqui, ela já foi feita). O
meta-modelo (stacking) nem é re-treinado: os pesos finais já estão calculados
(re-ajustados sem o BERTopic) e são só reconstruídos como um objeto LogisticRegression
do scikit-learn, pronto para usar.

Dataset (NÃO está neste repositório — datasets não vão para o git):
    FakeRecogna, tratado e deduplicado pelo time de dados:
    dados_tratados/NoRemovalWords_tratada_dedup.csv (11.670 linhas)
    Peça o arquivo a quem fez o desafio de ML (Mayara/Rayssa/Rafaella) e informe o
    caminho local com --dataset-csv.

Uso:
    python ml/treinar_e_exportar_stacking.py --dataset-csv /caminho/para/NoRemovalWords_tratada_dedup.csv

Saída: backend/models/stacking.joblib — um único pacote (dict) carregado por
backend/app/adapters/stacking_classifier.py::StackingClassifier. Ver o formato
exato em ml/README.md.
"""
import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

SEED = 42
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_PATH = REPO_ROOT / "backend" / "models" / "stacking.joblib"

# Ordem oficial dos modelos base (= base_models no pacote exportado).
BASE_MODELS = ["baseline", "svm", "nb", "char", "gbm"]

# Pesos finais do meta-modelo, re-ajustado sem o BERTopic (NÃO re-treinado aqui).
PESOS_META_FINAL = {
    "baseline": -2.81979266,
    "svm": 1.25086017,
    "nb": 0.27438934,
    "char": 0.53575253,
    "gbm": 0.2737443,
    "intercepto": -0.01641489,
}


# --------------------------------------------------------------------------- dados
def carregar_dev(dataset_csv: Path) -> tuple[np.ndarray, np.ndarray, int, int]:
    """Carrega o CSV e aplica o split determinístico oficial (teste 80/20 + seed 42).
    Retorna só a parte de DESENVOLVIMENTO (os 80%), que é tudo que o fit final usa."""
    df = pd.read_csv(dataset_csv)
    X = df["Noticia"].fillna("").astype(str).str.strip().to_numpy()
    y = (df["Rotulo"].astype(str).str.strip().str.lower() == "fake").astype(int).to_numpy()

    ids = np.arange(len(y))
    ids_dev, ids_te = train_test_split(ids, test_size=0.2, stratify=y, random_state=SEED)
    print(f"Documentos: {len(y)} | Fake: {int(y.sum())} ({y.mean():.1%}) | "
          f"Desenvolvimento: {len(ids_dev)} | Teste (reservado, não usado aqui): {len(ids_te)}")
    return X[ids_dev], y[ids_dev], len(ids_dev), len(ids_te)


# --------------------------------------------------------------------------- modelos clássicos
def vetorizador_padrao() -> TfidfVectorizer:
    return TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.9,
                           sublinear_tf=True, strip_accents="unicode")


def montar_baseline() -> Pipeline:
    return Pipeline([("tfidf", vetorizador_padrao()),
                     ("lr", LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))])


def montar_svm() -> Pipeline:
    # Escolhido: sigmoid, C=1.0 (modelos_outputs/svm/metricas.json).
    return Pipeline([("tfidf", vetorizador_padrao()),
                     ("calibrado", CalibratedClassifierCV(
                         estimator=LinearSVC(C=1.0, loss="squared_hinge", dual="auto",
                                             max_iter=20_000, random_state=SEED),
                         method="sigmoid", cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
                         ensemble=True))])


def montar_nb() -> CalibratedClassifierCV:
    # Escolhido: "depois_sigmoid" (modelos_outputs/nb/metricas.json). Sem Pipeline/tfidf
    # próprio porque o texto já entra vetorizado via o pipeline externo — ver treinar().
    return CalibratedClassifierCV(
        MultinomialNB(), method="sigmoid",
        cv=StratifiedKFold(5, shuffle=True, random_state=SEED), ensemble=True)


def montar_char() -> Pipeline:
    return Pipeline([("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=5,
                                               max_df=0.9, sublinear_tf=True, max_features=300_000,
                                               dtype=np.float32)),
                     ("clf", CalibratedClassifierCV(
                         LinearSVC(C=1.0, dual="auto", max_iter=20_000, random_state=SEED),
                         method="sigmoid", cv=StratifiedKFold(5, shuffle=True, random_state=SEED)))])


def montar_gbm() -> Pipeline:
    return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 1), min_df=5, max_df=0.9,
                                               sublinear_tf=True, strip_accents="unicode",
                                               max_features=30_000)),
                     ("svd", TruncatedSVD(200, random_state=SEED)),
                     ("gbm", HistGradientBoostingClassifier(max_depth=4, learning_rate=0.08,
                                                            max_iter=250, l2_regularization=1.0,
                                                            random_state=SEED))])


def montar_nb_pipeline() -> Pipeline:
    # NB precisa de um Pipeline próprio (com tfidf) pra ser chamado como os outros,
    # já que StackingClassifier chama model.predict_proba([texto]) direto.
    return Pipeline([("tfidf", vetorizador_padrao()), ("clf", montar_nb())])


FABRICAS = {
    "baseline": montar_baseline,
    "svm": montar_svm,
    "nb": montar_nb_pipeline,
    "char": montar_char,
    "gbm": montar_gbm,
}


def treinar_classicos(X_dev: np.ndarray, y_dev: np.ndarray) -> dict:
    modelos = {}
    for nome, fabrica in FABRICAS.items():
        modelo = fabrica().fit(X_dev, y_dev)
        modelos[nome] = modelo
        print(f"[{nome}] treinado")
    return modelos


# --------------------------------------------------------------------------- meta-modelo
def montar_meta_modelo() -> LogisticRegression:
    """NÃO re-treina: reconstrói o meta-modelo final com os pesos já calculados
    (re-ajustados sem o BERTopic), como decidido no protocolo (seção 9)."""
    meta = LogisticRegression()
    meta.classes_ = np.array([0, 1])
    meta.coef_ = np.array([[PESOS_META_FINAL[m] for m in BASE_MODELS]])
    meta.intercept_ = np.array([PESOS_META_FINAL["intercepto"]])
    return meta


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset-csv", required=True, type=Path,
                    help="caminho local para NoRemovalWords_tratada_dedup.csv (não está no repo)")
    ap.add_argument("--out-path", type=Path, default=DEFAULT_OUT_PATH,
                    help=f"arquivo de saída do pacote (padrão: {DEFAULT_OUT_PATH})")
    args = ap.parse_args()

    if not args.dataset_csv.exists():
        sys.exit(f"Dataset não encontrado: {args.dataset_csv}")

    args.out_path.parent.mkdir(parents=True, exist_ok=True)
    X_dev, y_dev, n_dev, n_teste = carregar_dev(args.dataset_csv)

    print("\n=== Modelos clássicos (TF-IDF: baseline, svm, nb, char, gbm) ===")
    modelos = treinar_classicos(X_dev, y_dev)

    print("\n=== Meta-modelo (stacking, pesos re-ajustados sem BERTopic) ===")
    meta = montar_meta_modelo()

    pacote = {
        "version": 1,
        "input": "noticia",
        "positive_class": "Fake",
        "base_models": BASE_MODELS,
        "models": modelos,
        "meta_model": meta,
        "sklearn_version": sklearn.__version__,
        "python_version": sys.version,
        "training_rows": n_dev,
        "training_split": "80% desenvolvimento; teste reservado excluído",
    }
    joblib.dump(pacote, args.out_path)
    tamanho_mb = args.out_path.stat().st_size / 1e6
    print(f"\nPacote salvo em {args.out_path} ({tamanho_mb:.1f} MB)")


if __name__ == "__main__":
    main()
