"""视频生成 API"""
from server.services.video_gen import video_gen


def handle(body):
    action = body.get("action", "text")

    if action == "text":
        return video_gen.generate_text_animation(
            body.get("text", ""),
            int(body.get("duration", 5)),
            body.get("style", "fade")
        )
    if action == "slideshow":
        return video_gen.generate_slideshow(
            body.get("images", []),
            int(body.get("duration", 3))
        )
    if action == "subtitles":
        return video_gen.generate_subtitles(body.get("text", ""))

    return {"ok": False, "error": f"未知操作: {action}"}