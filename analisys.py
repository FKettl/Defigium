import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from typing import Optional, Tuple, Dict
from scipy import stats
import powerlaw

LOG_REGEX = re.compile(
    r'^(?P<timestamp>\d+\.\d+)\s+'
    r'\[(?P<db>\d+)\s+(?P<client_ip>[^\]]+)\]\s+'
    r'"(?P<command>\w+)"'
    r'(?:\s+"(?P<target>[^"]*)")?'
    r'(?P<other_args>.*)?$'
)

def parse_log_to_dataframe(filepath: str) -> Optional[pd.DataFrame]:
    records = []
    print(f"Analisando o arquivo: {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                match = LOG_REGEX.match(line.strip())
                if match:
                    data = match.groupdict()
                    if data['target'] and data['command'].upper() != 'CLIENT':
                        ts = round(float(data['timestamp']), 5)
                        records.append({
                            'timestamp': ts,
                            'command': data['command'].upper(),
                            'target': data['target']
                        })

        if not records:
            print(f"AVISO: Nenhum registro válido com target encontrado em {filepath}.")
            return None

        df = pd.DataFrame(records)
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        df['inter_arrival_ms'] = df['timestamp'].diff() * 1000
        df = df.iloc[1:]
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {filepath}")
        return None
    except Exception as e:
        print(f"ERRO inesperado ao processar {filepath}: {e}")
        return None


def _calculate_chi2_and_cramer(contingency_table: np.ndarray) -> Tuple[float, float]:
    if contingency_table.sum() == 0:
        return np.nan, np.nan

    valid_rows = contingency_table.sum(axis=1) > 0
    valid_cols = contingency_table.sum(axis=0) > 0
    contingency_table = contingency_table[valid_rows, :][:, valid_cols]

    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 1:
         if (contingency_table.shape[1] > 0 and (contingency_table[:, 0] == contingency_table[:, 1]).all()):
             return 1.0, 0.0
         return np.nan, np.nan

    try:
        chi2_stat, chi_pvalue, dof, expected_freqs = stats.chi2_contingency(contingency_table)
        N = contingency_table.sum()
        k = min(contingency_table.shape)
        phi2 = chi2_stat / N
        k_minus_1 = k - 1
        if k_minus_1 == 0:
            cramers_v = np.nan if phi2 == 0 else np.sqrt(phi2)
            if (contingency_table[:, 0] == contingency_table[:, 1]).all():
                 cramers_v = 0.0
        else:
            cramers_v = np.sqrt(phi2 / k_minus_1)
        return chi_pvalue, cramers_v
    except Exception as e:
         if (contingency_table.shape[1] > 1 and (contingency_table[:, 0] == contingency_table[:, 1]).all()):
             return 1.0, 0.0
         return np.nan, np.nan


def calculate_similarity_metrics(df_inicial: pd.DataFrame, df_gerado: pd.DataFrame) -> Dict[str, float]:
    results = {
        'P (Comandos)': np.nan, 'V (Comandos)': np.nan,
        'P (Tempos)': np.nan, 'V (Tempos)': np.nan,
        'Alpha (Inicial)': np.nan, 'Alpha (Gerado)': np.nan
    }

    if df_inicial is None or df_gerado is None or df_inicial.empty or df_gerado.empty:
        return results

    # --- 1. Teste Qui-quadrado (χ²) para 'Proporção de Comandos' (Gráfico 1) ---
    try:
        counts_inicial_cmd = df_inicial['command'].value_counts()
        counts_gerado_cmd = df_gerado['command'].value_counts()

        contingency_table_df_cmd = pd.DataFrame({
            'Inicial': counts_inicial_cmd,
            'Gerado': counts_gerado_cmd
        }).fillna(0).astype(int)

        contingency_table_cmd = contingency_table_df_cmd.values
        p, v = _calculate_chi2_and_cramer(contingency_table_cmd)
        results['P (Comandos)'] = p
        results['V (Comandos)'] = v
    except Exception as e:
        print(f"Erro no Teste (Comandos): {e}")

    # --- 2. Teste Qui-quadrado (χ²) para 'Distribuição Tempos Chegada' (Gráfico 2) ---
    try:
        data_inicial_t = df_inicial[df_inicial['inter_arrival_ms'] > 0]['inter_arrival_ms']
        data_gerado_t = df_gerado[df_gerado['inter_arrival_ms'] > 0]['inter_arrival_ms']

        if not data_inicial_t.empty and not data_gerado_t.empty:
            min_val_global = min(data_inicial_t.min(), data_gerado_t.min())
            max_val_global = max(data_inicial_t.max(), data_gerado_t.max())
            if min_val_global <= 0: min_val_global = 1e-6

            min_log = np.log10(min_val_global)
            max_log = np.log10(max_val_global)

            if not (np.isfinite(min_log) and np.isfinite(max_log) and max_log > min_log):
                min_log, max_log = -6, 5

            bins = np.logspace(min_log, max_log, 50)

            counts_inicial_t, _ = np.histogram(data_inicial_t, bins=bins)
            counts_gerado_t, _ = np.histogram(data_gerado_t, bins=bins)

            contingency_table_t = pd.DataFrame({
                'Inicial': counts_inicial_t,
                'Gerado': counts_gerado_t
            }).fillna(0).astype(int).values

            p, v = _calculate_chi2_and_cramer(contingency_table_t)
            results['P (Tempos)'] = p
            results['V (Tempos)'] = v
    except Exception as e:
        print(f"Erro no Teste (Tempos Chi-quadrado): {e}")

    # --- 3. Teste de Expoente Power Law (Zipfian) para 'Recursos' (Gráfico 4) ---
    try:
        counts_inicial_res = df_inicial['target'].value_counts().values
        counts_gerado_res = df_gerado['target'].value_counts().values

        if counts_inicial_res.size > 1:
            fit_inicial = powerlaw.Fit(counts_inicial_res, discrete=True, verbose=False)
            results['Alpha (Inicial)'] = fit_inicial.alpha

        if counts_gerado_res.size > 1:
            fit_gerado = powerlaw.Fit(counts_gerado_res, discrete=True, verbose=False)
            results['Alpha (Gerado)'] = fit_gerado.alpha

    except Exception as e:
        print(f"Erro no Teste (Recursos PowerLaw Alpha): {e}")

    return results

def print_command_counts_table(df_inicial: pd.DataFrame, df_gerado: pd.DataFrame, experiment_name: str):
    print(f"\n--- Tabela de Contagem de Comandos: {experiment_name} ---")

    if df_inicial is None:
        print("DataFrame 'Inicial' está vazio.")
        return
    if df_gerado is None:
         print("DataFrame 'Gerado' está vazio ou ausente para este experimento.")
         counts_inicial = df_inicial['command'].value_counts()
         total_inicial = counts_inicial.sum()
         df_counts = pd.DataFrame({
             'Inicial (Contagem)': counts_inicial,
             'Inicial (%)': (counts_inicial / total_inicial * 100),
         }).fillna(0)
         df_counts.loc['TOTAL'] = [total_inicial, 100.0]
         print(df_counts.to_string(
            float_format="%.2f",
            formatters={'Inicial (Contagem)': "{:,.0f}".format}
         ))
         print("-" * (len(experiment_name) + 34))
         return

    try:
        counts_inicial = df_inicial['command'].value_counts()
        counts_gerado = df_gerado['command'].value_counts()

        total_inicial = counts_inicial.sum()
        total_gerado = counts_gerado.sum()

        df_counts = pd.DataFrame({
            'Inicial (Contagem)': counts_inicial,
            'Inicial (%)': (counts_inicial / total_inicial * 100),
            'Gerado (Contagem)': counts_gerado,
            'Gerado (%)': (counts_gerado / total_gerado * 100)
        }).fillna(0)

        df_counts.loc['TOTAL'] = [
            total_inicial,
            100.0,
            total_gerado,
            100.0
        ]

        print(df_counts.to_string(
            float_format="%.2f",
            formatters={'Inicial (Contagem)': "{:,.0f}".format,
                        'Gerado (Contagem)': "{:,.0f}".format}
        ))
        print("-" * (len(experiment_name) + 34))

    except Exception as e:
        print(f"Erro ao gerar tabela de contagem: {e}")


def plot_combined_comparisons(logs: Dict[str, Optional[pd.DataFrame]], experiment_name: str, path, valor):
    print(f"\nGerando gráfico combinado para o experimento: {experiment_name}...")

    TITLE_FONTSIZE = 20
    SUBPLOT_TITLE_FONTSIZE = 18
    AXIS_LABEL_FONTSIZE = 16
    LEGEND_FONTSIZE = 14
    TICK_LABEL_FONTSIZE = 14
    style_map = {
        'Inicial': {'color': 'C0', 'hist_kwargs': {'alpha': 0.6, 'histtype': 'bar'}, 'line_kwargs': {'linestyle': '-', 'alpha': 0.7, 'linewidth': 1.5}},
        'Gerado': {'color': 'C1', 'hist_kwargs': {'alpha': 0.9, 'histtype': 'step', 'linewidth': 2.0}, 'line_kwargs': {'linestyle': '--', 'alpha': 1.0, 'linewidth': 2.0}},
        'Recebido': {'color': 'C2', 'hist_kwargs': {'alpha': 0.9, 'histtype': 'step', 'linewidth': 2.0}, 'line_kwargs': {'linestyle': ':', 'alpha': 1.0, 'linewidth': 2.0}}
    }
    default_style = style_map['Inicial']
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # --- Gráfico 1: Proporção de Comandos (axes[0, 0])
    ax1 = axes[0, 0]
    valid_logs_g1 = {name: df for name, df in logs.items() if df is not None and not df.empty and 'command' in df.columns}
    if not valid_logs_g1:
        ax1.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes)
    else:
        df_proportions = pd.DataFrame({name: df['command'].value_counts(normalize=True) for name, df in valid_logs_g1.items()}).fillna(0)
        df_proportions.plot(kind='bar', ax=ax1, edgecolor='black', linewidth=0.7)
        ax1.set_title('Proporção de Comandos', fontsize=SUBPLOT_TITLE_FONTSIZE)
        ax1.set_ylabel('Proporção', fontsize=AXIS_LABEL_FONTSIZE)
        ax1.set_xlabel('command', fontsize=AXIS_LABEL_FONTSIZE)
        ax1.tick_params(axis='x', rotation=45, labelsize=TICK_LABEL_FONTSIZE)
        ax1.tick_params(axis='y', labelsize=TICK_LABEL_FONTSIZE)
        ax1.legend(fontsize=LEGEND_FONTSIZE)

    # --- Gráfico 2: Distribuição Tempos Chegada (Histograma Log) (axes[0, 1])
    ax2 = axes[0, 1]
    plot_successful_g2 = False
    global_bins = np.logspace(-6, 5, 50)
    try:
        all_inter_arrival = [df[df['inter_arrival_ms'] > 0]['inter_arrival_ms'] for df in logs.values() if df is not None and not df.empty]
        if all_inter_arrival:
            combined_data = pd.concat(all_inter_arrival).dropna()
            if not combined_data.empty:
                min_val_global = combined_data.min()
                max_val_global = combined_data.max()
                if min_val_global <= 0: min_val_global = 1e-6
                min_log = np.log10(min_val_global)
                max_log = np.log10(max_val_global)
                if (np.isfinite(min_log) and np.isfinite(max_log) and max_log > min_log):
                    global_bins = np.logspace(min_log, max_log, 50)
    except Exception: pass
    for name, df in logs.items():
        if df is not None and not df['inter_arrival_ms'].dropna().empty:
            inter_arrival_data = df[df['inter_arrival_ms'] > 0]['inter_arrival_ms']
            if not inter_arrival_data.empty:
                style = style_map.get(name, default_style)
                ax2.hist(inter_arrival_data, bins=global_bins, label=name, density=True, color=style['color'], **style['hist_kwargs'])
                plot_successful_g2 = True
    if not plot_successful_g2:
         ax2.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax2.transAxes)
    else:
        ax2.set_xscale('log')
        ax2.set_title('Distribuição Tempos Chegada (Escala Log)', fontsize=SUBPLOT_TITLE_FONTSIZE)
        ax2.set_xlabel('Tempo (ms)', fontsize=AXIS_LABEL_FONTSIZE)
        ax2.set_ylabel('Densidade de Probabilidade', fontsize=AXIS_LABEL_FONTSIZE)
        ax2.tick_params(axis='both', which='major', labelsize=TICK_LABEL_FONTSIZE)
        ax2.legend(fontsize=LEGEND_FONTSIZE)

    # --- Gráfico 3: Operações ao Longo do Tempo (axes[1, 0])
    ax3 = axes[1, 0]
    max_duration = 0
    plot_successful_g3 = False
    valid_logs_g3 = {name: df for name, df in logs.items() if df is not None and not df.empty and len(df) > 1}
    if not valid_logs_g3:
         ax3.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax3.transAxes)
    else:
        for df in valid_logs_g3.values():
            if len(df['timestamp']) > 0:
                duration = int(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0])
                if duration > max_duration:
                    max_duration = duration
        if max_duration == 0: max_duration = 1
        for name, df in valid_logs_g3.items():
            relative_time = df['timestamp'] - df['timestamp'].iloc[0]
            ops_counts = relative_time.astype(int).value_counts().sort_index()
            full_index = pd.RangeIndex(start=0, stop=max_duration + 1)
            ops_over_time = ops_counts.reindex(full_index, fill_value=0)
            if not ops_over_time.empty:
                style = style_map.get(name, default_style)
                ax3.plot(ops_over_time.index, ops_over_time.values, label=name, color=style['color'], **style['line_kwargs'])
                plot_successful_g3 = True
        if plot_successful_g3:
            ax3.set_title('Operações por Segundo', fontsize=SUBPLOT_TITLE_FONTSIZE)
            ax3.set_xlabel('Tempo (segundos)', fontsize=AXIS_LABEL_FONTSIZE)
            ax3.set_ylabel('Número de Operações', fontsize=AXIS_LABEL_FONTSIZE)
            ax3.tick_params(axis='both', labelsize=TICK_LABEL_FONTSIZE)
            ax3.legend(fontsize=LEGEND_FONTSIZE)

    # --- Gráfico 4: CDF Acesso a Recursos (axes[1, 1])
    ax4 = axes[1, 1]
    plot_successful_g4 = False
    for name, df in logs.items():
        if df is not None and not df.empty and 'target' in df.columns:
            target_counts = df['target'].value_counts()
            if not target_counts.empty:
                cumulative_counts = target_counts.cumsum()
                normalized_cumulative_freq = cumulative_counts / cumulative_counts.iloc[-1]
                normalized_rank = np.arange(1, len(target_counts) + 1) / len(target_counts)
                style = style_map.get(name, default_style)
                ax4.plot(normalized_rank, normalized_cumulative_freq.values, label=name, color=style['color'], **style['line_kwargs'])
                plot_successful_g4 = True
    if not plot_successful_g4:
        ax4.text(0.5, 0.5, 'Sem dados para plotar', horizontalalignment='center', verticalalignment='center', transform=ax4.transAxes)
    else:
        ax4.set_title('CDF Acesso a Recursos', fontsize=SUBPLOT_TITLE_FONTSIZE)
        ax4.set_xlabel('Proporção Recursos (Popularidade)', fontsize=AXIS_LABEL_FONTSIZE)
        ax4.set_ylabel('Proporção Cumulativa Acessos', fontsize=AXIS_LABEL_FONTSIZE)
        ax4.grid(True, linestyle='--', alpha=0.6)
        ax4.legend(fontsize=LEGEND_FONTSIZE)
        ax4.axhline(0.8, color='grey', linestyle=':', linewidth=0.8)
        ax4.axvline(0.2, color='grey', linestyle=':', linewidth=0.8)
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.tick_params(axis='both', labelsize=TICK_LABEL_FONTSIZE)

    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    output_filename = f'{path}/test{valor}.png'
    plt.savefig(output_filename)
    print(f"Salvo: {output_filename}")
    plt.close(fig)

