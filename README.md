# Fake News Residência

Extensão de navegador (Chrome) que ajuda o usuário a avaliar a confiabilidade de textos na web, **sem substituir o pensamento crítico**. O sistema alerta e explica os critérios usados, mas não decreta o que é verdade ou mentira.

> Projeto do desafio **Fake News / Desinformação** da Residência em IA da UnB. Em desenvolvimento.

## Status

| Componente | Estado |
|---|---|
| Back-end: estrutura base e `/health` | concluído |
| Back-end: configuração, contrato da API e trustlist | em andamento |
| Back-end: endpoint `/analyze` e pipeline de análise | disponível localmente |
| Modelo de Machine Learning | stacking retreinado integrado (5 modelos; detalhes em [ml/README.md](ml/README.md)) |
| Análise complementar por IA (fallback) | a fazer |
| Extensão: análise via API local | disponível para teste |

## Modelo integrado

O artefato `backend/models/stacking.joblib` foi atualizado com os cinco modelos
retreinados em `challenge2v2` (baseline, SVM, Naive Bayes, n-gramas de caracteres
e GBM). O treino usa a base FakeRecogna 2.0 extrativa casada por tamanho:
17.648 textos no total, com 14.119 no desenvolvimento e 3.529 reservados fora do
ajuste. O backend normaliza o texto para minúsculas, remove o artefato `none` e
normaliza espaços, sem truncar a notícia.

Antes desta mudança, no Fake.br completo (7.200 textos, sem truncar, limiar 0,5), o modelo
treinado só na FakeRecogna tinha AUC 0,7553 e classificava 20,1% das notícias Reais como
suspeitas. O treino inclui agora também metade dos pares do Fake.br, para reduzir falsos positivos (notícias reais
classificadas como Fake). O backend usa três faixas: Real (p < 0,3), Incerto e Fake (p >= 0,7); só
Fake vira "suspeito". Nos pares de teste do Fake.br o stacking obteve AUC 0,961, com 4,9% dos
Reais como Fake e 81% dos Fake detectados. O teste não é independente (pares das mesmas fontes);
em fontes novas o desempenho é pior. Na validação interna agrupada por URL, a AUC foi 0,9855.
Use o resultado apenas como sinal de triagem, nunca como veredito factual automático. Detalhes em
[ml/README.md](ml/README.md).

## O que o projeto faz

Escopo do MVP, conforme os [requisitos](docs/requisitos.md):

- Análise de um trecho selecionado ou do conteúdo principal da página
- Verificação do domínio contra uma trustlist de fontes confiáveis
- Classificação do texto por Machine Learning, com nível de confiança
- Análise complementar por IA quando a confiança do modelo é baixa
- Classificação em **confiável**, **suspeito** ou **não verificado**
- Exibição do método usado, da confiança e dos critérios da análise
- Tratamento claro de falhas e de conteúdo insuficiente

## Como funciona

```mermaid
flowchart TD
    A[Extensão envia texto e URL] --> B{Texto suficiente?}
    B -- não --> E1[Erro: pedir seleção maior]
    B -- sim --> C{Domínio na trustlist?}
    C -- sim --> R1[Resultado por  trustlist]
    C -- não --> D[Classificador de ML]
    D --> F{Confiança acima do mínimo?}
    F -- sim --> R2[Resultado por ML]
    F -- não --> G[Análise complementar por IA]
    G --> R3[Resultado por IA ou não verificado]
```

Conteúdo sem evidência suficiente é classificado como **não verificado**, e nunca como falso. Uma falha de comunicação ou de um mecanismo de análise nunca é apresentada como resultado.

## Estrutura do repositório

```
.
├── backend/      API em Python (FastAPI) e artefato do modelo
├── extension/    Extensão do navegador
├── ml/           Treino e exportação do stacking de 5 modelos
├── docs/         Documentação e requisitos
└── .github/      Templates de issue e de pull request
```

## Como rodar o back-end

O modelo foi treinado com Python 3.14 e scikit-learn 1.9.1. Para reproduzir a
inferência local, use a mesma versão principal/secundária do Python e as versões
fixadas em `backend/requirements.txt`.

Requisitos: Python 3.14 e venv. O artefato `backend/models/stacking.joblib` é
necessário para iniciar o classificador; ele é incluído neste repositório.

```bash
git clone https://github.com/Withy-S/Fake_News_Residencia.git
cd Fake_News_Residencia/backend

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
uvicorn app.main:app --reload
```

A documentação interativa da API fica em http://127.0.0.1:8000/docs.

Para testar a extensão, em `chrome://extensions` ative o modo do desenvolvedor e
carregue `extension/` como extensão descompactada. Mantenha o backend rodando em
`http://127.0.0.1:8000`, abra uma notícia e use um dos modos de análise. O popup
mostra a probabilidade estimada pelo stacking; ela não é uma verificação factual.
Se o Chrome bloquear a requisição por CORS, copie o ID da extensão da página de
extensões e configure `FN_ALLOWED_ORIGINS=["chrome-extension://ID_DA_EXTENSAO"]`
em `backend/.env`, depois reinicie a API.

Para rodar os testes e o lint, sempre de dentro de `backend/`:

```bash
pytest -q
ruff check . && ruff format .
```

## Configuração

Os parâmetros ficam em variáveis de ambiente (arquivo `backend/.env`, criado a partir do `.env.example`). O `.env` nunca vai para o Git.

| Variável | Descrição | Padrão |
|---|---|---|
| `FN_MIN_TEXT_LENGTH` | Tamanho mínimo do texto para análise | `20` |
| `FN_MIN_CONFIDENCE` | Confiança mínima do modelo antes do fallback | `0.6` |
| `FN_FALLBACK_METHOD` | Mecanismo usado como fallback | `ai_fallback` |
| `FN_TRUSTED_DOMAINS` | trustlist de domínios, em JSON | `[]` |
| `FN_REQUEST_TIMEOUT_SECONDS` | Timeout das requisições | `10` |
| `FN_ALLOWED_ORIGINS` | Origens permitidas (CORS), em JSON | `[]` |

Os valores padrão são provisórios e podem mudar conforme as decisões do grupo.

## Endpoints

| Método | Rota | Estado |
|---|---|---|
| GET | `/api/v1/health` | disponível |
| POST | `/api/v1/analyze` | em desenvolvimento |

## Requisitos e escopo

Os requisitos funcionais e não funcionais estão em [`docs/requisitos.md`](docs/requisitos.md), com prioridade **MVP**, **V2** ou **Futuro**. Ficam para V2, entre outros: análise de imagens, recomendação de fontes, histórico local e feedback do usuário.

## Princípios

- As classificações são **estimativas automáticas**, sujeitas a erros, e não determinações de verdade.
- Coletar e transmitir apenas os dados necessários para a análise.
- Segredos e chaves nunca ficam no código-fonte.

## Como contribuir

1. Crie uma branch a partir da `main`: `feat/nome`, `fix/nome` ou `docs/nome`.
2. Use [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/): `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
3. Rode `pytest -q` e `ruff check .` antes de abrir o PR.
4. Prefira PRs pequenos e peça revisão a pelo menos uma pessoa do grupo.

## Equipe

Davi 
Mayara
Miti
Tayrine
Rafaella
Rayssa

## Licença

A definir.
