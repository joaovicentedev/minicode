Trabalho Prático de Redes Neurais
MiniCode: construindo e especializando um agente de programação com LLMs
Trabalho individual ou em duplas

Cada dia de atraso incorre em uma perda de um ponto, com um máximo de dois dias de atraso.

1. Visão geral
Neste trabalho vocês deverão construir uma versão simplificada de um agente de programação semelhante ao Claude Code.

O sistema, denominado neste enunciado de MiniCode, receberá uma solicitação em linguagem natural e deverá modificar um projeto de software para atender à solicitação.

Exemplo:

$ minicode

> Adicione ao projeto uma rota /health que retorne:
> {"status": "ok"}
O MiniCode deverá analisar o projeto, compreender a tarefa, produzir uma especificação, planejar a solução, modificar os arquivos necessários, executar testes e verificar se a implementação está correta.

A atividade será desenvolvida em duas partes:

Etapa	Entrega	Objetivo principal
Parte 1 = Trabalho 1	15 dias	Construir o agente e seu harness
Parte 2 = Trabalho 2	30 dias	Treinar/especializar uma LLM e avaliar experimentalmente seu impacto
A Parte 1 possui maior ênfase em agentes e engenharia do sistema.

A Parte 2 possui maior ênfase em Redes Neurais, treinamento, fine-tuning e experimentação.

2. Objetivos de aprendizagem
Ao final do trabalho, espera-se que o aluno consiga compreender na prática:

funcionamento de LLMs dentro de sistemas agentes;

inferência utilizando modelos de linguagem;

contexto e janela de contexto;

geração estruturada;

uso de ferramentas por LLMs;

arquiteturas agentes;

Spec-Driven Development;

Harness Engineering;

Agent Hardness;

ciclos de feedback;

fine-tuning de LLMs;

LoRA e QLoRA;

criação de datasets;

treinamento e validação;

generalização;

métricas experimentais;

estudos de ablação.

O objetivo não é reproduzir todas as funcionalidades do Claude Code.

O objetivo é compreender quais componentes são necessários para transformar uma LLM em um agente capaz de realizar uma tarefa de programação verificável.

3. Infraestrutura disponibilizada
O professor fornecerá um endpoint para acesso a um modelo Qwen de aproximadamente 14 bilhões de parâmetros.

Este modelo poderá ser utilizado durante todo o desenvolvimento do agente.

Uma interação simplificada será semelhante a:

MiniCode
    |
    v
Qwen-14B
    |
    v
resposta / tool call
O endpoint deverá ser tratado como infraestrutura disponibilizada pela disciplina.

Credenciais fornecidas pelo professor:

não poderão ser publicadas no GitHub;

não poderão aparecer em commits;

deverão ser armazenadas em variáveis de ambiente ou mecanismos equivalentes.

Por exemplo:

export MINICODE_API_KEY=...
4. O problema
O MiniCode deverá receber uma tarefa como:

> Crie uma função que calcule o fatorial de um número.
ou:

> Adicione paginação ao endpoint GET /users.
ou:

> Os testes de UserService estão falhando. Descubra e corrija o problema.
O agente deverá então operar sobre um projeto real.

Não será considerado suficiente simplesmente enviar a solicitação para uma LLM e salvar a resposta.

Por exemplo, isto não caracteriza um agente adequado para o trabalho:

task = input()

answer = llm(task)

open("solution.py", "w").write(answer)
O MiniCode deverá possuir um ciclo explícito de raciocínio operacional:

TASK
  |
  v
SPEC
  |
  v
PLAN
  |
  v
EXECUTE
  |
  v
VERIFY
  |
  +-------- erro --------+
  |                      |
  |                      v
  |                    REPAIR
  |                      |
  +----------------------+
  |
 sucesso
  |
  v
DONE
5. Spec-Driven Development
Uma característica obrigatória do trabalho será o uso de Spec-Driven Development.

O agente não poderá iniciar diretamente a implementação.

A primeira etapa deverá transformar a solicitação do usuário em uma especificação.

Por exemplo:

Usuário:

"Adicione paginação ao endpoint GET /users."
O agente poderia produzir:

# Specification

## Objective

Adicionar paginação ao endpoint GET /users.

## Parameters

page:
- inteiro
- mínimo: 1
- default: 1

