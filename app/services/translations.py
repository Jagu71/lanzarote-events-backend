from app.models.event import EventTranslation


def pick_event_translation(translations: list[EventTranslation], preferred_language: str) -> EventTranslation:
    ordered = {translation.language: translation for translation in translations}
    for language in [preferred_language, "es", "en", "de", "fr"]:
        if language in ordered:
            return ordered[language]
    return translations[0]
