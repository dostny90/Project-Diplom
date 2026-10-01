import pandas as pd

# Загружаем наш датасет из папки data
file_path = 'data/cic.csv'

print("Загрузка датасета...")
# Читаем первые 100 000 строк (чтобы быстро затестить)
df = pd.read_csv(file_path, nrows=100000)

print(f"Размер таблицы: {df.shape[0]} строк, {df.shape[1]} колонок\n")

# Очищаем названия колонок от случайных пробелов
df.columns = df.columns.str.strip()

print("Список первых 10 колонок:")
print(list(df.columns[:10]))

# Проверяем, какие типы аномалий/атак есть в колонке Label
if 'Label' in df.columns:
    print("\nРаспределение меток (Normal vs Anomaly):")
    print(df['Label'].value_counts())
else:
    print("\nКолонка 'Label' не найдена, проверь названия колонок.")