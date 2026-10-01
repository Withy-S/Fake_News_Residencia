from typing import Protocol

from app.domain.models import ClassifierResult


class Classifier(Protocol):
    def classify(self, text: str) -> ClassifierResult: ...
