# Defigium: Gerador de Carga Modular Baseado em Rastro

Defigium é uma ferramenta de *benchmark* modular projetada para gerar cargas de trabalho personalizadas e de alta fidelidade. Ela é fundamentada na análise de rastros (logs) reais e na aplicação de modelos estatísticos para capturar padrões de uso específicos.

A principal motivação da ferramenta é resolver a limitação dos *benchmarks* padronizados, que frequentemente falham em replicar a complexidade e as características dinâmicas de uma carga de trabalho de produção real.

## 1. Arquitetura e Fluxo de Trabalho

A arquitetura do Defigium é sua principal contribuição. É um *pipeline* de três estágios que utiliza uma abordagem **bilíngue (Python/C++)** para equilibrar flexibilidade de análise com desempenho de execução.

O fluxo de trabalho é o seguinte:

1.  **Módulo Parser (Python):** Este é o tradutor bidirecional. Ele lê um `Rastro Bruto` (ex: `trace.log`) e o converte para um Formato de Evento Intermediário (`FEIEvent`) padronizado.
2.  **Módulo Generator (Python):** Este é o núcleo lógico. Ele consome os eventos `FEIEvent`, aplica uma estratégia (como `Heatmap` ou `Replay`) para **caracterizar** o rastro e **sintetizar** uma nova carga de trabalho. O resultado é salvo como `Rastro Sintético` (ex: `synthetic_trace.log`).
3.  **Módulo Executor (C++):** Este é o motor de execução. Escrito em C++ para alto desempenho e precisão temporal, ele lê o `Rastro Sintético` e o executa contra um sistema-alvo (ex: Redis), respeitando a cadência e o ritmo exatos do modelo gerado.

## 2. Como Usar

A execução da ferramenta é um processo de duas etapas, orquestrado por um único arquivo `config.yaml`.

### 2.1. Pré-requisitos

* **Python:** Python 3.x, `pip` e a biblioteca `PyYAML`.
* **C++:** Um compilador C++17, `make`, e as bibliotecas de desenvolvimento para `yaml-cpp`.
* **Bibliotecas de Cliente:** As bibliotecas C++ para o sistema-alvo que você deseja compilar (ex: `libredis++-dev`, `libhiredis-dev` para Redis).

### 2.2. Configuração (`config.yaml`)

Toda a ferramenta é controlada pelo `config.yaml` na raiz do projeto. Ele define quais módulos usar e seus parâmetros.


### 2.3. Etapa 1: Geração (Python)

Primeiro, use o processo Python para analisar seu rastro e gerar o arquivo de carga sintética.
 ```bash
# 1. Execute o script principal de geração
python main.py
 ```

Isso executará o `Parser` e o `Generator` configurados e salvará o resultado no caminho `generator_log_file`.

### 2.4. Etapa 2: Execução (C++)

Em seguida, compile e execute o processo C++ para disparar a carga sintética contra seu sistema-alvo.

 ```bash
# 1. Navegue até o diretório do executor
cd src/executors

# 2. Compile o alvo C++ para a estratégia desejada (ex: redis)
make redis

# 4. Execute o binário compilado
./executor
 ```

O Executor C++ lerá o mesmo `config.yaml`, se conectará ao sistema-alvo e começará a despachar as operações do `synthetic_trace.log` com precisão temporal.

## 3. Extensibilidade

A ferramenta é projetada para ser extensível através dos padrões **Strategy** e **Factory Method**.

* **Novo Parser (Python):** Implemente a interface `IParser` (`src/parsers/interfaces`) e registre-a na `ParserFactory` (`src/parsers/factory.py`).
* **Novo Generator (Python):** Implemente a interface `IGenerator` (`src/generators/interfaces`) e registre-o na `GeneratorFactory` (`src/generators/factory.py`).
* **Novo Executor (C++):** Implemente a interface `IExecutorStrategy` (`src/executors/interfaces.h`), registre-a na `ExecutorFactory` (`src/executors/factory.cpp`) usando uma *flag* de compilação condicional, e adicione um novo alvo ao `Makefile`.

## 4. Citação

Este repositório contém a implementação prática do Trabalho de Conclusão de Curso de Felipe Backes Kettl (UFSC, 2025). Se você utilizar este trabalho, por favor, cite o documento original.