page_size:
- inteiro
- mínimo: 1
- máximo: 100
- default: 20

## Acceptance Criteria

GET /users?page=2&page_size=10

deve retornar no máximo 10 usuários.

page_size > 100 deve ser rejeitado.
A especificação deverá conter critérios de aceitação verificáveis.

Depois da especificação, deverá ser produzido um plano.

Exemplo:

1. localizar implementação do endpoint /users
2. localizar camada de persistência
3. modificar API para aceitar page e page_size
4. modificar consulta ao banco
5. adicionar testes
6. executar testes
6. Agent Hardness
Para fins deste trabalho, chamaremos de Agent Hardness a transformação de regras importantes do agente em restrições programáticas verificáveis.

Há uma diferença importante entre:

"Por favor execute os testes antes de terminar."
e:

O programa não permite a transição VERIFY -> DONE
se os testes obrigatórios não tiverem sido executados.
O primeiro caso é uma instrução para a LLM.

O segundo é uma propriedade do sistema.

O MiniCode deverá possuir mecanismos desse segundo tipo.

Exemplos:

SPEC inexistente
     |
     X
IMPLEMENT
O sistema deverá impedir essa transição.

Da mesma forma:

TESTS FAILED
     |
     X
DONE
O agente não poderá declarar sucesso nessa situação.

7. Harness Engineering
A LLM será apenas um componente do sistema.

O aluno deverá construir um harness ao redor dela.

Uma possível arquitetura é:

                 +-------------+
                 |    USER     |
                 +------+------+
                        |
                        v
                 +-------------+
                 | ORCHESTRATOR|
                 +------+------+
                        |
                        v
                 +-------------+
                 |     LLM     |
                 +------+------+
                        |
       +----------------+----------------+
       |                |                |
       v                v                v
  READ FILE        WRITE FILE       RUN TESTS
       |                |                |
       +----------------+----------------+
                        |
                        v
                     RESULT
                        |
                        v
                       LLM
O harness será responsável por disponibilizar ferramentas, controlar a execução, aplicar restrições e retornar feedback ao modelo.

8. Ferramentas mínimas
O agente deverá possuir, no mínimo, capacidades equivalentes a:

list_files
read_file
write_file
run_tests
É recomendável também implementar funcionalidades como:

search_code
replace_text
create_file
git_diff
run_command
Não é necessário utilizar exatamente esses nomes.

O importante é existir separação explícita entre:

LLM
e

ações executadas pelo sistema.
9. Segurança
Uma LLM não deverá possuir acesso irrestrito ao computador.

O MiniCode deverá possuir mecanismos mínimos de segurança.

Por exemplo:

Agent
  |
  v
Command Validator
  |
  +------ permitido ------> Execute
  |
  +------ proibido -------> Reject
O sistema deverá impedir operações perigosas ou fora do escopo do projeto.

Exemplos:

sudo ...
rm -rf /
shutdown
reboot
O agente também não deverá modificar arbitrariamente arquivos fora do diretório do projeto.

Deverá existir limite de iterações para impedir loops infinitos.

PARTE 1
10. MiniCode v1
Prazo: 15 dias
Na primeira entrega vocês deverão implementar um agente funcional utilizando o Qwen-14B disponibilizado pelo professor.

A implementação deverá possuir obrigatoriamente:

Solicitação
    |
    v
Specification
    |
    v
Plan
    |
    v
Implementation
    |
    v
Tests
    |
    +---- failure ----> Repair
    |
    v
Result
11. Máquina de estados
Recomenda-se fortemente implementar explicitamente estados como:

RECEIVED

SPECIFIED

PLANNED

IMPLEMENTING

VERIFYING

REPAIRING

DONE

FAILED
As transições entre estados deverão ser controladas pelo programa.

Por exemplo:

SPECIFIED -> IMPLEMENTING
não deverá ser permitido sem passar por:

PLANNED
Esse controle constitui uma das formas de Agent Hardness avaliadas no trabalho.

12. Repair Loop
Caso a implementação produza um erro, o erro deverá retornar ao modelo.

Exemplo:

LLM
 |
 v
PATCH
 |
 v
pytest
 |
 v
FAILED
 |
 v
erro + contexto
 |
 v
LLM
 |
 v
novo PATCH
Esse ciclo poderá continuar até:

SUCCESS
ou até atingir um número máximo de tentativas.

