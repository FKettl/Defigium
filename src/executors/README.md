# Modulo Executor

## 1. Introducao

O Módulo Executor é o estágio final do *pipeline* do Defigium, responsável por transformar o rastro sintético (`synthetic_trace.log`) em interações concretas com um sistema-alvo.

Diferente dos módulos de análise (Python), o Executor é implementado inteiramente em **C++** para garantir alto desempenho e controle preciso sobre o tempo. Sua principal responsabilidade é a execução com fidelidade temporal: ele não apenas executa as operações, mas o faz respeitando a cadência e o ritmo exatos definidos no arquivo de rastro.

## 2. Arquitetura e Implementacao

A arquitetura do Executor é baseada em um padrão gerente-Trabalhador multithreaded para alcançar alta concorrência e precisão.

### 2.1. Thread 'main' (Manager)

A thread `main` atua como o Gerente, orquestrando a execução. Suas funções são:

* **Configuração:** Carrega o `config.yaml` (usando `yaml-cpp`) para obter o caminho do rastro, o número de *workers* e as configurações do sistema-alvo.
* **Criação dos Workers:** Inicia um *pool* de threads (`std::thread`) e cria uma fila segura (`ThreadSafeQueue`) para cada *worker*.
* **Parsing e Despacho:** Lê o `synthetic_trace.log` linha por linha. Para cada linha:
    1.  Utiliza uma instância do `IExecutorStrategy` (criada pela `ExecutorFactory`) para invocar `parse_line`, convertendo a string de log em um objeto `Task`.
    2.  Calcula o `target_time` absoluto da operação, somando o delta de tempo do rastro ao tempo de início.
    3.  Empurra a `Task_Worker` (contendo o `target_time` e o `Command`) para a fila de um worker, em round-robin.
* **Finalização:** Após despachar todas as tarefas, envia uma tarefa de finalização para cada worker e aguarda a conclusão (`join()`).

### 2.2. Threads 'worker_function' (Workers)

As *threads worker* são as responsáveis pela execução real das operações. Cada *worker* opera de forma independente:

* **Inicialização:** Cria sua *própria instância* da `IExecutorStrategy` (via `ExecutorFactory`).
* **Conexão:** Invoca o método `connect()` da sua estratégia para estabelecer uma conexão independente com o sistema-alvo.
* **Loop de Execução:** Entra em um loop onde:
    1.  Aguarda por uma `Task_Worker` em sua fila.
    2.  Verifica se é a finalização para encerrar.
    3.  **Execução Temporizada:** Usa `std::this_thread::sleep_until(task.target_time)` para pausar a thread até o exato nanossegundo agendado para o disparo.
    4.  No momento exato, invoca `executor->execute(task.command)` para realizar a operação contra o sistema-alvo.
* **Relatório:** Reporta o sucesso ou falha da operação incrementando contadores atômicos globais.

### 2.3. Interface: `IExecutorStrategy`

Assim como os outros módulos, o Executor usa o Padrão Strategy. A interface `IExecutorStrategy` define o contrato que cada sistema-alvo deve implementar:

* **`connect(config)`:** Lógica para se conectar ao sistema-alvo.
* **`execute(command)`:** Lógica para traduzir o `Command` genérico em uma chamada de biblioteca específica.
* **`parse_line(log_line)`:** Lógica para a thread *Manager* usar, convertendo uma linha de log de volta em um `Task`.

## 3. Extensao e Compilacao

Adicionar suporte a um novo sistema-alvo (ex: HTTP) é um processo que envolve C++ e o sistema de *build*.

### 3.1. Compilação Condicional

O Defigium utiliza **compilação condicional** para manter o executável final enxuto. A `ExecutorFactory` só inclui o código de uma estratégia (ex: `RedisExecutorStrategy`) se uma *flag* de pré-processador (ex: `BUILD_REDIS_STRATEGY`) estiver definida.

### 3.2. Makefile

O `Makefile` orquestra esse processo. Para adicionar uma nova estratégia (ex: `http`):

1.  **Código:** O desenvolvedor implementa `HttpExecutorStrategy` e a registra na `factory.cpp` dentro de um bloco `#ifdef BUILD_HTTP_STRATEGY`.
2.  **Makefile:** Um novo alvo é adicionado ao `Makefile` (ex: `http:`).
3.  **Flags de Build:** Esse alvo deve passar duas informações cruciais ao compilador:
    * `CXXFLAGS`: A *flag* de compilação (ex: `-DBUILD_HTTP_STRATEGY`).
    * `LIBS`: As bibliotecas externas necessárias (ex: `-lcurl`).

O usuário então compila a versão desejada (ex: `make redis` ou `make http`), e o executável final conterá apenas o código daquela estratégia.

### 3.3. Dependências

As dependências principais do Executor C++ são:

* `yaml-cpp`: Para ler o `config.yaml`.
* `pthread`: Para *multithreading*.
* Bibliotecas de Cliente (condicionais):
    * **Redis:** `redis++` e `hiredis`.
    * **(Exemplo) HTTP:** `curl`.
