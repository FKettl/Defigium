# Estrategia: HeatmapGenerator

## 1. Introdução

Seu objetivo é criar uma carga de trabalho sintética que mimetiza as características estatísticas do rastro original, permitindo a geração de cargas com durações arbitrárias.

O processo é dividido em duas fases: Caracterização e Síntese.

## 2. Fase de Caracterização (Análise)

Nesta fase, o gerador constrói um modelo de "heatmap" probabilístico do rastro original.

Ele divide a duração total do rastro em "fatias" ou intervalos, com base no parâmetro `percentage_interval`. Por exemplo, `percentage_interval: 1.0` divide a carga em 100 fatias de 1%.

Para cada fatia, ele aprende três distribuições de probabilidade distintas:

1.  **Composição de Comandos:** A probabilidade de cada `op_type` (ex: 50% HMSET, 40% HGETALL).
2.  **Popularidade de Recursos (Hotspots):** A probabilidade de cada `target` (chave) ser acessada, *dado* um `op_type` (ex: "user123" tem 30% dos acessos de `HGETALL` *nesta* fatia).
3.  **Ritmo da Carga (Tempos de Chegada):** A distribuição dos deltas de tempo (em milissegundos) entre eventos consecutivos.

## 3. Fase de Síntese (Geração)

Nesta fase, o gerador cria uma nova carga do zero, iterando até atingir o `simulation_duration_s` configurado.

A cada passo, ele primeiro determina em qual "fatia" do tempo simulado ele está, e então usa o modelo probabilístico daquela fatia para realizar uma **série de sorteios (`random.choices`)**:

1. Sorteia um `op_type`.
2. Sorteia um `target`.
3. Sorteia um `delta_ms` para determinar quando o *próximo* evento ocorrerá.

### 3.1. Gerenciamento de Estado

O gerador simula o ciclo de vida dos dados. Ele mantém um pool de chaves ativas para garantir que operações `READ` ou `DELETE` não sejam executadas em chaves que ainda não foram criadas.

### 3.2. Injeção de Dependência

Para operações de escrita, o gerador invoca o método `parser.generate_args()` (fornecido pelo `ParserFactory`) para criar argumentos sintéticos.

## 4. Mapeamento Temporal

O gerador pode criar cargas mais longas que o original usando o `time_expansion_strategy`:

* **`cyclic`:** Repete o padrão aprendido. Se o rastro original tem 10s e a simulação é de 30s, o padrão de 10s será executado 3 vezes.
* **`stretch`:** Alonga o padrão. Se o rastro tem 10s e a simulação é de 30s, cada "fatia" do modelo original durará 3x mais.

## 5. Configuração

Para usar esta estratégia, defina no arquivo `config.yaml`:

```yaml
generator:
  type: heatmap

  # (Obrigatório) Duração total da carga sintética em segundos
  simulation_duration_s: 120

  # (Opcional) Granularidade da análise. (Default: 5.0)
  # 1.0 = 100 fatias, 5.0 = 20 fatias, 50.0 = 2 fatias
  percentage_interval: 1.0

  # (Opcional) Estratégia para durações maiores. (Default: 'cyclic')
  # 'cyclic' = repete o padrão
  # 'stretch' = alonga o padrão
  time_expansion_strategy: cyclic
