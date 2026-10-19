import sys
from pathlib import Path

import joblib
import numpy as np
import sklearn

from app.domain.enums import Classification, Method
from app.domain.errors import AnalysisUnavailableError
from app.domain.models import ClassifierResult


class StackingClassifier:
    def __init__(self, model_path: str) -> None:
        path = Path(model_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        if not path.is_file():
            raise FileNotFoundError(f"Artefato do stacking não encontrado: {path}")

        package = joblib.load(path)
        if package.get("version") != 1 or package.get("input") != "noticia":
            raise ValueError(
                "Formato ou modo de entrada incompatível no artefato do stacking."
            )
        if package.get("sklearn_version") != sklearn.__version__:
            raise ValueError(
                "Versão do scikit-learn incompatível com o artefato: "
                f"treino={package.get('sklearn_version')}, runtime={sklearn.__version__}."
            )
        trained_python = package.get("python_version", "")
        if trained_python.split(".")[:2] != sys.version.split(".")[:2]:
            raise ValueError(
                "Versão principal/secundária do Python incompatível com o artefato: "
                f"treino={trained_python}, runtime={sys.version.split()[0]}."
            )
        self.base_models = package["base_models"]
        self.models = package["models"]
        self.meta_model = package["meta_model"]

    def classify(self, text: str) -> ClassifierResult:
        probabilities = []
        for name in self.base_models:
            model = self.models[name]
            class_index = list(model.classes_).index(1)
            probabilities.append(float(model.predict_proba([text])[0, class_index]))

        clipped = np.clip(probabilities, 1e-4, 1 - 1e-4)
        logits = np.log(clipped / (1 - clipped)).reshape(1, -1)
        fake_index = list(self.meta_model.classes_).index(1)
        fake_probability = float(self.meta_model.predict_proba(logits)[0, fake_index])
        if not np.isfinite(fake_probability):
            raise AnalysisUnavailableError(
                "O modelo retornou uma probabilidade inválida."
            )

        confidence = max(fake_probability, 1 - fake_probability)
        classification = (
            Classification.SUSPICIOUS
            if fake_probability >= 0.5
            else Classification.UNVERIFIED
        )
        return ClassifierResult(
            classification=classification,
            confidence=confidence,
            method=Method.ML_MODEL,
            fake_probability=fake_probability,
            justifications=[
                (
                    f"O modelo estimou {fake_probability:.1%} de probabilidade para a classe Fake. "
                    "É uma estimativa automática, não uma verificação factual."
                )
            ],
        )
