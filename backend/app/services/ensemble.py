from collections import defaultdict

from app.schemas.analyze import Classification
from app.services.classifiers import (
    AnalysisUnavailableError,
    Classifier,
    ClassifierResult,
)


class EnsembleClassifier:
    """Combina vários classificadores num só (padrão Composite).

    Para o pipeline, é só mais um Classifier. Cada membro vota na sua
    classificação com peso x confiança; vence a classificação com mais votos.
    Membro indisponível fica de fora da votação. Se todos caírem, o conjunto
    fica indisponível e o pipeline segue para o fallback.
    """

    def __init__(
        self, members: dict[str, Classifier], weights: dict[str, float]
    ) -> None:
        if not members:
            raise ValueError(
                "O classificador combinado precisa de pelo menos 1 membro."
            )
        self.members = members
        self.weights = weights

    def classify(self, text: str) -> ClassifierResult:
        votes: dict[Classification, float] = defaultdict(float)
        contribution: dict[Classification, dict] = defaultdict(dict)
        justifications: list[str] = []
        total_weight = 0.0

        for name, member in self.members.items():
            try:
                result = member.classify(text)
            except AnalysisUnavailableError:
                continue
            weight = self.weights.get(name, 1.0)
            total_weight += weight
            vote = weight * result.confidence
            votes[result.classification] += vote
            contribution[result.classification][result.method] = (
                contribution[result.classification].get(result.method, 0.0) + vote
            )
            justifications.extend(result.justifications)

        if total_weight == 0:
            raise AnalysisUnavailableError("Nenhum membro do conjunto respondeu.")

        winner = max(votes, key=votes.get)
        confidence = round(votes[winner] / total_weight, 2)
        # RF14: o método informado é o de quem mais pesou na classificação vencedora.
        methods = contribution[winner]
        method = max(methods, key=methods.get)
        return ClassifierResult(
            winner, confidence, list(dict.fromkeys(justifications)), method
        )
