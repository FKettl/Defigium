# Estratégia: RedisParser

## 1. Introdução

Esta é a implementação da estratégia `IParser` especializada em interagir com o **Redis**, especificamente com o formato de log produzido pelo comando `MONITOR`.

O `RedisParser` atua como o adaptador de domínio para o Redis, cumprindo todas as responsabilidades da interface:

1.  **Parse (Leitura):** Converte um arquivo de log bruto do `MONITOR` em uma stream de eventos `FEIEvent`.
2.  **Format (Escrita):** Converte eventos `FEIEvent` sintéticos de volta para o formato de string do `MONITOR`, para que possam ser lidos pelo Módulo Executor.
3.  **Geração de Argumentos:** Fornece lógica para criar argumentos sintéticos (ex: dados aleatórios) para operações de escrita como `HMSET` e `SET`.

## 2. Implementação e Funcionalidades

### 2.1. Parsing (Log -> FEI)

O `RedisParser` é projetado para lidar com a sintaxe específica do `MONITOR`.

* **Regex Inicial:** Uma expressão regular (`_LOG_LINE_REGEX`) primeiro divide a linha nos três componentes principais: `timestamp`, `[client_id]` e a `string de comando completa`.
* **Parser de Comando Customizado:** os argumentos do `MONITOR` são separados por `" "` (aspas e espaço), mas podem conter espaços *dentro* das aspas. Um parser customizado (`_parse_command_args`) é usado para dividir corretamente a string de comando, respeitando os argumentos como strings brutas.
* **Mapeamento de Atributos:**
    * `op_type`: É extraído como o primeiro argumento (ex: "HMSET").
    * `target`: É extraído como o segundo argumento (a chave, ex: "user...").
    * `additional_data['raw_args']`: Todos os argumentos subsequentes (ex: 'field0', 'value123') são armazenados nesta lista.
* **Granularidade de Timestamp:** O `timestamp` lido do log é arredondado para a precisão definida no `config.yaml` (ex: 5 casas decimais).
* **Mapeamento Semântico:** O parser mapeia os comandos Redis para suas semânticas (`CREATE`, `READ`, `UPDATE`, `DELETE`) para auxiliar os modelos de geração.

### 2.2. Formatação (FEI -> Log)

A operação inversa, `format`, reconstrói a string do `MONITOR` a partir de um `FEIEvent`. Ele garante que todos os argumentos (`op_type`, `target` e `raw_args`) sejam devidamente encapsulados em aspas duplas e separados por espaços.

### 2.3. Geração de Argumentos Sintéticos

O método `generate_args` é usado pelo `HeatmapGenerator` quando ele precisa criar um evento de escrita do zero. O `RedisParser` sabe como criar dados sintéticos realistas para os comandos suportados:

* **HMSET:** Gera um número aleatório de pares `field/value` com dados aleatórios.
* **SET:** Gera uma string aleatória como valor.
* **ZADD:** Gera um `score` numérico aleatório e seleciona um `member` aleatório do *pool* de chaves disponíveis.

### 2.4. Comandos Suportados

Esta implementação **não** suporta todos os comandos do Redis e nem flags nos comandos. Ela é focada nos comandos relevantes para a carga de trabalho do YCSB (Workload A) utilizada nos experimentos.

Os comandos com lógica de parsing e semântica definidas são:
* `HMSET`
* `HGETALL`
* `ZADD`

Comandos de infraestrutura, como `CLIENT`, são explicitamente ignorados e filtrados durante o parsing.

## 3. Dependências

O `RedisParser` não requer nenhuma biblioteca externa (`pip install`). Ele utiliza apenas módulos da biblioteca padrão do Python.

## 4. Configuração

Para utilizar este parser, defina no arquivo `config.yaml`:

```yaml
parser:
  type: redis