13. Estado e rastreabilidade
O agente deverá registrar sua execução.

Por exemplo:

.minicode/

    specification.md
    plan.md
    actions.jsonl
    state.json
Deverá ser possível descobrir posteriormente:

qual tarefa foi recebida;

qual especificação foi produzida;

qual plano foi criado;

quais ferramentas foram chamadas;

quais arquivos foram alterados;

quais testes foram executados;

quais erros ocorreram;

quantas tentativas foram realizadas;

qual foi o resultado final.

14. Avaliação da Parte 1
O grupo deverá preparar um conjunto de pequenas tarefas de programação para avaliar o agente.

As tarefas deverão incluir diferentes tipos de atividade, como:

implementação de função

correção de bug

modificação de API

criação de testes

validação de dados

pequena refatoração
O sucesso de uma tarefa deverá ser determinado preferencialmente por testes automatizados.

A principal métrica será:

[
TaskSuccessRate =
\frac{\text{tarefas concluídas corretamente}}
{\text{total de tarefas}}
]

Também deverão ser registrados:

[
FirstAttemptSuccess
]

[
AverageIterations
]

[
AverageLLMCalls
]

Opcionalmente poderão ser registrados tempo e quantidade de tokens.

15. Tarefas inéditas
Parte da avaliação será realizada em tarefas não utilizadas durante o desenvolvimento.

O professor poderá fornecer projetos ou tarefas contendo testes não conhecidos previamente pelos grupos.

O objetivo é avaliar generalização, e não apenas adaptação do agente aos exemplos utilizados durante seu desenvolvimento.

16. Entrega da Parte 1
A entrega deverá conter:

Repositório GitHub
Contendo código, testes e documentação.

README
Explicando:

arquitetura;

fluxo do agente;

ferramentas implementadas;

Spec-Driven Development;

Agent Hardness;

mecanismos de segurança;

repair loop;

como executar.

Vídeo
O vídeo deverá mostrar pelo menos uma execução completa:

prompt
 -> spec
 -> plan
 -> alteração de código
 -> execução
 -> erro, se houver
 -> correção
 -> testes
 -> resultado
PARTE 2
17. Especializando uma LLM
Prazo: 30 dias a partir do início do trabalho
Na segunda parte o grupo deverá estudar uma pergunta experimental:

É possível especializar uma LLM pequena para executar melhor uma função específica dentro do agente?

Agora o foco principal passa a ser o conteúdo de Redes Neurais.

18. Hipótese experimental
Antes de realizar o treinamento, o grupo deverá definir claramente uma hipótese.

Exemplo:

O fine-tuning de uma LLM pequena para seleção de ferramentas aumentará a acurácia de escolha da próxima ação do agente.

ou:

O fine-tuning de uma LLM pequena para geração de especificações aumentará o atendimento aos critérios de aceitação.

ou:

O fine-tuning permitirá que um modelo de 1B parâmetros produza planos comparáveis aos do Qwen-14B nessa tarefa específica.

A Parte 2 deverá tentar responder experimentalmente à hipótese proposta.

19. Escolha de UMA tarefa para fine-tuning
Cada grupo deverá escolher uma função específica do agente.

Exemplos:

Geração de especificação
task
 |
 v
LLM
 |
 v
specification
Planejamento
task + repository context
 |
 v
LLM
 |
 v
plan
Tool selection
agent state
 |
 v
LLM
 |
 v
next tool
Error repair
code + test error
 |
 v
LLM
 |
 v
proposed correction
Patch generation
task + code
 |
 v
LLM
 |
 v
patch
O grupo não precisa treinar uma LLM para executar o agente completo.

Especializar corretamente uma função limitada é preferível a tentar treinar todo o sistema de forma superficial.

20. Modelo
Deverá ser escolhido um modelo aberto que possa ser treinado utilizando os recursos disponíveis no Google Colab.

Sugere-se utilizar modelos aproximadamente entre:

0.5B e 3B parâmetros
dependendo da disponibilidade de memória.

21. Fine-tuning
O treinamento deverá utilizar técnicas adequadas ao cenário de recursos limitados.

São esperadas técnicas como:

LoRA
ou:

QLoRA
O aluno deverá compreender e ser capaz de explicar:

[
W' = W + \Delta W
]

com:

[
\Delta W = BA
]

onde:

