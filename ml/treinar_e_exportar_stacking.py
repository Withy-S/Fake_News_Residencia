# -*- coding: utf-8 -*-
"""
treinar_e_exportar_stacking.py — treina e persiste o classificador de produção (RF10)
=======================================================================================
Baseado nos scripts de treino de Mayara/Rayssa/Rafaella no desafio paralelo de ML
("Challenge: Fake News"), cujo protocolo completo e cuja decisão final (Stacking:
meta-regressão logística sobre 6 modelos base) estão documentados em
modelos/README.md e modelos_outputs/stacking/decisao_modelo.md daquele desafio
(resumo também em ml/README.md). Este script NÃO escolhe nem re-avalia modelos — a
escolha já foi feita pelo time de dados por protocolo pré-registrado (validação
cruzada de 5 folds, IC95% por bootstrap, teste de ganho consistente). A única
tarefa daqui é reproduzir o FIT FINAL de cada modelo (no conjunto de desenvolvimento
inteiro, sem CV) e persistir os artefatos treinados, que nunca tinham sido salvos.

Os hiperparâmetros de cada modelo são EXATAMENTE os hiperparâmetros finais escolhidos
pelo time de dados (não há busca de hiperparâmetro aqui, ela já foi feita). O
meta-modelo (stacking) nem é re-treinado: os pesos finais já estão calculados
(modelos_outputs/stacking/pesos_meta.csv) e são só reconstruídos como um objeto
LogisticRegression do scikit-learn, pronto para usar.

Dataset (NÃO está neste repositório — datasets não vão para o git):
    FakeRecogna, tratado e deduplicado pelo time de dados:
    dados_tratados/NoRemovalWords_tratada_dedup.csv (11.670 linhas)
    Peça o arquivo a quem fez o desafio de ML (Mayara/Rayssa/Rafaella) e informe o
    caminho local com --dataset-csv.

Uso:
    python ml/treinar_e_exportar_stacking.py --dataset-csv /caminho/para/NoRemovalWords_tratada_dedup.csv
    python ml/treinar_e_exportar_stacking.py --dataset-csv ... --skip-bertopic   # iteração rápida, NÃO usar para a entrega final

Saídas em backend/app/ml_artifacts/:
    baseline.joblib, svm.joblib, nb.joblib, char.joblib, gbm.joblib,
    bertopic_topic.pkl, bertopic_clf.joblib, meta_model.joblib, manifest.json
"""
import argparse
import json
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

SEED = 42
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "backend" / "app" / "ml_artifacts"

# Ordem oficial dos modelos base = MODELOS_BASE em modelos/stacking.py do desafio de ML.
MODELOS_BASE = ["baseline", "svm", "nb", "char", "gbm", "bertopic"]

# Pesos finais do meta-modelo (já treinado pelo time de dados, NÃO re-treinado aqui).
# Fonte: modelos_outputs/stacking/pesos_meta.csv, coluna peso_meta_final, na ordem de
# MODELOS_BASE (ver modelos_outputs/stacking/decisao_modelo.md para o protocolo completo).
PESOS_META_FINAL = {
    "baseline": -2.829553119752414,
    "svm": 1.2598988894809418,
    "nb": 0.2548623392821334,
    "char": 0.5326232943897913,
    "gbm": 0.262829446518367,
    "bertopic": 0.08344848148722434,
    "intercepto": -0.011128595019243046,
}

MODELO_EMBEDDING = "paraphrase-multilingual-MiniLM-L12-v2"

# stopwords mínimas do português — copiadas de modelos/treinar_bertopic.py (STOP_PT),
# só para os rótulos dos tópicos (c-TF-IDF) ficarem legíveis.
STOP_PT = [
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "sob", "sobre", "e", "ou", "mas", "que", "se", "como",
    "ao", "aos", "à", "às", "ser", "estar", "ter", "haver", "ir", "foi", "é", "são", "há", "já", "não",
    "mais", "muito", "também", "só", "seu", "sua", "seus", "suas", "ele", "ela", "eles", "elas", "isso",
    "este", "esta", "esse", "essa", "n", "ano", "dia", "vez",
]


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
                     ("clf", CalibratedClassifierCV(
                         estimator=LinearSVC(C=1.0, loss="squared_hinge", dual="auto",
                                             max_iter=20_000, random_state=SEED),
                         method="sigmoid", cv=StratifiedKFold(5, shuffle=True, random_state=SEED),
                         ensemble=True))])


def montar_nb() -> Pipeline:
    # Escolhido: "depois_sigmoid" (modelos_outputs/nb/metricas.json).
    return Pipeline([("tfidf", vetorizador_padrao()),
                     ("clf", CalibratedClassifierCV(
                         MultinomialNB(), method="sigmoid",
                         cv=StratifiedKFold(5, shuffle=True, random_state=SEED), ensemble=True))])


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


