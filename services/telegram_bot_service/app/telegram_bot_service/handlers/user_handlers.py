from html import escape
from typing import Any, Dict, List, Optional
import traceback

from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from telegram_bot_service.services.rag_client import get_rag_client
from telegram_bot_service.models.contracts import SearchResponse


router = Router()


class SearchStates(StatesGroup):
    waiting_for_query = State()
    waiting_for_author = State()
    waiting_for_date = State()
    waiting_for_topic = State()


def make_filter_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Автор"), KeyboardButton(text="📅 Дата")],
            [KeyboardButton(text="🏷️ Тема"), KeyboardButton(text="✅ Выполнить поиск")],
            [KeyboardButton(text="♻️ Сбросить фильтры")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def make_post_search_inline_keyboard(articles: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    # Recommend for first up to 3 items to keep UI compact
    rec_buttons: List[InlineKeyboardButton] = []
    for i in range(min(3, len(articles))):
        rec_buttons.append(InlineKeyboardButton(text=f"🔁 Похожие #{i+1}", callback_data=f"rec:{i}"))

    rows: List[List[InlineKeyboardButton]] = []
    if rec_buttons:
        rows.append(rec_buttons)

    rows.append([InlineKeyboardButton(text="📝 Тест по найденным", callback_data="quiz")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Привет! Я бот для интеллектуального поиска по статьям тех-СМИ.\n\n"
        "Команды:\n"
        "/search — начать поиск\n"
        "/help — справка",
        reply_markup=make_filter_keyboard(),
    )


@router.message(F.text == "/help")
async def process_help_command(message: Message) -> None:
    await message.answer(
        "Используйте /search и задайте запрос.\n"
        "Далее вы можете добавить фильтры: автор, дата (YYYY-MM-DD), тематика.\n\n"
        "После ответа доступны кнопки: похожие публикации и генерация теста."
    )


@router.message(F.text == "/search")
async def cmd_search(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer("Введите поисковый запрос:")


@router.message(SearchStates.waiting_for_query)
async def process_query(message: Message, state: FSMContext) -> None:
    await state.update_data(query=message.text.strip(), author=None, date=None, topic=None, last_articles=[])
    await state.set_state(None)
    await message.answer(
        "Выберите фильтры (или нажмите ✅ Выполнить поиск):",
        reply_markup=make_filter_keyboard(),
    )


@router.message(F.text == "👤 Автор")
async def filter_author(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("query"):
        await message.answer("Сначала введите запрос через /search.")
        return
    await state.set_state(SearchStates.waiting_for_author)
    await message.answer("Введите автора (точное совпадение):")


@router.message(SearchStates.waiting_for_author)
async def process_author(message: Message, state: FSMContext) -> None:
    await state.update_data(author=message.text.strip())
    await state.set_state(None)
    await message.answer("Фильтр по автору установлен.", reply_markup=make_filter_keyboard())


@router.message(F.text == "📅 Дата")
async def filter_date(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("query"):
        await message.answer("Сначала введите запрос через /search.")
        return
    await state.set_state(SearchStates.waiting_for_date)
    await message.answer("Введите дату в формате YYYY-MM-DD:")


@router.message(SearchStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext) -> None:
    await state.update_data(date=message.text.strip())
    await state.set_state(None)
    await message.answer("Фильтр по дате установлен.", reply_markup=make_filter_keyboard())


@router.message(F.text == "🏷️ Тема")
async def filter_topic(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("query"):
        await message.answer("Сначала введите запрос через /search.")
        return
    await state.set_state(SearchStates.waiting_for_topic)
    await message.answer("Введите тематику (как в базе, например 'ИИ'):")


@router.message(SearchStates.waiting_for_topic)
async def process_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=message.text.strip())
    await state.set_state(None)
    await message.answer("Фильтр по теме установлен.", reply_markup=make_filter_keyboard())


@router.message(F.text == "♻️ Сбросить фильтры")
async def reset_filters(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    query = data.get("query")
    if not query:
        await message.answer("Фильтры сброшены. Используйте /search для нового запроса.", reply_markup=make_filter_keyboard())
        await state.clear()
        return
    await state.update_data(author=None, date=None, topic=None)
    await message.answer("Фильтры сброшены. Нажмите ✅ Выполнить поиск.", reply_markup=make_filter_keyboard())


def format_search_response(resp: SearchResponse) -> str:
    summary = escape(resp.summary or "Результаты поиска")
    text = f"<b>{summary}</b>\n\n"

    if not resp.articles:
        return text + "Ничего не найдено."

    for idx, art in enumerate(resp.articles[:10], start=1):
        title = escape(art.title or "Без названия")
        author = escape(art.author or "—")
        date = escape(art.date or "—")
        topic = escape(art.topic or "—")
        url = art.url or ""

        text += (
            f"{idx}. <a href='{url}'>{title}</a>\n"
            f"   Автор: {author} | Дата: {date} | Тема: {topic}\n\n"
        )

    if len(text) > 4000:
        text = text[:4000] + "... (результат усечён)"

    return text


@router.message(F.text == "✅ Выполнить поиск")
async def run_search(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    query = data.get("query")
    if not query:
        await message.answer("Сначала введите запрос через /search.")
        return

    await message.answer("Ищу статьи…")

    client = get_rag_client()
    try:
        resp = await client.search(
            query=query,
            author=data.get("author"),
            date=data.get("date"),
            topic=data.get("topic"),
        )
    except Exception as e:
        tb = traceback.format_exc()
        await message.answer(
            "❌ Ошибка при поиске. Попробуйте позже.\n"
            f"{tb}"
        )
        return

    # Save for callbacks
    last_articles = [a.model_dump() for a in resp.articles]
    await state.update_data(last_articles=last_articles)

    text = format_search_response(resp)
    inline_kb = make_post_search_inline_keyboard(last_articles)

    await message.answer(text, parse_mode="HTML", disable_web_page_preview=False, reply_markup=inline_kb)


@router.callback_query(F.data.startswith("rec:"))
async def cb_recommend(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    last_articles: List[Dict[str, Any]] = data.get("last_articles") or []
    if not last_articles:
        await call.answer("Нет данных для рекомендаций. Сначала выполните поиск.", show_alert=True)
        return

    try:
        idx = int(call.data.split(":", 1)[1])
    except Exception:
        await call.answer("Некорректная команда.", show_alert=True)
        return

    if idx < 0 or idx >= len(last_articles):
        await call.answer("Статья не найдена.", show_alert=True)
        return

    seed_url = last_articles[idx].get("url")
    if not seed_url:
        await call.answer("Нет URL для выбранной статьи.", show_alert=True)
        return

    await call.answer("Ищу похожие…")

    client = get_rag_client()
    try:
        resp = await client.recommend(seed_url=seed_url, top_k=5)
    except Exception:
        await call.message.answer("❌ Ошибка при получении рекомендаций.")
        return

    # Update last_articles to enable chaining
    new_last = [a.model_dump() for a in resp.articles]
    await state.update_data(last_articles=new_last)

    text = format_search_response(resp)
    inline_kb = make_post_search_inline_keyboard(new_last)
    await call.message.answer(text, parse_mode="HTML", disable_web_page_preview=False, reply_markup=inline_kb)


@router.callback_query(F.data == "quiz")
async def cb_quiz(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    last_articles: List[Dict[str, Any]] = data.get("last_articles") or []
    if not last_articles:
        await call.answer("Нет статей для теста. Сначала выполните поиск.", show_alert=True)
        return

    urls = [a.get("url") for a in last_articles if a.get("url")]
    if not urls:
        await call.answer("Не удалось собрать ссылки на статьи.", show_alert=True)
        return

    await call.answer("Генерирую тест…")

    client = get_rag_client()
    try:
        resp = await client.quiz(urls=urls[:5], n_questions=8)
    except Exception:
        await call.message.answer("❌ Ошибка при генерации теста.")
        return

    # quiz response: summary contains the quiz text; articles = sources
    text = format_search_response(resp)
    inline_kb = make_post_search_inline_keyboard([a.model_dump() for a in resp.articles])
    await call.message.answer(text, parse_mode="HTML", disable_web_page_preview=False, reply_markup=inline_kb)
