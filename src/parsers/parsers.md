# Módulo Parser

## 1. Introdução

O Módulo Parser atua como um adaptador de domínio e tradutor bidirecional, sendo o primeiro estágio na cadeia de análise e o último na cadeia de geração.

Sua responsabilidade é desacoplar os formatos de log brutos (específicos de cada sistema) da lógica de geração de carga (que é agnóstica). Isso é alcançado através de duas operações principais:

1.  **Análise (Parse):** Converte um rastro bruto de um sistema-alvo (ex: logs do Redis `MONITOR` ou logs de acesso HTTP) para o **Formato de Evento Intermediário (FEI)**, que é a representação interna padronizada do Defigium.
2.  **Formatação (Format):** Realiza a operação inversa. Converte os eventos sintéticos (`FEIEvent`) gerados pelo Módulo Gerador de volta para uma string de log textual. O arquivo resultante, `synthetic_trace.log`, é então consumido pelo Módulo Executor.

## 2. Arquitetura e Implementação

A arquitetura do módulo é fundamentada nos padrões de projeto Strategy e Factory Method, permitindo que diferentes formatos de log sejam suportados de forma intercambiável.

### 2.1. Interface: `IParser`

A interface `IParser` define o contrato abstrato que todas as estratégias de parser concretas devem implementar. Ela exige três métodos:

* **`parse(file_path)`:** Responsável por ler um arquivo de log bruto, linha por linha, e retornar um iterador (`yield`) de objetos `FEIEvent` padronizados.
* **`format(event)`:** Recebe um único `FEIEvent` sintético e o formata em uma string de log textual, pronta para ser escrita no rastro sintético.
* **`generate_args(...)`:** Um método auxiliar invocado por Geradores estatísticos (como o `HeatmapGenerator`). Sua função é criar argumentos sintéticos realistas (ex: valores aleatórios para um `HMSET`) com base no `op_type` e `target` sorteados.

### 2.2. Fabrica: `ParserFactory`

A `ParserFactory` é responsável por instanciar a estratégia de parser correta com base no arquivo `config.yaml`. Ela isola o núcleo da ferramenta dos detalhes de implementação de cada parser.

## 3. Extensão

A arquitetura modular foi projetada especificamente para ser extensível, permitindo a adição de suporte a novos formatos de log (ex: MongoDB, PostgreSQL, HTTP).

Para adicionar um novo parser (ex: `MongoDbParser`):

1.  **Implementar a Interface:** Crie uma nova classe `MongoDbParser` em um novo diretório (ex: `src/parsers/mongodb/`). Esta classe deve herdar de `IParser` e implementar os três métodos abstratos (`parse`, `format`, `generate_args`).
2.  **Registrar na Fábrica:** Modifique o arquivo `src/parsers/factory.py` para importar e instanciar a nova classe `MongoDbParser` quando o `type` no arquivo de configuração for `mongodb` (conforme o exemplo comentado no código da fábrica).
3.  **Configurar:** A nova estratégia pode agora ser selecionada no arquivo `config.yaml` simplesmente definindo `parser: { type: mongodb }`.