CLASSICOS = {
    "baseline": montar_baseline,
    "svm": montar_svm,
    "nb": montar_nb,
    "char": montar_char,
    "gbm": montar_gbm,
}


def treinar_classicos(X_dev: np.ndarray, y_dev: np.ndarray, out_dir: Path) -> None:
    for nome, fabrica in CLASSICOS.items():
        t0 = time.time()
        modelo = fabrica().fit(X_dev, y_dev)
        caminho = out_dir / f"{nome}.joblib"
        joblib.dump(modelo, caminho)
        tamanho_mb = caminho.stat().st_size / 1e6
        print(f"[{nome}] treinado e salvo em {caminho.name} ({tamanho_mb:.1f} MB, {time.time() - t0:.0f}s)")


# --------------------------------------------------------------------------- BERTopic
def sem_acento(docs: list[str]) -> list[str]:
    """Igual a modelos/treinar_bertopic.py::sem_acento. O BERTopic remove caracteres
    não-ASCII ao montar os rótulos dos tópicos; tirar os acentos antes preserva as
    palavras. Os embeddings já foram calculados com o texto original."""
    return [unicodedata.normalize("NFKD", d).encode("ascii", "ignore").decode("ascii") for d in docs]


def novo_bertopic():
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from umap import UMAP

    return BERTopic(
        embedding_model=None,  # embeddings pré-calculados são passados em fit/transform
        umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine",
                        random_state=SEED),
        hdbscan_model=HDBSCAN(min_cluster_size=30, metric="euclidean",
                              cluster_selection_method="eom", prediction_data=True),
        vectorizer_model=CountVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95,
                                         strip_accents="unicode", stop_words=STOP_PT),
        calculate_probabilities=True,
        nr_topics=None,
        top_n_words=10,
        verbose=False,
    )


def features_topicos(modelo, docs: list[str], emb: np.ndarray, com_embeddings: bool) -> np.ndarray:
    """Igual a modelos/treinar_bertopic.py::features_topicos. com_embeddings=False é o
    padrão oficial: só as probabilidades de tópico, sem concatenar o embedding denso."""
    topicos, probs = modelo.transform(sem_acento(docs), embeddings=emb)
    topicos = np.asarray(topicos)
    n_top = len([t for t in modelo.get_topics() if t != -1])
    if probs is None or np.ndim(probs) != 2:
        probs = np.zeros((len(docs), n_top))
        for i, t in enumerate(topicos):
            if t >= 0:
                probs[i, t] = 1.0
    probs = np.asarray(probs, dtype=np.float64)
    outlier = np.clip(1.0 - probs.sum(axis=1, keepdims=True), 0, 1)
    f = np.hstack([probs, outlier, (topicos == -1).astype(float).reshape(-1, 1)])
    if com_embeddings:
        f = np.hstack([f, emb])
    return f


def treinar_bertopic(X_dev: np.ndarray, y_dev: np.ndarray, out_dir: Path,
                     modelo_embedding: str, batch_size: int) -> None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise SystemExit(
            "Instale sentence-transformers (pip install -r ml/requirements.txt) "
            "ou rode com --skip-bertopic para iterar sem o BERTopic (NÃO vale para a entrega final)."
        ) from e

    print(f"[bertopic] calculando embeddings com '{modelo_embedding}' (baixa do Hugging Face "
          "na 1a execução, precisa de internet)...")
    t0 = time.time()
    enc = SentenceTransformer(modelo_embedding)
    E_dev = np.asarray(
        enc.encode(list(X_dev), batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True),
        dtype=np.float32,
    )
    print(f"[bertopic] embeddings {E_dev.shape} prontos em {time.time() - t0:.0f}s")

    t0 = time.time()
    bt = novo_bertopic()
    bt.fit_transform(sem_acento(list(X_dev)), embeddings=E_dev)
    F_dev = features_topicos(bt, list(X_dev), E_dev, com_embeddings=False)
    n_topicos = len([t for t in bt.get_topics() if t != -1])
    print(f"[bertopic] {n_topicos} tópicos encontrados, ajustado em {time.time() - t0:.0f}s")

    clf = Pipeline([("sc", StandardScaler()),
                    ("lr", LogisticRegression(C=1.0, max_iter=3000, random_state=SEED))])
    clf.fit(F_dev, y_dev)

    caminho_bt = out_dir / "bertopic_topic.pkl"
    bt.save(str(caminho_bt), serialization="pickle")
    caminho_clf = out_dir / "bertopic_clf.joblib"
    joblib.dump(clf, caminho_clf)
    print(f"[bertopic] salvo: {caminho_bt.name} ({caminho_bt.stat().st_size / 1e6:.1f} MB), "
          f"{caminho_clf.name} ({caminho_clf.stat().st_size / 1e6:.1f} MB)")


