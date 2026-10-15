# ml/ — Modelo de Machine Learning (RF10)

Treina e exporta o classificador de produção: um **stacking de 5 modelos clássicos**
(TF-IDF + Regressão Logística, SVM, Naive Bayes, SVM em n-gramas de caractere,
SVD+GBM), combinados por um meta-modelo de regressão logística. O protocolo de
treino, validação e a decisão do modelo final **já foram definidos** pelo time de
dados (Mayara, Rayssa e Rafaella) num desafio paralelo de ML.

## Histórico: por que não tem BERTopic

O protocolo original (`decisao_modelo.md` do desafio de ML) decidiu por um
stacking de **6** modelos, incluindo BERTopic+LR. Duas integrações independentes
foram feitas no mesmo dia (12-13/10) — uma com os 6 modelos (Tayrine) e outra só
com os 5 clássicos (Mayara, `backend/app/adapters/stacking_classifier.py`) — e
foram consolidadas na segunda, por três motivos:

1. BERTopic era o modelo com **menor peso no meta-modelo** (0.08, o menor dos 6)
   e a **pior performance individual** (ROC-AUC 0.835 vs 0.98+ dos outros).
2. Em produção (Docker), o artefato do BERTopic quebrou por incompatibilidade de
   versão do Python entre treino e runtime (pickle de objetos compilados pelo
   `numba`, usado pelo UMAP/HDBSCAN internos do BERTopic) — um problema de
   fragilidade operacional que os outros 5 modelos não têm.
3. O artefato do BERTopic sozinho tinha 78MB (baixa um modelo de embeddings do
   Hugging Face na primeira execução) — bem mais pesado que os outros 5 somados.

O meta-modelo foi re-treinado só com os 5 modelos (não é só remover o peso do
BERTopic do vetor original — os pesos mudam quando se re-ajusta sem ele).

## Dataset

Os datasets **não estão neste repositório**. O modelo atual usa a **FakeRecogna 2.0** (Hugging Face,
`recogna-nlp`, variante extrativa: texto natural, em minúsculas, sem lematização) e o **Fake.br**,
tratados no repositório do desafio de ML. Os modelos salvos de lá viram o pacote do backend com
`ml/empacotar_stacking.py`.

**Importante**: os modelos usam **somente a coluna `Noticia`**. O `Titulo` traz o veredito escrito
em ~64% das notícias Fake (ex.: "É #FAKE: ...") e inflaria as métricas.

## Decisão do modelo (resumo, protocolo original com os 6)

Protocolo (seção 9 do desafio de ML): validação cruzada de 5 folds, ROC-AUC com
IC95% por bootstrap, Brier como métrica de calibração, e ensembles só adotados se
houver ganho **consistente** (IC95% do ganho pareado excluindo 0 e vitória em ≥4/5
folds, tanto em AUC quanto em Brier).

| modelo | roc_auc | brier | accuracy |
|---|---|---|---|
| baseline (LR) | 0.989 | 0.055 | 0.951 |
| svm (calibrado) | 0.992 | 0.030 | 0.962 |
| nb (calibrado) | 0.981 | 0.052 | 0.930 |
| char (SVM n-gramas) | 0.992 | 0.031 | 0.960 |
| gbm (SVD+HistGBM) | 0.982 | 0.050 | 0.933 |
| ~~bertopic (tópicos+LR)~~ | ~~0.835~~ | ~~0.167~~ | ~~0.752~~ |
| **stacking (meta-LR), 5 modelos** | **~0.993** | **~0.028** | **~0.964** |

Detalhes completos do protocolo original (pesos, correlação entre modelos,
gráficos) ficam só no material de origem do time de dados
(`modelos_outputs/stacking/decisao_modelo.md`), que não faz parte deste repositório.

## Artefato gerado

`backend/models/stacking.joblib` — um único pacote (dict serializado via joblib)
carregado por `backend/app/adapters/stacking_classifier.py::StackingClassifier`:

| chave | conteúdo |
|---|---|
| `base_models` | lista de nomes, na ordem usada pelo meta-modelo: `baseline`, `svm`, `nb`, `char`, `gbm` |
| `models` | dict nome → `Pipeline`/`CalibratedClassifierCV` do scikit-learn, já ajustado |
| `meta_model` | `LogisticRegression` sobre o logit das probabilidades dos modelos base |
| `version`, `input` | versão do formato do pacote e modo de entrada (`"noticia"`) |
| `sklearn_version`, `python_version` | gravados no treino; o `StackingClassifier` **recusa carregar** se não baterem com o ambiente de execução (evita o tipo de quebra silenciosa que o BERTopic teve) |
| `training_rows`, `training_split` | proveniência do treino |

## Como treinar/re-exportar (modelo ANTIGO, FakeRecogna 1)

> Mantido por histórico. Para o modelo atual use `ml/empacotar_stacking.py` (seção abaixo).

```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python treinar_e_exportar_stacking.py --dataset-csv /caminho/para/NoRemovalWords_tratada_dedup.csv
```

Treina os 5 modelos clássicos (rápido, segundos a poucos minutos) e grava o
pacote em `backend/models/stacking.joblib`, no formato acima.

## Modelo em produção (atualizado em 2026-10-15)

`backend/models/stacking.joblib` vem do desafio de ML: FakeRecogna 2.0 extrativa casada por
tamanho **mais metade dos pares do Fake.br** (`modelos/avaliar_externo.py --salvar
--treino-externo 0.5` no repositório do desafio). O pacote é gerado por:

```bash
python ml/empacotar_stacking.py --origem /caminho/modelos_salvos/FakeRecogna2_extrativa_casada_com_fakebr
```

Rode com o **mesmo Python e scikit-learn do backend**: o `StackingClassifier` recusa carregar se
divergirem, ou se `input_preprocessing` do pacote não for o que o backend aplica (minúsculas,
remoção do `none`, espaços normalizados, texto completo).

### Falsos positivos e a correção

O modelo treinado só na FakeRecogna dava "suspeito" com probabilidade alta para notícias reais: o
Real do treino é quase só de 2020-2021 sobre covid, e o modelo aprendeu época e tema. No Fake.br,
26% dos Reais saíam como Fake com limiar 0,5.

Correções: (1) metade dos pares do Fake.br entra no treino; (2) o backend usa três faixas, não o
limiar único: Real (p < 0,3), Incerto (0,3 a 0,7) e Fake (p >= 0,7). Só Fake vira `suspeito`;
Real e Incerto viram `nao_verificado`, e o Incerto traz a justificativa de revisão humana.

### Desempenho esperado

Nos pares de teste do Fake.br (não vistos no treino): AUC 0,961; 4,9% dos Reais como Fake, 81% dos
Fake detectados, ~14% em Incerto. Esse teste não é independente (pares das mesmas fontes) e, fora
do diariodobrasil.org, tem só 141 Fake. **Em fontes e épocas novas, espere pior.** Sem truncar o
texto, o resultado no Fake.br foi igual ou ligeiramente melhor que com corte em 100 palavras (Reais
como Fake: 1,9% contra 2,4%, em todo o conjunto, que inclui a metade vista no treino).

O treino só viu textos de ~50 a 190 palavras.
