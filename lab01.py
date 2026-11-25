import os
from dotenv import  load_dotenv
from openai import OpenAI
import json
from pathlib import Path
from pydantic import *
import time
from typing import Literal

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
# ЗАДАНИЕ 2
# ==============================================================================
short_question = "Что такое база данных?"
response = client.responses.create(
    model=model_name,
    instructions="Отвечай по-русски ровно одним коротким предложением.",
    input=short_question,
)

first_answer = response.output_text
print(first_answer)

with open(output_dir / "first.answer.txt", "w", encoding="utf-8") as file:
    file.write(first_answer)


# ==============================================================================
# ЗАДАНИЕ 3
# ==============================================================================
questions = [
    "Что такое таблица базы данных?",
    "Что такое запись в таблице?",
    "Что такое поле таблицы?",
]

responses_data = []
times_list = []

started_at = time.perf_counter()
for question in questions:
    response = client.responses.create(
        model=model_name,
        instructions="Отвечай по-русски ровно одним коротким предложением.",
        input=question,
    )
    elapsed_seconds = time.perf_counter() - started_at
    times_list.append(elapsed_seconds)
    responses_data.append(response)

average_seconds = sum(times_list) / len(times_list)
response = responses_data[0]

print(f"ID ответа: {response.id}")
print(f"Статус ответа: {response.status}")
print(f"Текст ответа: {response.output_text}")

for i in range(len(times_list)):
    print(f"Время запроса {i+1}: {times_list[i]:.2f}")
print(f"Среднее время: {round(average_seconds, 2)}")

if response.usage is None:
    print("Сервер не вернул сведенья о токенах")
else:
    print(f"Входные токены: {response.usage.input_tokens}")
    print(f"Выходные токены: {response.usage.output_tokens}")
    print(f"Всего токенов: {response.usage.total_tokens}")

timing_report = {
    "questions": questions,
    "times_seconds": times_list,
    "average_seconds": average_seconds
}

with open(output_dir / "timing_report.json",  "w", encoding="utf-8") as file:
    json.dump(timing_report, file, ensure_ascii=False, indent=2)


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
    
    
with open(output_dir / "entities_data.json",  "w", encoding="utf-8") as file:
    json.dump(parsed_entities, file, ensure_ascii=False, indent=2)
