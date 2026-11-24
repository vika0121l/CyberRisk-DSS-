
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Завантаження результатів експерименту
input_file = Path(
    "experiment_results/risk_model_125_scenarios.csv"
)

df = pd.read_csv(input_file)

# Перевірка кількості сценаріїв
assert len(df) == 125, "Некоректна кількість сценаріїв"

# Порядок рівнів ризику
risk_levels = [
    "Дуже низький",
    "Низький",
    "Середній",
    "Високий",
    "Критичний"
]

# Кількість сценаріїв за рівнями
distribution = (
    df["Risk_Level"]
    .value_counts()
    .reindex(risk_levels, fill_value=0)
)

# Основні статистичні показники
print("АНАЛІЗ ЕКСПЕРИМЕНТУ")
print("-" * 40)

print(f"Кількість сценаріїв: {len(df)}")
print(f"Мінімальна оцінка: {df['R'].min()}")
print(f"Максимальна оцінка: {df['R'].max()}")
print(f"Середня оцінка: {df['R'].mean():.2f}")
print(f"Медіана: {df['R'].median():.2f}")

print("\nРОЗПОДІЛ ЗА РІВНЯМИ РИЗИКУ")

for level, count in distribution.items():
    print(f"{level}: {count}")

# Папка для результатів
output_dir = Path("experiment_results")
output_dir.mkdir(exist_ok=True)

# Збереження таблиці розподілу
distribution_df = distribution.reset_index()
distribution_df.columns = [
    "Risk_Level",
    "Scenario_Count"
]

distribution_df.to_csv(
    output_dir / "risk_level_distribution.csv",
    index=False,
    encoding="utf-8-sig"
)

# Побудова діаграми
plt.figure(figsize=(10, 6))

bars = plt.bar(
    distribution.index,
    distribution.values
)

plt.title(
    "Розподіл сценаріїв за рівнями кіберризику"
)

plt.xlabel("Рівень ризику")
plt.ylabel("Кількість сценаріїв")

plt.xticks(rotation=20, ha="right")

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height,
        str(int(height)),
        ha="center",
        va="bottom"
    )

plt.tight_layout()

plt.savefig(
    output_dir / "risk_level_distribution.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\nТаблицю та діаграму успішно збережено.")
