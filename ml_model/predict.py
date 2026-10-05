import joblib
import pandas as pd
import numpy as np

class AnomalyDetector:
    def __init__(self, model_path='ml_model/model.pkl', features_path='ml_model/features.pkl'):
        # Загружаем сохраненную модель и список фичей
        self.model = joblib.load(model_path)
        self.features = joblib.load(features_path)
        print("ML-модель детекции аномалий успешно загружена!")

    def predict(self, input_data: dict) -> dict:
        """
        Принимает словарь с параметрами трафика.
        Возвращает вердикт и вероятность аномалии.
        """
        # Преобразуем входящий словарь в DataFrame
        df_input = pd.DataFrame([input_data])
        
        # Добавляем отсутствующие колонки нулями, чтобы структура совпадала с train.py
        for col in self.features:
            if col not in df_input.columns:
                df_input[col] = 0.0
                
        # Оставляем только те фичи и в том порядке, на которых обучалась модель
        df_input = df_input[self.features]
        
        # Заменяем возможные бесконечные значения
        df_input.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_input.fillna(0.0, inplace=True)
        
        # Делаем предсказание
        prediction = self.model.predict(df_input)[0]
        probabilities = self.model.predict_proba(df_input)[0]
        
        status = "Anomaly" if prediction == 1 else "Normal"
        confidence = float(probabilities[1] if prediction == 1 else probabilities[0])
        
        return {
            "status": status,
            "is_anomaly": bool(prediction == 1),
            "confidence": round(confidence * 100, 2)
        }

# Быстрый тест работы
if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Симулируем случайный тестовый пакет
    sample_packet = {
        'Dst Port': 21,
        'Protocol': 6,
        'Flow Duration': 1000,
        'Tot Fwd Pkts': 5
    }
    
    result = detector.predict(sample_packet)
    print("\nТестовый вывод инференса:")
    print(result)