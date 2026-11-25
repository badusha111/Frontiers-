import json
import os
import time
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# ЗАДАНИЕ 1
# ==============================================================================

load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL")

if not api_key or not base_url or not model_name:
    raise ValueError("Ошибка: не заданы API_KEY, BASE_URL или MODEL в файле .env")

client = OpenAI(api_key=api_key, base_url=base_url)

# Зачем в этой работе нужен .env? — Чтобы хранить ключ и настройки отдельно от кода.
# Чем LLM_BASE_URL отличается от LLM_MODEL? — BASE_URL задаёт адрес сервера API, а MODEL — имя самой языковой модели.
# Почему API ключ нельзя прикладывать к сдаче? — Им могут воспользоваться посторонние и исчерпать выделенную квоту.


# ==============================================================================
# ЗАДАНИЕ 2
# ==============================================================================

short_question = "Что такое база данных?"

response_short = client.responses.create(
    model=model_name,
    instructions="Отвечай по-русски ровно одним коротким предложением.",
    input=short_question,
)

first_answer = response_short.output_text
print("=== Задание 2 ===")
print(first_answer)

(OUTPUT_DIR / "first_answer.txt").write_text(first_answer, encoding="utf-8")

# Что задаёт параметр instructions? — Системную инструкцию: стиль, язык и ограничения формата ответа.
# Что передаёт параметр input? — Текст пользовательского запроса или вопроса для модели.
# Какой метод отправляет запрос? — client.responses.create().
# В каком поле находится готовый текст? — В поле response.output_text.


# ==============================================================================
# ЗАДАНИЕ 3
# ==============================================================================

questions_timing = [
    "Что такое таблица базы данных?",
    "Что такое запись в таблице?",
    "Что такое поле таблицы?",
]

timing_records = []
times_list = []

print("\n=== Задание 3 ===")
for idx, q in enumerate(questions_timing):
    started_at = time.perf_counter()
    resp = client.responses.create(
        model=model_name,
        instructions="Отвечай кратко по-русски.",
        input=q,
    )
    elapsed_seconds = time.perf_counter() - started_at

    times_list.append(elapsed_seconds)
    timing_records.append(
        {
            "question": q,
            "elapsed_seconds": round(elapsed_seconds, 4),
        }
    )

    if idx == 0:
        print(f"ID ответа: {resp.id}")
        print(f"Статус ответа: {resp.status}")
        print(f"Текст ответа: {resp.output_text}")
        if resp.usage is None:
            print("Сервер не вернул сведения о токенах.")
        else:
            print(f"Входные токены: {resp.usage.input_tokens}")
            print(f"Выходные токены: {resp.usage.output_tokens}")
            print(f"Всего токенов: {resp.usage.total_tokens}")

average_seconds = sum(times_list) / len(times_list)

timing_report = {
    "measurements": timing_records,
    "average_seconds": round(average_seconds, 4),
}

(OUTPUT_DIR / "timing_report.json").write_text(
    json.dumps(timing_report, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Какой участок программы измеряет perf_counter? — Время выполнения самого API-запроса client.responses.create().
# Какие три времени вы получили и как вычислили среднее? — Времена записаны в times_list (и timing_report.json), среднее: sum(times_list) / len(times_list).
# Где находятся входные, выходные и общие токены? — В полях response.usage.input_tokens, output_tokens и total_tokens.
# Что означает статус вашего ответа? — Статус "completed" означает, что генерация ответа успешно завершена.
# Почему нельзя объяснить разницу во времени только по трём запускам? — На время влияют длина ответа, нагрузка сервера и сеть; трёх замеров мало для статистики.


# ==============================================================================
# ЗАДАНИЕ 4
# ==============================================================================

class PlantOrder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plant: Literal["cactus", "fern", "orchid"] | None = Field(default=None)
    quantity: int | None = Field(default=None, ge=1, le=6)
    pot_size: Literal["small", "medium", "large"] | None = Field(default=None)
    gift_wrap: bool | None = Field(default=None)
    is_ready: bool
    clarification_question: str | None = Field(default=None)


messages_variant_14 = [
    "Две orchid в больших горшках с подарочной упаковкой",
    "Один cactus в маленьком горшке без упаковки",
    "Хочу купить fern",
]

parsed_entities = []

print("\n=== Задание 4 ===")
for msg in messages_variant_14:
    structured_response = client.responses.parse(
        model=model_name,
        instructions=(
            "Извлеки данные заказа растения (PlantOrder) из сообщения. "
            "Не добавляй поля вне схемы и не угадывай недостающие сведения. "
            "Если не хватает хотя бы одного из полей (plant, quantity, pot_size, gift_wrap), "
            "поставь is_ready=False и сформулируй один уточняющий вопрос в clarification_question. "
            "Если все данные указаны, поставь is_ready=True и clarification_question=None."
        ),
        input=msg,
        text_format=PlantOrder,
    )

    result = structured_response.output_parsed
    if result is None:
        raise RuntimeError("Структурированный ответ не получен")

    print(f"Сообщение: '{msg}' -> {result}")
    parsed_entities.append(result.model_dump())

(OUTPUT_DIR / "entities_data.json").write_text(
    json.dumps(parsed_entities, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Какие поля и ограничения включили в Entity и почему? — plant и pot_size (Literal из допустимых значений), quantity (int с ge=1, le=6), gift_wrap (bool), plus is_ready и clarification_question.
# Как различаются готовые и неполные данные? — При полных данных is_ready=True и clarification_question=None, при неполных — False и текст вопроса.
# Зачем запрещать дополнительные поля? — Чтобы модель строго следовала схеме и не придумывала лишние ключи.
# Что передаёт параметр text_format=Entity? — Схему Pydantic для приведения ответа к строгой JSON-структуре.
# Чем output_parsed отличается от output_text? — output_text — сырая строка, а output_parsed — готовый провалидированный объект Pydantic.


# ==============================================================================
# ДОПОЛНИТЕЛЬНОЕ ЗАДАНИЕ
# ==============================================================================

print("\n=== Дополнительное задание ===")
q1 = "Что такое таблица базы данных?"
q2 = "Приведи один короткий пример таблицы для библиотеки."

first_turn = client.responses.create(
    model=model_name,
    instructions="Отвечай кратко на русском языке.",
    input=q1,
    store=True,
)
print("Первый ответ:", first_turn.output_text)

try:
    second_turn = client.responses.create(
        model=model_name,
        instructions="Отвечай кратко на русском языке.",
        previous_response_id=first_turn.id,
        input=q2,
    )
except Exception:
    second_turn = client.responses.create(
        model=model_name,
        instructions="Отвечай кратко на русском языке.",
        input=f"Вопрос: {q1}\nОтвет: {first_turn.output_text}\nНовый вопрос: {q2}",
    )

print("Второй ответ:", second_turn.output_text)

(OUTPUT_DIR / "dialogue_answer.txt").write_text(
    second_turn.output_text, encoding="utf-8"
)

# Зачем второму запросу previous_response_id? — Чтобы привязать его к первому ответу на сервере и сохранить контекст диалога.
# Почему во втором запросе снова указываются instructions? — Системные инструкции не наследуются по ID и задаются заново для каждого вызова.
# Почему второй запрос тоже расходует токены? — Сервер загружает всю предыдущую историю по ID в контекст модели и заново её обрабатывает.
