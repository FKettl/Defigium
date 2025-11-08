# Módulo Gerador

## 1. Introdução

O Módulo Gerador é o núcleo lógico do *pipeline* do Defigium. Sua responsabilidade é transformar o rastro original, já processado pelo `IParser` em uma lista de eventos `FEIEvent`, em um novo **rastro sintético**, também como uma lista de `FEIEvent`.

Este módulo encapsula as diferentes técnicas de geração de carga, que podem variar de uma simples replicação a modelos estatísticos complexos. O processo de geração é conceitualmente dividido em duas sub-etapas:

1.  **Caracterização (Análise):** A estratégia analisa a sequência de eventos `FEIEvent` de entrada para construir um modelo interno de carga de trabalho (ex: distribuições de probabilidade, matrizes de transição).
2.  **Síntese (Geração):** A estratégia utiliza o modelo construído para gerar uma nova sequência de eventos `FEIEvent`, com parâmetros como a duração da simulação.

## 2. Arquitetura e Implementação

A arquitetura segue os padrões **Strategy** e **Factory Method** para permitir que diferentes algoritmos de geração sejam selecionados e executados de forma intercambiável.

### 2.1. Interface: `IGenerator`

A interface `IGenerator` define o contrato abstrato para todas as estratégias de geração. Ela exige a implementação de um único método principal:

* **`generate(events)`:** Recebe a lista de `FEIEvent` do rastro original e retorna uma *nova* lista de `FEIEvent` sintéticos, processados de acordo com a lógica da estratégia.

### 2.2. Fabrica: `GeneratorFactory`

A `GeneratorFactory` é responsável por instanciar a estratégia de geração correta com base no `config.yaml`.

Um detalhe arquitetural importante é que a fábrica realiza a **Injeção de Dependência**: ela passa a instância do `IParser` (criada anteriormente) para o construtor das estratégias de geração que dela necessitam (como o `HeatmapGenerator`). Isso é crucial para que o gerador possa invocar o método `parser.generate_args()` ao sintetizar novos eventos de escrita.

## 3. Extensão

Para adicionar uma nova estratégia de geração (ex: `MarkovGenerator`):

1.  **Implementar a Interface:** Crie uma nova classe `MarkovGenerator` em um novo diretório (ex: `src/generators/markov/`). A classe deve herdar de `IGenerator` e implementar o método `generate`.
2.  **Registrar na Fábrica:** Modifique o arquivo `src/generators/factory.py` para importar e instanciar a nova classe `MarkovGenerator` quando o `type` no arquivo de configuração for `markov`.
3.  **Configurar:** A nova estratégia pode agora ser selecionada no arquivo `config.yaml` definindo `generator: { type: markov }`.
