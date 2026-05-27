"""
音乐生成 API
"""
from server.services.music_gen import music_gen


def handle(body: dict) -> dict:
    action = body.get("action", "full")
    prompt = body.get("prompt", "")
    tempo = int(body.get("tempo", 120))

    if action == "melody":
        scale = body.get("scale", "C")
        style = body.get("style", "happy")
        measures = int(body.get("measures", 8))
        return music_gen.generate_melody(scale, measures, tempo, style)

    if action == "chords":
        progression = body.get("progression", "happy")
        return music_gen.generate_chords(progression, tempo)

    if action == "full" or action == "text":
        if prompt:
            return music_gen.text_to_music(prompt, tempo)
        scale = body.get("scale", "C")
        style = body.get("style", "happy")
        measures = int(body.get("measures", 16))
        return music_gen.generate_full(scale, style, tempo, measures)

    return {"ok": False, "error": f"Unknown action: {action}"}