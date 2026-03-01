from deep_translator import GoogleTranslator

def translate_city(name: str, source: str, target: str) -> str:
    try:
        return GoogleTranslator(source=source, target=target).translate(name)
    except Exception:
        return name