"""Classificador de ML real (RF10): stacking de 6 modelos sobre o dataset FakeRecogna.

Protocolo decidido pelo time de dados (ver ml/README.md e os artefatos em
ml_artifacts/manifest.json): 5 modelos clássicos (TF-IDF + LR/SVM/NB/SVM-char/GBM) mais
um BERTopic+LR, combinados por um meta-modelo de regressão logística sobre o logit das
probabilidades de cada um. Este módulo só carrega os artefatos já treinados e reproduz a
combinação — não re-treina nada (isso é feito por ml/treinar_e_exportar_stacking.py).
"""

import json
import unicodedata
from pathlib import Path

import joblib
import numpy as np

from app.domain.enums import Classification, Method
from app.domain.models import ClassifierResult

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"

# Ordem oficial dos modelos base (= MODELOS_BASE em modelos/stacking.py do time de dados).
MODELOS_BASE = ["baseline", "svm", "nb", "char", "gbm", "bertopic"]


def _logit(p: np.ndarray, eps: float = 1e-4) -> np.ndarray:
    """Igual a modelos/stacking.py::logit — clipa e aplica log-odds."""
    p = np.clip(p, eps, 1 - eps)
    return np.log(p / (1 - p))


def _sem_acento(docs: list[str]) -> list[str]:
    """Igual a modelos/treinar_bertopic.py::sem_acento."""
    return [
        unicodedata.normalize("NFKD", d).encode("ascii", "ignore").decode("ascii")
        for d in docs
    ]


def _features_topicos(modelo, docs: list[str], emb: np.ndarray) -> np.ndarray:
    """Igual a modelos/treinar_bertopic.py::features_topicos (com_embeddings=False, o
    padrão oficial): probabilidades por tópico + massa de outlier + flag de outlier."""
    topicos, probs = modelo.transform(_sem_acento(docs), embeddings=emb)
    topicos = np.asarray(topicos)
    n_top = len([t for t in modelo.get_topics() if t != -1])
    if probs is None or np.ndim(probs) != 2:
        probs = np.zeros((len(docs), n_top))
        for i, t in enumerate(topicos):
            if t >= 0:
                probs[i, t] = 1.0
    probs = np.asarray(probs, dtype=np.float64)
    outlier = np.clip(1.0 - probs.sum(axis=1, keepdims=True), 0, 1)
    return np.hstack([probs, outlier, (topicos == -1).astype(float).reshape(-1, 1)])


class MLStackingClassifier:
    """Stacking de 6 classificadores (RF10): a decisão final de produção do time de dados.

    Carrega todos os artefatos uma única vez no __init__ (pensado para ser instanciado
    uma vez só, via lru_cache em app/api/v1/dependencies.py::get_pipeline). Timeout e
    isolamento de erro em runtime já são tratados por ResilientClassifier — esta classe
    não precisa (e não deve) duplicar essa lógica.
    """

    def __init__(self, artifacts_dir: Path = ARTIFACTS_DIR) -> None:
        self.baseline = joblib.load(artifacts_dir / "baseline.joblib")
        self.svm = joblib.load(artifacts_dir / "svm.joblib")
        self.nb = joblib.load(artifacts_dir / "nb.joblib")
        self.char = joblib.load(artifacts_dir / "char.joblib")
        self.gbm = joblib.load(artifacts_dir / "gbm.joblib")
        self.meta = joblib.load(artifacts_dir / "meta_model.joblib")

        # BERTopic é o modelo base mais caro: embeddings SBERT + tópicos.
        from bertopic import BERTopic

        self.bertopic_topics = BERTopic.load(str(artifacts_dir / "bertopic_topic.pkl"))
        self.bertopic_clf = joblib.load(artifacts_dir / "bertopic_clf.joblib")

        manifest = json.loads(
            (artifacts_dir / "manifest.json").read_text(encoding="utf-8")
        )
        from sentence_transformers import SentenceTransformer

        self.embedder = SentenceTransformer(manifest["modelo_embedding"])

    def _p_fake_bertopic(self, text: str) -> float:
        emb = self.embedder.encode([text], normalize_embeddings=True)
        features = _features_topicos(self.bertopic_topics, [text], emb)
        return float(self.bertopic_clf.predict_proba(features)[:, 1][0])

    def classify(self, text: str) -> ClassifierResult:
        probs = {
            "baseline": float(self.baseline.predict_proba([text])[:, 1][0]),
            "svm": float(self.svm.predict_proba([text])[:, 1][0]),
            "nb": float(self.nb.predict_proba([text])[:, 1][0]),
            "char": float(self.char.predict_proba([text])[:, 1][0]),
            "gbm": float(self.gbm.predict_proba([text])[:, 1][0]),
            "bertopic": self._p_fake_bertopic(text),
        }
        vetor = _logit(np.array([[probs[m] for m in MODELOS_BASE]]))
        p_fake = float(self.meta.predict_proba(vetor)[:, 1][0])

        classification = (
            Classification.SUSPICIOUS if p_fake >= 0.5 else Classification.TRUSTED
        )
        confidence = round(p_fake if p_fake >= 0.5 else 1 - p_fake, 2)
        return ClassifierResult(
            classification=classification,
            confidence=confidence,
            justifications=[
                (
                    "Classificação por stacking de 6 classificadores de ML (5 modelos "
                    "clássicos + BERTopic), treinados sobre o dataset FakeRecogna."
                ),
                (
                    "AVISO: o texto de treino do FakeRecogna passou por um pré-processamento "
                    "(lematização) que ainda não foi replicado aqui para o texto de entrada. "
                    "O percentual pode não ser confiável para texto real da web até isso ser "
                    "corrigido (ver ml/README.md)."
                ),
            ],
            method=Method.ML_MODEL,
        )
