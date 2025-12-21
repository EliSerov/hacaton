const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Tech Media RAG MVP";

function titleSlide(title, subtitle) {
  const slide = pptx.addSlide();
  slide.addText(title, { x: 0.6, y: 1.2, w: 12.2, h: 0.8, fontSize: 40, bold: true });
  slide.addText(subtitle, { x: 0.6, y: 2.3, w: 12.2, h: 0.6, fontSize: 20 });
  slide.addText("Cloud.ru — AI-агент для поиска и анализа статей (MVP)", { x: 0.6, y: 6.6, w: 12.2, h: 0.4, fontSize: 14 });
}

function bulletsSlide(title, bullets) {
  const slide = pptx.addSlide();
  slide.addText(title, { x: 0.6, y: 0.5, w: 12.2, h: 0.6, fontSize: 28, bold: true });
  const text = bullets.map(b => `• ${b}`).join("\n");
  slide.addText(text, { x: 0.9, y: 1.4, w: 12.0, h: 5.8, fontSize: 18, valign: "top" });
}

titleSlide("Tech Media RAG MVP", "Интеллектуальный поиск и анализ статей технологических СМИ");

bulletsSlide("Проблема и цель", [
  "Статей много, поиск по ключевым словам не покрывает смыслы и контекст",
  "Нужен агент: найти релевантные материалы, кратко резюмировать, дать ссылки на источники",
  "ЦА: студенты и специалисты, потребляющие IT-контент"
]);

bulletsSlide("MVP функциональность", [
  "RAG-пайплайн: эмбеддинги запроса → поиск в Qdrant → генерация ответа",
  "Аннотационное резюме с цитированием источников [n]",
  "Фильтры: автор, дата, тематика",
  "Доп. функции: рекомендации похожих публикаций; генерация вопросов/теста",
  "Интерфейс: Telegram-бот"
]);

bulletsSlide("Архитектура (микросервисы)", [
  "telegram-bot-service: UI/диалоги, фильтры, RPC в rag-service",
  "rag-service (GPU): retrieval + LLM summary/quiz/recommend (один CUDA-контекст)",
  "indexer-service: CSV → чанки → эмбеддинги → Qdrant upsert",
  "Транспорт: RabbitMQ RPC; Векторное хранилище: Qdrant"
]);

bulletsSlide("Этичность и безопасность", [
  "Точные ссылки на источники и запрет на 'галлюцинации' в промпте",
  "Защита данных: минимизация логируемого текста, trace_id для трассировки",
  "Аутентификация: Telegram user_id; Авторизация: allowlist",
  "Service-to-service: API key в AMQP headers"
]);

bulletsSlide("Дальнейшее развитие", [
  "Reranker и гибридный поиск (dense+sparse/BM25)",
  "Мультиязычность RU+EN, новые источники и дисциплины",
  "Загрузка PDF/HTML, планировщик переиндексации",
  "Кэширование и масштабирование компонентов"
]);

pptx.writeFile({ fileName: "docs/presentation.pptx" });