[
A \in \mathbb{R}^{r \times d}
]

e:

[
B \in \mathbb{R}^{d \times r}
]

com:

[
r \ll d
]

Deverá ser discutido por que técnicas como LoRA reduzem o número de parâmetros treináveis.

22. Dataset
O grupo deverá criar ou adaptar um dataset adequado à tarefa escolhida.

O Qwen-14B disponibilizado pelo professor poderá ser utilizado como teacher model para auxiliar na criação de exemplos.

Exemplo:

tarefas
   |
   v
Qwen-14B
   |
   v
respostas candidatas
   |
   v
filtragem / validação
   |
   v
dataset
A geração automática pelo teacher não elimina a necessidade de verificar a qualidade dos dados.

O grupo deverá documentar:

origem dos dados

processo de geração

processo de filtragem

formato

quantidade de exemplos

train split

validation split

test split
23. Separação dos dados
O conjunto de teste não poderá ser utilizado durante o treinamento.

A divisão deverá ser semelhante a:

DATASET
 |
 +---- TRAIN
 |
 +---- VALIDATION
 |
 +---- TEST
O objetivo é medir capacidade de generalização.

24. Experimento principal
A comparação obrigatória será:

MESMO MODELO
antes e depois do fine-tuning.

Portanto:

Modelo Base
     versus
Modelo Fine-Tuned
Essa é a comparação fundamental para determinar se o treinamento trouxe ganho.

O Qwen-14B disponibilizado pelo professor deverá ser utilizado como referência adicional quando fizer sentido.

Assim, uma comparação típica será:

Modelo	Papel
Modelo pequeno original	baseline
Mesmo modelo + LoRA/QLoRA	experimento
Qwen-14B	referência
25. Avaliação local e avaliação end-to-end
O modelo deverá ser avaliado em dois níveis.

Nível 1 — tarefa especializada
Exemplo para seleção de ferramentas:

[
Accuracy =
\frac{\text{tool calls corretas}}
{\text{total de exemplos}}
]

Nível 2 — agente completo
Depois o modelo deverá ser inserido no MiniCode.

Deverá ser investigado se sua utilização altera:

[
TaskSuccessRate
]

do agente.

Isso permitirá observar uma diferença importante:

Melhorar uma métrica de modelo não necessariamente melhora o sistema completo.

26. Estudo de ablação
Cada grupo deverá realizar uma ablação simples.

Exemplos:

com Spec
versus
sem Spec
ou:

com Repair Loop
versus
sem Repair Loop
ou:

prompt:
"execute os testes"

versus

hard gate:
DONE somente se testes passarem
A ablação deverá responder:

Esse componente realmente contribui para o desempenho do agente?

27. Resultados
Os resultados deverão ser apresentados quantitativamente.

Por exemplo:

Sistema	Task Success
Qwen + agente simples	52%
+ Spec	64%
+ Hard Gates	72%
+ Repair Loop	81%
ou, para o treinamento:

Modelo	Accuracy
modelo base	61%
modelo fine-tuned	84%
Qwen-14B	88%
Os números acima são apenas exemplos.

28. Notebook
O treinamento deverá ser entregue em notebook executável no Google Colab.

Por exemplo:

notebooks/

    train.ipynb
O notebook deverá conter:

carregamento do dataset

tokenização

modelo

configuração LoRA/QLoRA

treinamento

loss de treinamento

loss de validação

inferência

avaliação
Sempre que possível, apresentar gráficos como:

[
TrainingLoss \times Epoch
]

e:

[
ValidationLoss \times Epoch
]

29. Integração final
O sistema final poderá possuir uma arquitetura semelhante a:

                         USER
                           |
                           v
                    ORCHESTRATOR
                           |
           +---------------+---------------+
           |                               |
           v                               v
  modelo especializado                 Qwen-14B
           |                               |
           +---------------+---------------+
                           |
                           v
                         TOOLS
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
           FILES         TESTS          GIT
O modelo treinado poderá assumir apenas a função para a qual foi especializado.

30. Entrega final
A entrega de 30 dias deverá conter:

GitHub

MiniCode completo

notebook de treinamento

dataset ou script de geração

experimentos

resultados

ablação

vídeo
Os pesos do modelo não precisam ser armazenados diretamente no GitHub.

