# Система анализа сетевого трафика и детекции аномалий

## 📌 Тема диплома
Разработка интеллектуальной системы анализа сетевого трафика для выявления аномалий в локальной сети организации.

## 👥 Команда проекта
- **Разработчик 1 (Network & Data):** 
- **Разработчик 2 (ML Engineer):** 
- **Разработчик 3 (Backend & UI):** 

## 🛠 Стек технологий
- **Язык разработки:** Python 3.10+
- **Анализ трафика:** Wireshark, Scapy, PyShark
- **Machine Learning:** Scikit-learn, XGBoost, Pandas
- **Backend API:** FastAPI
- **База данных:** PostgreSQL

## 🚀 Запуск backend
Все команды выполняются из корня проекта.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Документация API откроется на http://127.0.0.1:8000/docs.

| Метод | Путь | Что делает |
|---|---|---|
| `GET` | `/health` | Загружена ли модель и доступна ли база |
| `POST` | `/predict` | Классифицирует поток: тело — словарь признаков CIC, например `{"Dst Port": 21, "Flow Duration": 1000}` |
| `GET` | `/anomalies?limit=50` | Последние обнаруженные аномалии из базы |

Без переменной `DATABASE_URL` сервис работает, но `/predict` не сохраняет результаты, а `/anomalies` отвечает 503. Как подготовить базу — в [data/README.md](data/README.md).

Тесты: `pytest`.
