import joblib
import matplotlib.pyplot as plt
import pandas as pd

# Загружаем модель и фичи
model = joblib.load('ml_model/model.pkl')
features = joblib.load('ml_model/features.pkl')

# Получаем важность признаков
importances = model.feature_importances_

# Словарь перевода терминов сетевого трафика на русский
translation = {
    'Flow Pkts/s': 'Интенсивность пакетов (пакет/с)',
    'Bwd Pkts/s': 'Скорость входящих пакетов (пакет/с)',
    'Flow IAT Mean': 'Среднее время между пакетами',
    'Fwd Pkts/s': 'Скорость исходящих пакетов (пакет/с)',
    'Flow IAT Max': 'Макс. время между пакетами',
    'Init Fwd Win Bytes': 'Размер начального окна TCP',
    'Fwd IAT Min': 'Мин. пауза между исходящими пакетами',
    'Subflow Fwd Pkts': 'Среднее число исходящих пакетов в подпотоке',
    'Fwd IAT Tot': 'Суммарное время исходящего потока',
    'Fwd Seg Size Min': 'Мин. размер сегмента исходящего пакета'
}

# Формируем датафрейм
df_imp = pd.DataFrame({'Feature': features, 'Importance': importances})
df_imp = df_imp.sort_values(by='Importance', ascending=True).tail(10)

# Переводим названия на русский (если термина нет в словаре, оставит исходный)
df_imp['Feature_RU'] = df_imp['Feature'].map(lambda x: translation.get(x, x))

# Строим красивый график
plt.figure(figsize=(11, 6))
plt.barh(df_imp['Feature_RU'], df_imp['Importance'], color='#2ecc71')
plt.title('Топ-10 наиболее значимых признаков модели Random Forest', fontsize=12)
plt.xlabel('Индекс важности признака (Importance Score)', fontsize=10)
plt.tight_layout()

# Сохраняем и обновляем файл
plt.savefig('ml_model/feature_importance.png', dpi=300)
print("график сохранен в 'ml_model/feature_importance.png'!")