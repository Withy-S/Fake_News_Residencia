# ml/ — Modelo de Machine Learning (RF10)

Treina e exporta o classificador de produção: um **stacking de 6 modelos** (TF-IDF +
Regressão Logística, SVM, Naive Bayes, SVM em n-gramas de caractere, SVD+GBM, e
BERTopic+LR), combinados por um meta-modelo de regressão logística. O protocolo de
treino, validação e a decisão do modelo final **já foram definidos** pelo time de
dados (Mayara, Rayssa e Rafaella) num desafio paralelo de ML; este diretório só
reproduz o fit final e persiste os artefatos que faltavam (eles nunca tinham sido
salvos em disco — só os scripts e as métricas).

## Dataset

O dataset **não está neste repositório** (datasets não vão para o git). É o
**FakeRecogna** (notícias em português rotuladas Fake/Real), já tratado e
deduplicado pelo time de dados: `NoRemovalWords_tratada_dedup.csv` (11.670 linhas,
colunas `Titulo`, `Noticia`, `Rotulo`, entre outras). Peça o arquivo a quem fez o
desafio de ML e informe o caminho local com `--dataset-csv`.

**Importante**: os modelos usam **somente a coluna `Noticia`**. Uma auditoria de
vazamento de rótulo mostrou que `Titulo` traz o veredito escrito em ~64% das
notícias Fake (ex.: "É #FAKE: ...", "...#boato") — usar o título inflaria
artificialmente as métricas. Nenhuma outra coluna (`Categoria`, `Dominio`, `URL`,
`Autor`, `Data`, features estruturais etc.) é usada.

## Como rodar

```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r ../backend/requirements.txt   # ou só os pacotes de ML, ver abaixo
python treinar_e_exportar_stacking.py --dataset-csv /caminho/para/NoRemovalWords_tratada_dedup.csv
```

Isso treina os 5 modelos clássicos (rápido, segundos) e o BERTopic (mais caro: baixa
o modelo de embeddings `paraphrase-multilingual-MiniLM-L12-v2` do Hugging Face na
primeira execução — precisa de internet — e leva alguns minutos para o fit de
UMAP+HDBSCAN em ~9.300 documentos). Os artefatos são gravados em
`backend/app/ml_artifacts/`.

Para iterar rapidamente sem o BERTopic (não vale para a entrega final, o protocolo
exige os 6 modelos base):

```bash
python treinar_e_exportar_stacking.py --dataset-csv ... --skip-bertopic
```

## Decisão do modelo (resumo)

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
| bertopic (tópicos+LR) | 0.835 | 0.167 | 0.752 |
| soft voting | 0.990 | 0.043 | 0.958 |
| **stacking (meta-LR)** | **0.994** | **0.027** | **0.965** |

O stacking teve ganho de AUC e de Brier consistente (≥4/5 folds, IC95% > 0) contra
todos os modelos individuais — inclusive contra o SVM, que isoladamente já teria
IC95% de AUC não sobreposto ao do baseline. **Decisão final: Stacking (LR meta)**.
Detalhes completos (pesos, correlação entre modelos, gráficos) ficam só no material
de origem do time de dados (`modelos_outputs/stacking/decisao_modelo.md`), que não
faz parte deste repositório; os pesos finais usados pelo meta-modelo estão
hard-coded em `treinar_e_exportar_stacking.py::PESOS_META_FINAL` e replicados em
`backend/app/ml_artifacts/manifest.json`.

## Artefatos gerados

Em `backend/app/ml_artifacts/` (carregados por
`backend/app/adapters/ml_classifier.py::MLStackingClassifier`):

| arquivo | conteúdo |
|---|---|
| `baseline.joblib`, `svm.joblib`, `nb.joblib`, `char.joblib`, `gbm.joblib` | `Pipeline` do scikit-learn de cada modelo clássico, já ajustado |
| `bertopic_topic.pkl` | modelo `BERTopic` (tópicos), salvo com `bt.save(..., serialization="pickle")` |
| `bertopic_clf.joblib` | `Pipeline(StandardScaler + LogisticRegression)` sobre as features de tópico |
| `meta_model.joblib` | `LogisticRegression` do meta-modelo (pesos fixos, não re-treinados) |
| `manifest.json` | proveniência: ordem dos modelos base, modelo de embeddings, pesos do meta-modelo, data de treino, origem dos dados |

Os pesos do SBERT (`paraphrase-multilingual-MiniLM-L12-v2`) não são persistidos —
são baixados/cacheados pelo Hugging Face na primeira execução, tanto no treino
quanto no backend em produção.

## ⚠️ Limitação conhecida: pré-processamento do texto de entrada (2026-10-12)

A coluna `Noticia` do FakeRecogna **já vem lematizada/normalizada na fonte**
(ex.: "saúde" → "saudar", "fila" → "filar", "multa" → "multar", artigos
("a"/"as"/"os"/"um"...) colapsados para "o"). Os 6 modelos foram treinados em
cima dessa forma, não em texto natural.

O `MLStackingClassifier` (`backend/app/adapters/ml_classifier.py`) hoje recebe o
texto **da forma como a extensão captura da página, sem nenhum pré-processamento**.
Isso causa uma incompatibilidade de vocabulário: testei a API com texto real
(neutro e até notícia formal de saúde) e o modelo deu "suspeito" com 80-99% de
confiança de forma sistemática — mas, ao mandar uma linha do próprio dataset
(já na forma lematizada, rótulo conhecido), ele acertou os dois casos (Real→confiável
99%, Fake→suspeito 98%). Ou seja: **o modelo e os pesos estão corretos**, falta só
replicar o pré-processamento de texto que gerou a coluna `Noticia` antes de chamar
o classificador em produção.

Tentei aproximar com spaCy (`pt_core_news_sm` e `pt_core_news_lg`) e com o stemmer
RSLP do NLTK — nenhum dos dois reproduz o padrão observado (substantivos virando
verbo cognato: saúde→saudar, fila→filar, deputado→deputar). Isso não é lematização
nem stemming padrão; é algo customizado. **Quem souber qual ferramenta/script gerou
`FakeRecogna_no_removal_words.xlsx` original precisa confirmar** — a resposta certa
provavelmente está com quem montou essa base antes da limpeza (`tratamento/rodar_limpeza.py`
não faz essa transformação, ela já vem pronta no xlsx de origem).

Até isso ser resolvido, trate o percentual do `ml_stacking` como não confiável para
texto real da web (a API já inclui esse aviso nas `justifications` da resposta).
