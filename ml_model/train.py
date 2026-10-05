import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

print("1. Загрузка данных...")
df = pd.read_csv('data/cic.csv', nrows=100000)
df.columns = df.columns.str.strip()

print("2. Очистка и предобработка...")
# Заменяем бесконечные значения (Inf/-Inf) на NaN и удаляем их
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

# Выделяем целевую колонку Label
if 'Label' not in df.columns:
    raise ValueError("Колонка 'Label' не найдена в датасете!")

y = df['Label'].apply(lambda x: 0 if str(x).strip() == 'Benign' else 1)

# Выкидываем текстовые/ненужные колонки, если они есть (например, Timestamp, IP)
drop_cols = ['Label', 'Timestamp', 'Flow ID', 'Source IP', 'Src IP', 'Destination IP', 'Dst IP']
X = df.drop(columns=[col for col in drop_cols if col in df.columns])

# Оставляем только числовые столбцы
X = X.select_dtypes(include=[np.number])

print(f"Фичей для обучения: {X.shape[1]}")
print(f"Распределение классов (0 - Норма, 1 - Аномалия):\n{y.value_counts()}")

print("\n3. Разделение на train/test...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("\n4. Обучение модели Random Forest...")
clf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
clf.fit(X_train, y_train)

print("\n5. Оценка качества модели...")
y_pred = clf.predict(X_test)
print("\nОтчет по классификации:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))

print("\nМатрица ошибок (Confusion Matrix):")
print(confusion_matrix(y_test, y_pred))

# Сохраняем модель и список используемых фичей
joblib.dump(clf, 'ml_model/model.pkl')
joblib.dump(list(X.columns), 'ml_model/features.pkl')
print("\nУра! Модель успешно сохранена в 'ml_model/model.pkl'")