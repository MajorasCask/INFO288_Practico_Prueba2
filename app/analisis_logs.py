# analisis_logs.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

pd.options.mode.chained_assignment = None

# Cargar el log
df = pd.read_csv('centralized_log.log', comment='#', header=None)
df.columns = ['timestamp_ini', 'timestamp_fin', 'maquina', 'tipo_maquina', 
              'query', 'tiempo_total', 'score', 'rango_etario', 'Tamaño_en_MB']

df['timestamp_ini'] = pd.to_datetime(df['timestamp_ini'])
df['timestamp_fin'] = pd.to_datetime(df['timestamp_fin'])

# 1: Gráfico de torta con porcentaje de consulta por rango etario.
plt.figure(figsize=(8, 8))
df['rango_etario'].value_counts().plot.pie(
    autopct='%1.1f%%', 
    startangle=140,
    colors=['#840032', '#3A606E', '#73BA9B'],
    textprops={'fontsize': 12}
)
plt.title('Porcentaje de Consultas por Rango Etario', fontsize=16)
plt.tight_layout()
plt.savefig('porcentaje_consultas.png')
plt.close()

# 2: Curvas de los promedios de score a través del tiempo con tamaños de ventana variables.
plt.figure(figsize=(12, 6))
for ventana, color in zip([3, 7, 15], ['#FF6B6B', '#4ECDC4', '#556270']):
    df[f'score_{ventana}'] = df['score'].rolling(ventana, min_periods=1).mean()
    plt.plot(df['timestamp_ini'], df[f'score_{ventana}'], 
             label=f'Ventana {ventana}', color=color, linewidth=2)

plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

plt.title('Curva de Evolución del Score Promedio')
plt.xlabel('Tiempo')
plt.ylabel('Score')
plt.legend()
plt.grid(alpha=0.3)

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig('evolucion_score_promedio.png')
plt.close()

# 3: Gráfico de cajas destacando los tiempos promedio, min, max por esclavo. 
df_esclavos = df[df['tipo_maquina'] != 'Maestro'].copy()

plt.figure(figsize=(10, 6))
sns.boxplot(
    x='tipo_maquina', 
    y='tiempo_total', 
    data=df_esclavos, 
    hue='tipo_maquina',
    palette="Set3", 
    width=0.5, 
    showfliers=False,
    legend=False
)

stats = df_esclavos.groupby('tipo_maquina')['tiempo_total'].agg(['mean', 'min', 'max'])
for i, esclavo in enumerate(stats.index):
    plt.scatter(i, stats.loc[esclavo, 'mean'], color='red', s=100, 
               label='Promedio' if i == 0 else "", zorder=3)
    plt.scatter(i, stats.loc[esclavo, 'min'], color='green', s=100, 
               label='Mínimo' if i == 0 else "", zorder=3)
    plt.scatter(i, stats.loc[esclavo, 'max'], color='blue', s=100, 
               label='Máximo' if i == 0 else "", zorder=3)

plt.title("Tiempos por Esclavo")
plt.legend()
plt.tight_layout()
plt.savefig('tiempos_esclavos.png')
plt.close()

# 4: Latencia de red entre el maestro y los esclavos
maestro_df = df[df['tipo_maquina'] == 'Maestro'][['query', 'timestamp_ini']]
merged_df = pd.merge(
    df[df['tipo_maquina'] != 'Maestro'], 
    maestro_df.rename(columns={'timestamp_ini': 'timestamp_maestro'}), 
    on='query'
)
merged_df['latencia'] = (merged_df['timestamp_ini'] - merged_df['timestamp_maestro']).dt.total_seconds() * 1000

plt.figure(figsize=(12, 6))
for esclavo in merged_df['tipo_maquina'].unique():
    subset = merged_df[merged_df['tipo_maquina'] == esclavo]
    plt.plot(subset['timestamp_ini'], subset['latencia'], 'o-', label=esclavo)

plt.title('Latencia entre Maestro y Esclavos')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('latencia.png')
plt.close()

# 5: Tamaño en MB de las respuestas por hora a través del día, indicando el día.
df['Tamaño_en_MB'] = pd.to_numeric(df['Tamaño_en_MB'], errors='coerce')

df['Hora'] = df['timestamp_ini'].dt.hour
df['Día'] = df['timestamp_ini'].dt.date.astype(str)

df_agrupado = df.groupby(['Hora', 'Día'])['Tamaño_en_MB'].sum().reset_index()

plt.figure(figsize=(14, 7))
sns.barplot(
    x='Hora',
    y='Tamaño_en_MB',
    hue='Día',
    data=df_agrupado,
    palette='viridis'
)

plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.5f}'))

plt.title('Tamaño Total de Respuestas por Hora (MB)', pad=15)
plt.xlabel('Hora del día')
plt.ylabel('Tamaño total (MB)')
plt.legend(title='Día', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Guardar figura
plt.savefig('tamaño_respuestas.png', dpi=120, bbox_inches='tight')
plt.close()
