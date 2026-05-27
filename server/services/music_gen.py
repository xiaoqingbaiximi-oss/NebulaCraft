"""
内置音乐生成引擎
基于 MIDI + 算法作曲，纯本地运行
支持: 旋律生成 / 和弦进行 / 多风格
"""
import os
import time
import random
import math
from midiutil import MIDIFile
from server.config import OUTPUT_DIR

MUSIC_DIR = os.path.join(OUTPUT_DIR, "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

# 音阶定义
SCALES = {
    "C": [60, 62, 64, 65, 67, 69, 71, 72],  # C大调
    "D": [62, 64, 66, 67, 69, 71, 73, 74],
    "E": [64, 66, 68, 69, 71, 73, 75, 76],
    "F": [65, 67, 69, 70, 72, 74, 76, 77],
    "G": [67, 69, 71, 72, 74, 76, 78, 79],
    "A": [69, 71, 73, 74, 76, 78, 80, 81],
    "B": [71, 73, 75, 76, 78, 80, 82, 83],
    "Am": [69, 71, 72, 74, 76, 77, 79, 81],  # A小调
    "Em": [64, 66, 67, 69, 71, 72, 74, 76],
}

# 和弦进行模板
CHORD_PROGRESSIONS = {
    "happy":    [("C", "M"), ("G", "M"), ("Am", "m"), ("F", "M")],
    "sad":      [("Am", "m"), ("F", "M"), ("C", "M"), ("G", "M")],
    "energetic":[("C", "M"), ("F", "M"), ("G", "M"), ("C", "M")],
    "relaxed":  [("F", "M"), ("C", "M"), ("Am", "m"), ("G", "M")],
    "mysterious":[("Am", "m"), ("Dm", "m"), ("E", "M"), ("Am", "m")],
}

# 和弦音符映射
CHORD_NOTES = {
    "C": [60, 64, 67], "D": [62, 66, 69], "E": [64, 68, 71],
    "F": [65, 69, 72], "G": [67, 71, 74], "A": [69, 73, 76],
    "B": [71, 75, 78], "Am": [69, 72, 76], "Dm": [62, 65, 69],
    "Em": [64, 67, 71],
}

# 鼓组音符
DRUM_NOTES = {
    "kick": 36, "snare": 38, "hihat_closed": 42, "hihat_open": 46,
}

class MusicGenEngine:
    def __init__(self):
        pass

    def generate_melody(self, scale_name="C", num_measures=8, tempo=120, style="happy"):
        """生成旋律 MIDI"""
        scale = SCALES.get(scale_name, SCALES["C"])
        rng = random.Random(sum(ord(c) for c in scale_name + style) + int(time.time()) % 1000)

        midi = MIDIFile(2)  # 2轨：旋律 + 打击乐
        midi.addTempo(0, 0, tempo)
        midi.addTempo(1, 0, tempo)

        # 旋律轨
        beat_duration = 0.5  # 八分音符
        time_pos = 0
        prev_note = scale[len(scale)//2]

        for _ in range(num_measures * 8):  # 每小节8个八分音符
            # 随机选音阶内音符，避免跳太大
            candidates = [n for n in scale if abs(n - prev_note) <= 5]
            if not candidates:
                candidates = scale
            note = rng.choice(candidates)
            velocity = rng.randint(70, 110)
            midi.addNote(0, 0, note, time_pos, beat_duration * 0.9, velocity)
            time_pos += beat_duration
            prev_note = note

        # 打击乐轨
        self._add_drums(midi, 1, num_measures, tempo, rng)

        file_id = f"melody_{int(time.time() * 1000)}.mid"
        filepath = os.path.join(MUSIC_DIR, file_id)
        with open(filepath, "wb") as f:
            midi.writeFile(f)

        return {
            "ok": True,
            "url": f"/output/music/{file_id}",
            "scale": scale_name,
            "tempo": tempo,
            "style": style,
            "measures": num_measures,
            "format": "midi",
        }

    def generate_chords(self, progression_name="happy", tempo=120):
        """生成和弦进行"""
        progression = CHORD_PROGRESSIONS.get(progression_name, CHORD_PROGRESSIONS["happy"])

        midi = MIDIFile(1)
        midi.addTempo(0, 0, tempo)

        time_pos = 0
        for chord_name, chord_type in progression * 2:  # 重复两遍
            notes = CHORD_NOTES.get(chord_name, [60, 64, 67])
            for note in notes:
                midi.addNote(0, 0, note, time_pos, 1.8, 80)
            time_pos += 2

        file_id = f"chords_{int(time.time() * 1000)}.mid"
        filepath = os.path.join(MUSIC_DIR, file_id)
        with open(filepath, "wb") as f:
            midi.writeFile(f)

        return {
            "ok": True,
            "url": f"/output/music/{file_id}",
            "progression": progression_name,
            "tempo": tempo,
            "format": "midi",
        }

    def generate_full(self, scale="C", style="happy", tempo=120, measures=16):
        """生成完整乐曲：旋律 + 和弦 + 鼓"""
        chord_prog = CHORD_PROGRESSIONS.get(style, CHORD_PROGRESSIONS["happy"])
        scale_notes = SCALES.get(scale, SCALES["C"])
        rng = random.Random(sum(ord(c) for c in scale + style) + int(time.time()) % 1000)

        midi = MIDIFile(3)  # 3轨：旋律 + 和弦 + 鼓
        for track in range(3):
            midi.addTempo(track, 0, tempo)

        # 旋律轨
        time_pos = 0
        prev_note = scale_notes[len(scale_notes)//2]
        beat = 0.25
        for _ in range(measures * 16):
            candidates = [n for n in scale_notes if abs(n - prev_note) <= 7]
            if not candidates:
                candidates = scale_notes
            note = rng.choice(candidates)
            vel = rng.randint(65, 105)
            midi.addNote(0, 0, note, time_pos, beat * 0.8, vel)
            time_pos += beat
            prev_note = note

        # 和弦轨
        time_pos = 0
        for _ in range(measures // 2):
            for chord_name, _ in chord_prog:
                notes = CHORD_NOTES.get(chord_name, [60, 64, 67])
                for note in notes:
                    midi.addNote(1, 0, note, time_pos, 1.8, 70)
                time_pos += 2

        # 鼓轨
        self._add_drums(midi, 2, measures, tempo, rng)

        file_id = f"full_{int(time.time() * 1000)}.mid"
        filepath = os.path.join(MUSIC_DIR, file_id)
        with open(filepath, "wb") as f:
            midi.writeFile(f)

        return {
            "ok": True,
            "url": f"/output/music/{file_id}",
            "scale": scale,
            "style": style,
            "tempo": tempo,
            "measures": measures,
            "format": "midi",
        }

    def text_to_music(self, prompt, tempo=120):
        """根据文字描述生成音乐"""
        prompt_lower = prompt.lower()

        # 根据关键词选择参数
        if any(w in prompt_lower for w in ["快乐", "欢快", "happy", "开心"]):
            style = "happy"; scale = "C"
        elif any(w in prompt_lower for w in ["悲伤", "伤感", "sad", "难过"]):
            style = "sad"; scale = "Am"
        elif any(w in prompt_lower for w in ["能量", "燃", "energetic", "运动"]):
            style = "energetic"; scale = "E"
        elif any(w in prompt_lower for w in ["放松", "平静", "relax", "瑜伽"]):
            style = "relaxed"; scale = "F"
        elif any(w in prompt_lower for w in ["神秘", "悬疑", "mysterious"]):
            style = "mysterious"; scale = "Am"
        else:
            style = "happy"; scale = "C"

        if "快" in prompt_lower or "fast" in prompt_lower:
            tempo = 160
        elif "慢" in prompt_lower or "slow" in prompt_lower:
            tempo = 80

        return self.generate_full(scale=scale, style=style, tempo=tempo, measures=16)

    def _add_drums(self, midi, track, measures, tempo, rng):
        """添加鼓轨"""
        beat_duration = 60.0 / tempo / 2  # 八分音符时长
        for measure in range(measures):
            for beat in range(8):
                time_pos = (measure * 8 + beat) * beat_duration
                # 强拍踢鼓
                if beat % 4 == 0:
                    midi.addNote(track, 9, DRUM_NOTES["kick"], time_pos, 0.1, 100)
                # 弱拍军鼓
                if beat % 4 == 2:
                    midi.addNote(track, 9, DRUM_NOTES["snare"], time_pos, 0.1, 90)
                # 闭镲
                midi.addNote(track, 9, DRUM_NOTES["hihat_closed"], time_pos, 0.05, 60)


music_gen = MusicGenEngine()