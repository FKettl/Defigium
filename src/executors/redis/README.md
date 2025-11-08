# Estrategia: RedisExecutorStrategy

## 1. Introducao

Esta é a implementação da estratégia `IExecutorStrategy` especializada em interagir com um servidor **Redis**.

Esta classe C++ é o *driver* de sistema-alvo para o Redis. Ela cumpre as três responsabilidades da interface `IExecutorStrategy`:

1.  **`parse_line(log_line)`:** Converte uma linha de log (no formato `MONITOR`) em um objeto `Task`. Esta função é usada pela *thread Manager*.
2.  **`connect(config)`:** Estabelece e gerencia a conexão com o servidor Redis usando a biblioteca `redis++`. Esta função é usada por cada *thread Worker*.
3.  **`execute(command)`:** Traduz o objeto `Command` genérico em uma chamada de API específica do `redis++` (ex: `m_redis_client->hmset(...)`). Esta função é usada por cada *thread Worker*.

## 2. Implementacao

### 2.1. Parsing (Log -> Task)

O método `parse_line` é projetado para analisar a sintaxe específica do log do `MONITOR` do Redis.

* **Regex Inicial:** Uma expressão regular (`line_splitter_regex`) divide a linha nos três componentes: `timestamp`, `[client_id]` e a `string de comando completa`.
* **Parser de Comando Customizado:** Assim como o `RedisParser` (Python), esta classe usa um parser (`parse_command_args`) que entende a regra de separação por `" "` (aspas e espaço), tratando os argumentos como strings brutas.
* **Mapeamento de Atributos:** O parser preenche a struct `Task`, que contém o `original_timestamp` e o `Command` (com `op_type`, `target` e `additional_data["raw_args"]`).

### 2.2. Conexao

O método `connect` é chamado uma vez por *thread worker*. Ele lê o `host` e `port` do nó de configuração (`executor_config`).

Crucialmente, ele configura *timeouts* de conexão e *socket* (ex: 1 segundo). Isso é vital para garantir que a *thread worker* não fique bloqueada indefinidamente em uma operação de rede (especialmente no destrutor `m_redis_client.reset()`), permitindo que o programa finalize corretamente.

### 2.3. Execucao de Comandos

O método `execute` é o núcleo da *thread worker*. Ele implementa um `switch` (usando `if-else if`) sobre o `command.op_type` para traduzir a tarefa genérica em uma chamada de biblioteca `redis++`.

* **Tradução de Argumentos:** A lógica de `execute` é responsável por formatar os argumentos. Por exemplo, para `HMSET`, ela converte o `std::vector<std::string>` de `raw_args` em um `std::vector<std::pair<std::string, std::string>>` exigido pela biblioteca `redis++`.

### 2.4. Comandos Suportados

A implementação atual suporta um subconjunto de comandos focado na carga de trabalho do YCSB (Workload A):

* `HMSET`
* `SET`
* `GET`
* `HGETALL`
* `DEL`
* `ZADD`

A adição de novos comandos (ex: `HGET`) exigiria a adição de um novo bloco `else if (command.op_type == "HGET")` dentro do método `execute`.

## 3. Dependencias

Esta estratégia introduz dependências C++ externas que devem ser vinculadas durante a compilação:

* **`redis++`:** A biblioteca cliente C++ para Redis.
* **`hiredis`:** A biblioteca C de baixo nível da qual o `redis++` depende.

## 4. Compilacao

Para compilar o Executor com esta estratégia, o `Makefile` deve ser usado com o alvo `redis`:

```bash
make redis
