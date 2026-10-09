# PostgreSQL база данных

Схема и Python-модуль рассчитаны на текущий код в `ml_model`:

- `train.py` обучается на числовых столбцах CIC CSV, удаляя `Label`, IP-адреса, `Timestamp` и `Flow ID`.
- `predict.py` возвращает `status` (`Normal` или `Anomaly`), `is_anomaly` и `confidence` в процентах.
- Все числовые признаки потока хранятся в `network_flows.features` как JSONB. Это позволяет схеме поддерживать список признаков, который меняется при переобучении модели.
- Каждое предсказание записывается в `anomaly_predictions` и связано с исходным потоком.

## Запуск

1. Установите PostgreSQL и драйвер Python: `python -m pip install "psycopg[binary]>=3.1"`.
2. Укажите строку подключения в переменной окружения `DATABASE_URL`, например `postgresql://user:password@localhost:5432/traffic_db`.
3. Из корня проекта создайте таблицы командой `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f data/schema.sql`.

В Python можно вызвать `initialize_database()` для создания таблиц из файла схемы. Чтобы получить предсказание и сразу сохранить поток с результатом:

```python
from data.database import predict_and_save
from ml_model.predict import AnomalyDetector

detector = AnomalyDetector()
result = predict_and_save(sample_packet, detector)
print(result)
```

`sample_packet` — словарь тех же сетевых полей, который передается в `AnomalyDetector.predict()`.