31. Estrutura sugerida
minicode/
│
├── README.md
├── pyproject.toml
│
├── src/
│   ├── agent/
│   ├── llm/
│   ├── tools/
│   ├── spec/
│   ├── evaluator/
│   └── cli/
│
├── tests/
│
├── experiments/
│
├── datasets/
│
├── notebooks/
│   └── train.ipynb
│
├── docs/
│   └── architecture.md
│
└── AI_USAGE.md
32. Uso de Claude Code, Codex, Copilot e outras IAs
O uso de ferramentas de desenvolvimento assistido por IA é permitido e incentivado.

Podem ser utilizadas, entre outras:

Claude Code

Codex

GitHub Copilot

ChatGPT
Entretanto:

O aluno continua sendo responsável por todo o código entregue.

O aluno deverá ser capaz de explicar:

arquitetura;

código;

prompts;

ferramentas;

treinamento;

dataset;

resultados experimentais.

O arquivo:

AI_USAGE.md
deverá descrever brevemente como ferramentas de IA foram utilizadas durante o desenvolvimento.

Não é necessário registrar cada prompt individualmente.

33. Reprodutibilidade
Outro aluno deverá conseguir:

git clone
seguir o README e executar o projeto.

Dependências deverão ser declaradas adequadamente.

Exemplo:

pyproject.toml
ou:

requirements.txt
O notebook de treinamento também deverá conter as dependências necessárias.

34. Critérios de avaliação
Parte 1 — 40%
Critério	Peso
agente funcional	10%
Spec-Driven Development	7%
Agent Hardness	7%
ferramentas e harness	6%
verification + repair loop	5%
arquitetura, testes e documentação	5%
Parte 2 — 60%
Critério	Peso
formulação da hipótese	5%
dataset e metodologia	10%
implementação do treinamento	12%
compreensão de LoRA/QLoRA	8%
avaliação base × fine-tuned	10%
integração ao agente	5%
estudo de ablação	5%
análise dos resultados	5%
35. Penalizações importantes
Não será considerado adequado um sistema que apenas:

envia um prompt
        |
        v
recebe código
        |
        v
grava o arquivo
Também não será suficiente colocar todas as regras dentro de um grande system prompt.

Por exemplo:

"Planeje antes."
"Teste sempre."
"Não faça operações perigosas."
Essas instruções são úteis, mas o objetivo deste trabalho é construir mecanismos programáticos capazes de impor e verificar parte desse comportamento.

36. Cronograma
Dia 0
Liberação do enunciado e acesso ao Qwen-14B.

Dia 15
MiniCode v1
Esperado:

LLM
+
Tools
+
Spec
+
Plan
+
Hard Gates
+
Verification
+
Repair Loop
Dia 30
MiniCode v2
Acrescentando:

Dataset
+
Modelo pequeno
+
LoRA/QLoRA
+
Fine-tuning no Colab
+
Avaliação
+
Integração
+
Ablation Study
37. Questões que deverão ser respondidas ao final
Ao término do projeto, o grupo deverá ser capaz de responder, utilizando seus próprios experimentos:

1.
Quanto uma LLM consegue fazer sozinha e quanto depende do harness?

2.
Spec-Driven Development melhora a execução das tarefas?

3.
Há diferença entre pedir ao modelo que siga uma regra e impor essa regra programaticamente?

4.
O feedback dos testes permite que o agente corrija seus próprios erros?

5.
O fine-tuning realmente melhorou o modelo?

6.
O ganho observado no modelo especializado resultou em ganho no agente completo?

7.
Um modelo pequeno especializado pode competir com um modelo muito maior em uma tarefa restrita?

8.
Quais componentes tiveram maior impacto sobre a taxa de sucesso?

38. Ideia central do trabalho
Ao longo do projeto vocês irão trabalhar em três níveis diferentes:

              REDES NEURAIS
                   |
                   v
              Modelo / LLM
                   |
                   v
          Harness Engineering
                   |
                   v
           Agente de Software
Um bom sistema baseado em IA não depende apenas de possuir o maior modelo possível.

O desempenho final emerge da combinação de:

[
\boxed{
Sistema =
Modelo +
Dados +
Contexto +
Ferramentas +
Restrições +
Feedback
}
]

O desafio deste trabalho será investigar experimentalmente como esses componentes interagem para transformar uma LLM em um agente capaz de modificar software de maneira autônoma e verificável.