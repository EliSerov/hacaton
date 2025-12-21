from typing import Any, Dict, List


class PromptBuilder:
    def build_summary(self, query: str, sources: List[Dict[str, Any]]) -> str:
        blocks = []
        for i, s in enumerate(sources, start=1):
            blocks.append(
                f"[{i}] {s['title']}\nURL: {s['url']}\nАвтор: {s.get('author','')}\nДата: {s.get('date','')}\nТематика: {s.get('topic','')}\nФрагменты:\n{s['excerpt']}\n"
            )

        rules = (
            "Ты — AI-агент для поиска и анализа статей технологических СМИ.\n"
            "Этичность и точность:\n"
            "- Используй ТОЛЬКО предоставленные фрагменты.\n"
            "- Не выдумывай факты. Если данных нет — явно скажи об этом.\n"
            "- На каждое значимое утверждение ставь ссылку [n].\n"
            "- Не раскрывай персональные данные, которых нет в источниках.\n\n"
            "Формат ответа:\n"
            "1) Короткое аннотационное резюме (3–7 предложений).\n"
            "2) Строка: Источники: [1][2]...[k]\n"
        )

        return f"""{rules}
Запрос: {query}

Источники:
{chr(10).join(blocks)}

Сформируй аннотационное резюме по запросу.
"""

    def build_quiz(self, query: str, sources: List[Dict[str, Any]], n_questions: int = 6) -> str:
        blocks = []
        for i, s in enumerate(sources, start=1):
            blocks.append(f"[{i}] {s['title']}\nURL: {s['url']}\nФрагменты:\n{s['excerpt']}\n")

        rules = (
            "Ты — AI-агент. Сгенерируй мини-тест по материалам источников.\n"
            "Правила:\n"
            "- Используй только источники ниже, не выдумывай.\n"
            "- Каждый вопрос должен иметь ссылку [n] на источник.\n"
            "- Формат: Вопрос, 4 варианта (A–D), правильный ответ, краткое объяснение.\n"
            f"- Количество вопросов: {n_questions}.\n"
            "- В конце: Источники: [1][2]...[k]\n"
        )

        return f"""{rules}
Запрос: {query}

Источники:
{chr(10).join(blocks)}

Сгенерируй тест.
"""
