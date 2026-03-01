import json
import os
from contextvars import ContextVar

ctx_lang: ContextVar[str] = ContextVar("ctx_lang", default="ru")

class Translator:
    def __init__(self):
        self.locales = {'ru': {}, 'lv': {}}
        self.load_locales()

    def load_locales(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_path = os.path.join(base_path, 'locales')
        
        for root, dirs, files in os.walk(root_path):
            for file in files:
                if file.endswith(".json"):
                    lang = 'ru' if file.endswith('_ru.json') else 'lv'
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if not content:
                                print(f"⚠️ Файл пуст: {path}")
                                continue
                            data = json.loads(content)
                            self.locales[lang].update(data)
                            print(f"✅ Успешно загружен: {file}")
                    except json.JSONDecodeError as e:
                        print(f"❌ ОШИБКА В JSON ({file}): {e}")
                    except Exception as e:
                        print(f"❌ Не удалось прочитать {file}: {e}")

    def __call__(self, key: str, **kwargs) -> str:
        lang = ctx_lang.get()
        text = self.locales.get(lang, {}).get(key, self.locales['ru'].get(key, key))
        return text.format(**kwargs) if kwargs else text

_ = Translator()