import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# ПОДГОТОВКА
# ==============================================================================

load_dotenv()

api_key = os.environ["LLM_API_KEY"]
base_url = os.environ["LLM_BASE_URL"]
model_name = os.environ["LLM_MODEL"]

client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)


# ==============================================================================
# ЗАДАНИЕ 1
# ==============================================================================

# Зачем в этой работе нужен .env?
# Чтобы хранить ключ и настройки отдельно от кода.

# Чем LLM_BASE_URL отличается от LLM_MODEL?
# LLM_BASE_URL задаёт адрес сервера API, а LLM_MODEL — имя языковой модели.

# Почему API-ключ нельзя прикладывать к сдаче?
# Им могут воспользоваться посторонние и исчерпать выделенную квоту.


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

answer_path = output_dir / "first_answer.txt"
answer_path.write_text(first_answer, encoding="utf-8")


# Что задаёт параметр instructions?
# Общие правила для ответа модели: стиль, язык и формат.

# Что передаёт параметр input?
# Текст пользовательского запроса или вопроса для модели.

# Какой метод отправляет запрос?
# client.responses.create().

# В каком поле находится готовый текст?
# В поле response.output_text.


# ==============================================================================
# ЗАДАНИЕ 3
# ==============================================================================

questions = [
    "Что такое таблица базы данных?",
    "Что такое запись в таблице?",
    "Что такое поле таблицы?",
]

responses_data = []

print("\n=== Задание 3 ===")

for question in questions:
    response = client.responses.create(
        model=model_name,
        instructions="Отвечай кратко по-русски.",
        input=question,
    )

    print("\nВопрос:", question)
    print("ID ответа:", response.id)
    print("Модель:", response.model)
    print("Статус ответа:", response.status)
    print("Текст ответа:", response.output_text)

    if response.usage is not None:
        print("Входные токены:", response.usage.input_tokens)
        print("Выходные токены:", response.usage.output_tokens)
        print("Всего токенов:", response.usage.total_tokens)
    else:
        print("Сервер не вернул сведения о токенах.")

    responses_data.append(
        {
            "id": response.id,
            "model": response.model,
            "status": response.status,
            "output_text": response.output_text,
        }
    )

report_path = output_dir / "responses_report.json"

report_path.write_text(
    json.dumps(responses_data, ensure_ascii=False, indent=2),
    encoding="utf-8",
)


# Где находятся входные, выходные и общие токены?
# В response.usage.input_tokens, output_tokens и total_tokens.

# Что означает статус ответа?
# Статус "completed" означает, что ответ сформирован полностью.

# Почему нужно проверять response.usage is not None?
# Потому что сервер может не вернуть сведения о расходе токенов.


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


messages = [
    "Две orchid в больших горшках с подарочной упаковкой",
    "Один cactus в маленьком горшке без упаковки",
    "Хочу купить fern",
]

parsed_entities = []

print("\n=== Задание 4 ===")

for message in messages:
    structured_response = client.responses.parse(
        model=model_name,
        instructions=(
            "Извлеки данные заказа растения из сообщения пользователя. "
            "Не добавляй поля вне схемы и не угадывай недостающие сведения. "
            "Если не хватает хотя бы одного из полей "
            "(plant, quantity, pot_size, gift_wrap), "
            "поставь is_ready=False и сформулируй один уточняющий вопрос "
            "в clarification_question. "
            "Если все данные указаны, поставь is_ready=True "
            "и clarification_question=None."
        ),
        input=message,
        text_format=PlantOrder,
    )

    result = structured_response.output_parsed

    if result is not None:
        print("Сообщение:", message)
        print("Результат:", result)

        parsed_entities.append(result.model_dump())

entities_path = output_dir / "entities_data.json"

entities_path.write_text(
    json.dumps(parsed_entities, ensure_ascii=False, indent=2),
    encoding="utf-8",
)


# Какие поля и ограничения включили в PlantOrder и почему?
# plant и pot_size — Literal с допустимыми значениями;
# quantity — int с ограничениями ge=1 и le=6;
# gift_wrap — bool;
# также is_ready и clarification_question.

# Как различаются готовые и неполные данные?
# При полных данных is_ready=True и clarification_question=None.
# При неполных — is_ready=False и текст уточняющего вопроса.

# Зачем запрещать дополнительные поля?
# Чтобы модель следовала заданной схеме и не добавляла лишние поля.

# Что передаёт параметр text_format=PlantOrder?
# Pydantic-схему ожидаемого структурированного ответа.

# Чем output_parsed отличается от output_text?
# output_text — текстовая строка ответа,
# output_parsed — разобранный объект Pydantic.


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
)

print("Первый ответ:", first_turn.output_text)

second_turn = client.responses.create(
    model=model_name,
    instructions="Отвечай кратко на русском языке.",
    previous_response_id=first_turn.id,
    input=q2,
)

print("Второй ответ:", second_turn.output_text)

dialogue_path = output_dir / "dialogue_answer.txt"

dialogue_path.write_text(
    second_turn.output_text,
    encoding="utf-8",
)


# Зачем второму запросу previous_response_id?
# Чтобы связать его с первым ответом и продолжить диалог.

# Почему во втором запросе снова указываются instructions?
# Инструкции указываются повторно для каждого вызова.

# Почему второй запрос тоже расходует токены?
# Потому что предыдущий контекст участвует в обработке нового запроса.
