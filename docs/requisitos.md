# Requisitos Funcionais

## RF01 - Verificação de domínio
O sistema deve verificar se o domínio da página analisada está presente
na whitelist de fontes confiáveis definida pelo projeto.

Caso o domínio seja reconhecido, essa informação deve ser considerada
durante a análise do conteúdo.

Prioridade: MVP


## RF02 - Seleção manual de texto
A extensão deve permitir que o usuário selecione manualmente um trecho
de texto presente em uma página para solicitar sua análise.

Prioridade: MVP


## RF03 - Análise completa da página
A extensão deve permitir que o usuário solicite uma análise do conteúdo
textual principal da página atual.

O sistema deve extrair informações relevantes, como:

- título;
- conteúdo textual principal;
- URL;
- domínio da página.

Prioridade: MVP


## RF04 - Seleção de imagem
A extensão deve permitir que o usuário selecione uma imagem presente
na página para submetê-la a uma análise.

Prioridade: V2


## RF05 - Análise de manipulação de imagem
O sistema deve analisar uma imagem selecionada e retornar indícios de
possível:

- manipulação;
- edição;
- geração por inteligência artificial.

O resultado deve ser apresentado como uma estimativa ou indicação,
sem afirmar de forma absoluta que uma imagem é verdadeira ou falsa.

Prioridade: V2


## RF06 - Envio de conteúdo para a API
A extensão deve enviar para a API o conteúdo selecionado pelo usuário
ou extraído automaticamente da página.

A requisição deve conter, quando disponível:

- título;
- texto;
- URL;
- domínio;
- tipo de análise solicitada.

Prioridade: MVP


## RF07 - Análise linguística do conteúdo
O sistema deve analisar características do conteúdo textual que possam
auxiliar na identificação de desinformação.

A análise pode considerar:

- linguagem sensacionalista;
- tom emocional;
- ausência de fontes;
- afirmações sem evidências;
- alegações extraordinárias;
- contexto;
- estrutura textual;
- possíveis indicadores de viés.

Prioridade: MVP


## RF08 - Exibição de alertas
O sistema deve alertar o usuário quando forem identificados indícios de
conteúdo:

- suspeito;
- potencialmente desinformativo;
- ou não verificado.

O sistema não deve apresentar uma classificação probabilística como uma
determinação absoluta de verdade ou falsidade.

Prioridade: MVP


## RF09 - Recomendação de fontes
Após a análise de um conteúdo, o sistema deve permitir a busca por
informações relacionadas ao mesmo assunto em fontes pertencentes à
whitelist definida pelo projeto.

As fontes encontradas devem ser apresentadas ao usuário como referências
adicionais para comparação.

Prioridade: V2


## RF10 - Classificação por Machine Learning
Quando a classificação não puder ser realizada apenas pela verificação
do domínio, o sistema deve utilizar um modelo de Machine Learning para
analisar o conteúdo textual.

O resultado deve incluir:

- classificação;
- nível de confiança do modelo.

Prioridade: MVP


## RF11 - Fallback para análise por IA
Quando o nível de confiança do modelo de Machine Learning estiver abaixo
do limite definido pelo sistema, o conteúdo deve ser encaminhado para
um mecanismo adicional de análise.

Esse mecanismo poderá utilizar um modelo de IA generativa como uma
segunda análise.

Prioridade: MVP


## RF12 - Exibição do resultado da análise
O sistema deve apresentar ao usuário o resultado da análise de forma
compreensível.

A resposta deve conter, quando possível:

- classificação;
- justificativa;
- nível de confiança;
- método utilizado para a classificação;
- fontes adicionais relacionadas ao conteúdo.

Prioridade: MVP


## RF13 - Conteúdo não verificado
Quando não existirem informações suficientes para classificar um
conteúdo com confiança adequada, o sistema deve classificá-lo como
"não verificado".

O sistema não deve classificar automaticamente como falso um conteúdo
para o qual não existam evidências suficientes.

Prioridade: MVP

## RF14 - Identificação do método de análise
O sistema deve informar qual mecanismo foi utilizado para produzir
o resultado.

Exemplos:

- domínio presente na whitelist;
- classificação por Machine Learning;
- análise complementar por IA.

Prioridade: MVP


## RF15 - Exibição do nível de confiança
Quando a análise utilizar um modelo que produza uma medida de confiança,
o sistema deve apresentar essa informação ao usuário de forma clara.

Exemplo:

"Modelo de Machine Learning: confiança de 82%."

Prioridade: MVP


## RF16 - Solicitação manual de nova análise
O usuário deve poder solicitar novamente a análise do conteúdo atual
sem precisar recarregar toda a página.

Prioridade: V2


## RF17 - Feedback do usuário
O sistema deve permitir que o usuário informe se considera o resultado
da análise útil, incorreto ou inconclusivo.

Esse feedback poderá ser armazenado para avaliação futura do desempenho
do sistema.

Prioridade: V2


## RF18 - Histórico local de análises
A extensão poderá manter um histórico local das últimas análises
realizadas pelo usuário.

O histórico poderá apresentar:

- título;
- domínio;
- data da análise;
- classificação;
- nível de confiança.

Prioridade: V2


## RF19 - Explicação dos indicadores encontrados
O sistema deve informar quais características do conteúdo contribuíram
para a análise apresentada.

Exemplos:

- ausência de fontes identificáveis;
- linguagem altamente emocional;
- alegações extraordinárias sem evidência;
- domínio desconhecido;
- classificação do modelo de ML.

Prioridade: V2


## RF20 - Comparação com fontes confiáveis
Quando possível, o sistema deve apresentar conteúdos de fontes da
whitelist que tratem do mesmo assunto analisado.

O usuário deve conseguir acessar essas referências diretamente pela
extensão.

Prioridade: V2


## RF21 - Configuração da análise automática
A extensão deve permitir que o usuário escolha entre:

- análise automática ao abrir uma página;
- análise somente mediante solicitação;
- análise somente de conteúdo selecionado.

Prioridade: V2


## RF22 - Tratamento de falhas da API
Quando a API estiver indisponível ou ocorrer um erro durante a análise,
a extensão deve informar o usuário de maneira clara.

O sistema não deve apresentar uma falha de comunicação como resultado
de análise.

Prioridade: MVP


## RF23 - Tratamento de conteúdo insuficiente
Quando o texto selecionado ou extraído for insuficiente para uma
análise adequada, o sistema deve informar o usuário e solicitar uma
seleção maior ou outra forma de análise.

Prioridade: MVP


## RF24 - Identificação de fonte citada
Quando possível, o sistema deve identificar links, referências ou fontes
citadas dentro do conteúdo analisado.

Essas informações poderão ser utilizadas como apoio à avaliação da
confiabilidade do texto.

Prioridade: V2


## RF25 - Consulta manual de URL
O sistema poderá permitir que o usuário informe manualmente uma URL
para solicitar sua análise, mesmo sem estar navegando diretamente
na página.

Prioridade: Futuro


## RF26 - Visualização dos critérios da análise
A extensão deve permitir que o usuário consulte uma explicação resumida
sobre os critérios utilizados pelo sistema para produzir sua classificação.

Prioridade: MVP