# --------------------------------------------------------------------------- meta-modelo
def exportar_meta_modelo(out_dir: Path) -> None:
    """NÃO re-treina: reconstrói o meta-modelo final com os pesos já calculados
    (modelos_outputs/stacking/pesos_meta.csv), como decidido no protocolo (seção 9)."""
    meta = LogisticRegression()
    meta.classes_ = np.array([0, 1])
    meta.coef_ = np.array([[PESOS_META_FINAL[m] for m in MODELOS_BASE]])
    meta.intercept_ = np.array([PESOS_META_FINAL["intercepto"]])
    caminho = out_dir / "meta_model.joblib"
    joblib.dump(meta, caminho)
    print(f"[meta] reconstruído a partir dos pesos finais e salvo em {caminho.name}")


# --------------------------------------------------------------------------- manifest
def escrever_manifest(out_dir: Path, n_dev: int, n_teste: int, modelo_embedding: str,
                      dataset_csv: Path, incluiu_bertopic: bool) -> None:
    manifest = {
        "descricao": "Artefatos do classificador de produção (RF10): stacking de 6 modelos "
                     "sobre o dataset FakeRecogna, protocolo decidido pelo time de dados.",
        "modelos_base_ordem": MODELOS_BASE,
        "modelo_embedding": modelo_embedding,
        "bertopic_incluido": incluiu_bertopic,
        "meta_modelo": "LogisticRegression sobre logit(P(Fake)) dos 6 modelos base "
                       "(pesos fixos, não re-treinados — ver pesos_meta_final abaixo)",
        "pesos_meta_final": PESOS_META_FINAL,
        "treinado_em_utc": datetime.now(timezone.utc).isoformat(),
        "origem_dados": {
            "dataset": "FakeRecogna (fake news em português), tratado pelo time de dados",
            "arquivo": "dados_tratados/NoRemovalWords_tratada_dedup.csv",
            "linhas_totais_originais": n_dev + n_teste,
            "linhas_desenvolvimento_usadas_no_fit": n_dev,
            "linhas_teste_reservado_nao_usadas": n_teste,
            "coluna_entrada": "Noticia (NÃO Titulo — vaza o veredito em ~64% dos Fake, ver auditoria)",
            "caminho_local_usado_no_treino": str(dataset_csv),
        },
        "decisao_do_modelo": "Stacking (meta-regressão logística sobre os 6 modelos base) — "
                             "decisão final do protocolo pré-registrado do time de dados. "
                             "Resumo em ml/README.md; detalhes completos em "
                             "modelos_outputs/stacking/decisao_modelo.md do desafio de ML "
                             "(Mayara/Rayssa/Rafaella).",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[manifest] escrito em {out_dir / 'manifest.json'}")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset-csv", required=True, type=Path,
                    help="caminho local para NoRemovalWords_tratada_dedup.csv (não está no repo)")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                    help=f"pasta de saída dos artefatos (padrão: {DEFAULT_OUT_DIR})")
    ap.add_argument("--modelo-embedding", default=MODELO_EMBEDDING)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--skip-bertopic", action="store_true",
                    help="pula o BERTopic (iteração rápida; NÃO usar para a entrega final — "
                         "o protocolo exige os 6 modelos base)")
    args = ap.parse_args()

    if not args.dataset_csv.exists():
        sys.exit(f"Dataset não encontrado: {args.dataset_csv}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    X_dev, y_dev, n_dev, n_teste = carregar_dev(args.dataset_csv)

    print("\n=== Modelos clássicos (TF-IDF: baseline, svm, nb, char, gbm) ===")
    treinar_classicos(X_dev, y_dev, args.out_dir)

    if args.skip_bertopic:
        print("\n[AVISO] --skip-bertopic: bertopic_topic.pkl/bertopic_clf.joblib NÃO foram "
              "gerados. O MLStackingClassifier não vai carregar sem eles.")
    else:
        print("\n=== BERTopic ===")
        treinar_bertopic(X_dev, y_dev, args.out_dir, args.modelo_embedding, args.batch_size)

    print("\n=== Meta-modelo (stacking) ===")
    exportar_meta_modelo(args.out_dir)

    escrever_manifest(args.out_dir, n_dev, n_teste, args.modelo_embedding,
                      args.dataset_csv, incluiu_bertopic=not args.skip_bertopic)

    print(f"\nArtefatos em {args.out_dir}")


if __name__ == "__main__":
    main()
