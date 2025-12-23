from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from app.embeddings import resolve_device

logger = logging.getLogger(__name__)

@dataclass
class LocalGenerator:
    model_name: str
    device: str

    def __post_init__(self) -> None:
        self.device = resolve_device(self.device)
        logger.info("Loading gen model: %s (device=%s)", self.model_name, self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, use_fast=True)
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=dtype,
            device_map="auto" if self.device == "cuda" else None,
        )
        if self.device != "cuda":
            self.model.to(self.device)

    @torch.inference_mode()
    def summarize(self, query: str, contexts: list[dict[str, Any]], max_new_tokens: int = 360) -> str:
        sources_block = []
        for i, c in enumerate(contexts, start=1):
            s = c["source"]
            snippets = c["snippets"]
            sources_block.append(
                f"[{i}] title: {s.get('title','')}"
                f"author: {s.get('author','')}"
                f"platform: {s.get('platform','')}"
                f"pub_date: {s.get('pub_date','')}"
                f"url: {s.get('url','')}"
                f"snippets:- " + "\n- ".join(snippets)
            )
        context_text = "\n\n".join(sources_block)

        system = (
            "Ты — AI-агент для поиска и анализа статей технологических СМИ. "
            "Отвечай строго ТОЛЬКО на основе предоставленного контекста. "
            "Если контекста недостаточно — скажи об этом и попроси уточнить запрос. "
            "Обязательно укажи источники (url) и авторство. "
            "Не добавляй фактов или ссылок, которых нет в контексте."
        )
        user = (
            f"Запрос пользователя: {query}\n\n"
            f"Контекст (источники и фрагменты):\n{context_text}\n\n"
            "Сформируй:\n"
            "1) Аннотацию (5-10 предложений).\n"
            "2) Ключевые пункты (3-7 буллетов).\n"
            "3) Источники: нумерованный список, где каждый элемент соответствует [i] из контекста и содержит "
            "title, author, platform, pub_date, url.\n"
        )

        messages = [{"role":"system","content":system},{"role":"user","content":user}]
        try:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            prompt = system + "\n\n" + user + "\n\nОтвет:"

        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.2,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        if "Ответ:" in text:
            text = text.split("Ответ:")[-1].strip()
        return text.strip()
