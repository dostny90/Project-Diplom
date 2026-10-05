import joblib
import matplotlib.pyplot as plt
import pandas as pd

# Загружаем модель и фичи
model = joblib.load('ml_model/model.pkl')
features = joblib.load('ml_model/features.pkl')

# Получаем важность признаков
importances = model.feature_importances_

# Сортируем и берем топ-10 самых важных
df_imp = pd.DataFrame({'Feature': features, 'Importance': importances})
df_imp = df_imp.sort_values(by='Importance', ascending=True).tail(10)

# Строим красивый график
plt.figure(figsize=(10, 6))
plt.barh(df_imp['Feature'], df_imp['Importance'], color='#2ecc71')
plt.title('Top 10 Most Important Features in Random Forest Model')
plt.xlabel('Importance Score')
plt.tight_layout()

# Сохраняем в папку ml_model
plt.savefig('ml_model/feature_importance.png', dpi=300)
print("График успешно сохранен в 'ml_model/feature_importance.png'!")