if __name__ == '__main__':

    experiment_configs = {
        1: {'name': 'Replay Simples', 'path_suffix': 'test1'},
        2: {'name': 'Heatmap 1% (Original)', 'path_suffix': 'test2'},
        3: {'name': 'Heatmap 50% (Original)', 'path_suffix': 'test3'},
        4: {'name': 'Heatmap 1% (Cyclic)', 'path_suffix': 'test4'},
        5: {'name': 'Heatmap 1% (Stretch)', 'path_suffix': 'test5'},
    }

    path_log_inicial = 'logs/input/trace.log'

    df_inicial_base = parse_log_to_dataframe(path_log_inicial)

    if df_inicial_base is None:
        print("ERRO FATAL: Não foi possível carregar o log inicial. Abortando.")
        exit()

    print(f"\n=== Iniciando análise dos 5 experimentos ===")

    results_summary_list = []

    print_command_counts_table(df_inicial_base, df_inicial_base, "Log Inicial (Base)")

    for x, config in experiment_configs.items():
        experiment_name = config['name']
        path_suffix = config['path_suffix']

        print(f"\n--- Processando Experimento {x}: {experiment_name} ---")

        path_log_gerado = f'logs/output/{path_suffix}/synthetic_trace.log'
        path_log_recebido = f'logs/output/{path_suffix}/redis_monitor_received.log'

        df_gerado_atual = parse_log_to_dataframe(path_log_gerado)
        df_recebido_atual = parse_log_to_dataframe(path_log_recebido)

        logs_data = {
            'Inicial': df_inicial_base,
            'Gerado': df_gerado_atual,
            'Recebido': df_recebido_atual,
        }

        print_command_counts_table(df_inicial_base, df_gerado_atual, experiment_name)

        stats_dict = calculate_similarity_metrics(df_inicial_base, df_gerado_atual)
        stats_dict['Experimento'] = experiment_name
        results_summary_list.append(stats_dict)

        plot_combined_comparisons(logs_data, experiment_name, f'logs/output/{path_suffix}', x)

    print(f"\n=== Análise concluída ===")

    print("\n\n=== Tabela de Validação Estatística (Inicial vs. Gerado) ===")

    df_summary = pd.DataFrame(results_summary_list)
    df_summary = df_summary.set_index('Experimento')

    columns_order = [
        'P (Comandos)', 'V (Comandos)',
        'P (Tempos)', 'V (Tempos)',
        'Alpha (Inicial)', 'Alpha (Gerado)'
    ]
    columns_to_show = [col for col in columns_order if col in df_summary.columns]
    df_summary = df_summary[columns_to_show]

    print(df_summary.to_string(float_format="%.4f"))
    print("\nInterpretação:")
    print("  P (P-Value):     Significância. P < 0.05 significa 'Estatísticamente Diferente' (esperado para N grande).")
    print("  V (V-Cramer):    Tamanho do Efeito (Categórico/Binned). V < 0.1 indica 'Ajuste Excelente' (Bom).")
    print("  Alpha (Recursos): Expoente da Power-Law (Zipfian). Valores próximos (ex: 1.51 vs 1.53) provam")
    print("                    que a 'forma' da distribuição (o hotspot) foi aprendida corretamente (Bom).")
