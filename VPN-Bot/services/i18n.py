import json
import os
from config import DEFAULT_LANGUAGE


class I18n:
    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

    def _load(self, lang: str) -> dict:
        if lang not in self._cache:
            path = os.path.join(self._locales_dir, f"{lang}.json")
            fallback = os.path.join(self._locales_dir, f"{DEFAULT_LANGUAGE}.json")
            try:
                with open(path, encoding="utf-8") as f:
                    self._cache[lang] = json.load(f)
            except FileNotFoundError:
                with open(fallback, encoding="utf-8") as f:
                    self._cache[lang] = json.load(f)
        return self._cache[lang]

    def t(self, key: str, lang: str = DEFAULT_LANGUAGE, **kwargs) -> str:
        data = self._load(lang)
        text = data.get(key) or self._load(DEFAULT_LANGUAGE).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text


i18n = I18n()
