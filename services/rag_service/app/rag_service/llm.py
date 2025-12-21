from typing import Protocol
import os


class LLM(Protocol):
    def generate(self, prompt: str) -> str: ...


class LlamaCppLLM:
    def __init__(self, model_path: str, n_ctx: int, max_tokens: int, temperature: float, top_p: float, n_gpu_layers: int) -> None:
        from llama_cpp import Llama

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"LLM model file not found: {model_path}")

        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p

        # One Llama instance = one context (CUDA if built with CUDA + n_gpu_layers > 0)
        self._llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

    def generate(self, prompt: str) -> str:
        out = self._llm(
            prompt,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            stop=["</s>"],
        )
        return (out["choices"][0]["text"] or "").strip()
