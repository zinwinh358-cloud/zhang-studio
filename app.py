# မြန်မာစာတန်းထိုး + အသံဖတ်ပြ App (Gradio + Gemini + Edge TTS) — Cell တစ်ခု တည်း — v2
# v2 အသစ်များ:
# 1) Key ကို Colab Secrets (GEMINI_API_KEY) မှာ တစ်ခါ သိမ်းထားရင် ထပ်ထည့်စရာ မလိုဘူး။
# 2) Tab 2 အသစ်: စာရိုက်ထည့် → AI အသံဖတ်ပြ + အသံနဲ့ ကိုက်တဲ့ စာတန်း (SRT) ပါ ထုတ်ပေးမယ်။
#    အသံ: Nilar (အမျိုးသမီး) / Thiha (အယောက်ျား) + အမြန်/အနှေး + အသံအနိမ့်အမြင့် ရွေးနိုင်တယ်။
# လုပ်ပုံ: ဒီ Cell ကို run → ပေါ်လာတဲ့ public link ကို ဖွင့် → Tab ရွေး → လုပ်ဆောင်ပါ။
# Untitled2.ipynb (သို့) notebook အသစ် မှာ သုံးနိုင်တယ် — 2026-11-13
# v3 (2026-11-13): App နာမည် "Zhang စတူတီယို" + banner ပုံ။
# v4 (2026-11-13): နာမည် "Zhang Studio" (အင်္ဂလိပ်) + favicon (home-screen icon အတွက်)။
# v5 (2026-11-13): စာတန်းအချိန် တိကျအောင် — Gemini ကို cue အတိုတွေ တောင်းခြင်း + ရှည်တဲ့ cue တွေ 5 စက္ကန့်အောက် ခွဲခြင်း။
# v6 (2026-11-13): မြန်အောင် — install ပြီးသားဆို ကျော်ခြင်း + encode ultrafast။
# v7 (2026-11-13): Colab + Hugging Face Spaces နှစ်ခုလုံး အလုပ်ဖြစ်အောင် — env var Key, local ပုံများ, Spaces မှာ share ပိတ်။
# v8 (2026-11-13): Render.com (အခမဲ့ အမြဲ link) ပါ အလုပ်ဖြစ်အောင် — RENDER env ရှိရင် 0.0.0.0:$PORT မှာ run, share ပိတ်, font install ကျော်။
# v9 (2026-11-13): Render အခမဲ့ CPU မှာ မြန်အောင် — output ကို အရှည်ဆုံး ဘက် 1280 အထိ ချုံ့ + SRT ကို အရင် ပြခြင်း (video စောင့်နေစဉ် SRT ရပြီ)။
# v10 (2026-11-13): Gemini call တစ်ခု ငြိမ်သွားရင် (read timeout) အလုပ်ရပ်မသွားအောင် — model တစ်ခုချင်းစီကို try/except နဲ့ ကာ + timeout 180s + နောက် model ကို အလိုလို ပြောင်းသုံးခြင်း။
# v11 (2026-11-13): Burn မြန်အောင် — cue PNG တွေကို frame အပြည့် အစား အောက်ခြေ band လေးပဲ ဆွဲခြင်း (overlay=0:<y>) + gemini-3.6-flash ကို ပထမ model အဖြစ် ထားခြင်း (3.8-flash 2 ခါ ငြိမ်သွားလို့)။
# v12 (2026-11-13): ဘာသာပြန် — မြန်မာစကား မဟုတ်ရင် အသံကို အဓိပ္ပာယ် ဘာသာပြန်ပြီး မြန်မာစာတန်း ထုတ်ခြင်း (အသံထွက် အတိုင်း မြန်မာစာလုံးနဲ့ ရေးခြင်း လုံးဝ မလုပ်ရ)။
# v13 (2026-11-13): Android API — POST /api/transcribe (video → SRT, sync)။
# v14 (2026-11-13): async jobs — /api/transcribe က job_id ပြန်ပေးပြီး /api/status/{job_id} ကို poll လုပ်ခြင်း + ကိုယ့် API Key ထည့်သုံးနိုင်ခြင်း။
# v15 (2026-11-13): TTS API — POST /api/tts (စာသား → AI အသံ + SRT, async) + GET /api/download/{job_id}/audio။
# v16 (2026-11-13): Voiceover API — POST /api/voiceover (video → Gemini စာသား → AI မြန်မာအသံ → ffmpeg နဲ့ Video ထဲ အသံထည့်) + GET /api/download/{job_id}/video။

import glob
import os
import subprocess
import sys


def _have_myanmar_font():
    for pat in ("/usr/share/fonts/truetype/padauk/*.ttf",
                "/usr/share/fonts/**/NotoSansMyanmar-Regular.ttf"):
        if glob.glob(pat, recursive=True):
            return True
    return False


print("📦 လိုအပ်တာ စစ်နေတယ်...")
try:
    import gradio  # noqa: F401
    import edge_tts  # noqa: F401
    print("✅ လိုအပ်တာ ရှိနေပြီ — install ကျော်မယ်။")
except Exception:
    print("📦 လိုအပ်တာ install လုပ်နေတယ်...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio", "edge-tts"],
                   capture_output=True, timeout=600)
    print("✅ install ပြီးပြီ။")
if not os.environ.get("SPACE_ID") and not os.environ.get("RENDER") and not _have_myanmar_font():
    subprocess.run(["bash", "-c", "apt-get update -qq && apt-get install -y -qq fonts-sil-padauk"],
                   capture_output=True, timeout=300)

import asyncio
import base64
import concurrent.futures
import math
import re
import tempfile
import urllib.request

import gradio as gr
import requests
from PIL import Image, ImageDraw, ImageFont, features

print("🔤 မြန်မာစာ ပုံဖော်စနစ် (raqm):", features.check("raqm"))

# Key သိမ်းတဲ့နေရာ: (1) Hugging Face Secrets / env var, (2) Colab Secrets
SECRET_KEY = os.environ.get("GEMINI_API_KEY") or None
if not SECRET_KEY:
    try:
        from google.colab import userdata
        SECRET_KEY = userdata.get("GEMINI_API_KEY") or None
    except Exception:
        SECRET_KEY = None
print("Secrets Key:", bool(SECRET_KEY))

# Banner + favicon ပုံများ: အရင် ဘေးက ဖိုင် (Spaces repo) ကို သုံး, မရှိရင် download (Colab)
def _local_or_download(local_name, url):
    if os.path.exists(local_name):
        return local_name
    try:
        tmp = os.path.join(tempfile.gettempdir(), local_name)
        urllib.request.urlretrieve(url, tmp)
        return tmp
    except Exception:
        return None


BANNER_PATH = _local_or_download(
    "zhang-studio-banner.jpg",
    "https://muse.ai/files/1475283228992014/1126674410148409/izq6th343rb182atej9wy43u/zhang-studio-banner.jpg")
FAVICON_PATH = _local_or_download(
    "zhang-studio-favicon.png",
    "https://muse.ai/files/1475283228992014/1148245037715311/56ul0wu34oapc6mosgqmm17z/zhang-studio-favicon.png")

CANDIDATE_MODELS = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite",
                    "gemini-3.7-flash", "gemini-flash-latest", "gemini-3.5-flash",
                    "gemini-2.5-flash", "gemini-2.0-flash"]

VOICES = {"အမျိုးသမီး အသံ (Nilar)": "my-MM-NilarNeural",
          "အယောက်ျား အသံ (Thiha)": "my-MM-ThihaNeural"}


def find_myanmar_font():
    for pat in ("/usr/share/fonts/truetype/padauk/Padauk-Regular.ttf",
                "/usr/share/fonts/truetype/padauk/*.ttf",
                "/usr/share/fonts/**/NotoSansMyanmar-Regular.ttf"):
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return None


def probe_video(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height",
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1", path],
                       capture_output=True, text=True, errors="ignore", timeout=60)
    vals = {}
    for line in r.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return int(vals["width"]), int(vals["height"]), float(vals["duration"])


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", path],
                       capture_output=True, text=True, errors="ignore", timeout=60)
    return float(r.stdout.strip())


def to_seconds(ts):
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s.replace(",", "."))


def format_time(seconds):
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


# ---------------- Tab 1: video စာတန်းထိုး ----------------

def transcribe_with_gemini(api_key, audio_path, duration):
    with open(audio_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    prompt = (
        "Listen to this audio. First detect the spoken language. "
        "If the speech is in Myanmar (Burmese), transcribe EXACTLY what is said, word for word, "
        "in Myanmar script. "
        "If the speech is in ANY other language (Chinese, Thai, English, Indonesian, Korean, or any "
        "other), TRANSLATE the meaning into natural, fluent Myanmar (Burmese) language — translate "
        "the MEANING, not the sounds. "
        "NEVER write foreign-language sounds phonetically in Myanmar script (no transliteration). "
        "Every cue must be meaningful Myanmar words a Myanmar viewer can understand. "
        "Do not summarize, do not add explanations. "
        "Return ONLY a valid SRT subtitle file: numbered cues, each with start --> end timestamps "
        "in HH:MM:SS,mmm format. Pay close attention to WHEN each phrase starts and ends — "
        "the timestamps must match the speech exactly, not approximately. "
        "Use MANY SHORT cues: each cue at most 5 seconds, one short phrase "
        "per cue, with the most accurate timestamps you can estimate. Never put a whole paragraph "
        "in one cue. If a word is unclear, write your best guess."
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "audio/mpeg", "data": audio_b64}}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    for name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=180)
        except requests.exceptions.RequestException:
            continue
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                continue
            cands = data.get("candidates", [])
            parts = cands[0].get("content", {}).get("parts", []) if cands else []
            texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
            if texts:
                return name, "\n".join(texts)
            continue
        if resp.status_code in (404, 503, 429):
            continue
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    raise RuntimeError("model တွေ အကုန် အလုပ်များနေတယ် (သို့) စာသား ပြန်မပေးဘူး။ ခဏစောင့်ပြီး ထပ်နှိပ်ပါ။")


def parse_srt_text(raw_text, duration):
    clean = re.sub(r"```\w*", "", raw_text).strip()
    ts_re = re.compile(r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})")
    lines = clean.splitlines()
    cues = []
    i = 0
    while i < len(lines):
        m = ts_re.match(lines[i].strip())
        if m:
            start = to_seconds(m.group(1))
            end = to_seconds(m.group(2))
            j = i + 1
            text_parts = []
            while j < len(lines):
                ln = lines[j].strip()
                if ln == "" or re.match(r"^\d+$", ln) or ts_re.match(ln):
                    break
                text_parts.append(ln)
                j += 1
            text = " ".join(text_parts)
            if text:
                cues.append((start, end, text))
            i = j
        else:
            i += 1
    if not cues:
        text_lines = []
        for ln in clean.splitlines():
            ln = ln.strip()
            if not ln or ln.isdigit() or "-->" in ln:
                continue
            text_lines.append(ln)
        if not text_lines:
            raise RuntimeError("Gemini က စာသား ပြန်မပေးဘူး။ ထပ်စမ်းကြည့်ပါ။")
        n = len(text_lines)
        for k, ln in enumerate(text_lines):
            cues.append((duration * k / n, duration * (k + 1) / n, ln))
    fixed = []
    for start, end, text in cues:
        end = min(end, duration)
        if end <= start:
            end = min(start + 1.0, duration)
        fixed.append((start, end, text))
    return fixed


def split_long_cues(cues, max_dur=5.0):
    # ရှည်တဲ့ cue (ဥပမာ 16 စက္ကန့် တစ်ပိုင်း) ကို အတိုလေးတွေ ခွဲခြင်း —
    # စာသား အရှည်အလိုက် အချိန် ခွဲဝေတယ် (အသံနဲ့ လိုက်ဖက် ပိုနီးစပ်အောင်)
    out = []
    for start, end, text in cues:
        dur = end - start
        n = max(1, math.ceil(dur / max_dur))
        if n <= 1:
            out.append((start, end, text))
            continue
        parts = [p.strip() for p in re.split(r"(?<=[။,])\s*", text.strip()) if p.strip()]
        if len(parts) < n:
            words = text.split(" ")
            target = max(1, len(text) // n)
            parts, cur = [], ""
            for w in words:
                if cur and len(cur) + len(w) + 1 > target:
                    parts.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            if cur:
                parts.append(cur)
        total = sum(len(p) for p in parts) or 1
        t = start
        for k, p in enumerate(parts):
            share = dur * len(p) / total
            e = end if k == len(parts) - 1 else t + share
            out.append((t, e, p))
            t = e
    return out


def wrap_text(draw, text, font, max_w):
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            while draw.textlength(word, font=font) > max_w:
                cut = len(word)
                while cut > 1 and draw.textlength(word[:cut], font=font) > max_w:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_cue_png(text, w, h, font_path, font_size, out_path):
    # Band-sized PNG: အောက်ခြေ စာတန်း အပိုင်းလေးပဲ ဆွဲမယ် (frame အပြည့် မဟုတ်ဘူး) —
    # overlay filter က pixel နည်းနည်းပဲ ရောရတော့ burn မြန်တယ်။ စာရဲ့ နေရာအတိအကျ မပြောင်းဘူး။
    font = ImageFont.truetype(font_path, font_size)
    measure = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    lines = wrap_text(measure, text, font, int(w * 0.9))
    line_h = font_size + int(font_size * 0.35)
    stroke = max(2, font_size // 16)
    pad = stroke + 4
    band_h = line_h * len(lines) + 2 * pad
    band_top = h - int(h * 0.08) - line_h * len(lines) - pad
    band_top = max(0, band_top)
    band_h = min(band_h, h - band_top)
    img = Image.new("RGBA", (w, band_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = pad
    for ln in lines:
        tw = draw.textlength(ln, font=font)
        x = (w - tw) / 2
        draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += line_h
    img.save(out_path)
    return band_top


def burn_subtitles(video_path, cues, out_path, font_path):
    w, h, duration = probe_video(video_path)
    # Render အခမဲ့ CPU (0.1) မှာ မြန်အောင် — အရှည်ဆုံး ဘက်ကို 1280 အထိ ချုံ့မယ်။
    scale = 1280 / max(w, h) if max(w, h) > 1280 else 1.0
    sw = max(2, int(w * scale) // 2 * 2)
    sh = max(2, int(h * scale) // 2 * 2)
    font_size = max(24, int(sh * 0.045))
    tmpdir = tempfile.mkdtemp(prefix="cues_")
    pngs = []
    for k, (start, end, text) in enumerate(cues):
        p = os.path.join(tmpdir, f"cue_{k}.png")
        y_off = render_cue_png(text, sw, sh, font_path, font_size, p)
        pngs.append((p, start, end, y_off))
    cmd = ["ffmpeg", "-y", "-i", video_path]
    for p, _, _, _ in pngs:
        cmd += ["-loop", "1", "-t", str(duration), "-i", p]
    filt = f"[0:v]scale={sw}:{sh}[base];"
    prev = "base"
    for k, (_, start, end, y_off) in enumerate(pngs):
        out = f"v{k}"
        filt += f"[{prev}][{k + 1}:v]overlay=0:{y_off}:enable='between(t,{start:.3f},{end:.3f})'[{out}];"
        prev = out
    cmd += ["-filter_complex", filt.rstrip(";"),
            "-map", f"[{prev}]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "copy", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", timeout=1800)
    if r.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError("video ထဲ စာတန်း ထည့်လို့ မရဘူး: " + r.stderr[-300:])


# ---------------- Exact timing (v18) ----------------
# Gemini ရဲ့ timestamp တွေက ခန့်မှန်းချက်ပဲ ဖြစ်လို့ အချိန်လွဲနိုင်တယ်။
# တိကျအောင်: (1) အသံတိတ်နေတဲ့ နေရာတွေမှာ အပိုင်းခွဲပြီး တစ်ပိုင်းစီ
# သီးသန့် နားထောင်ခိုင်းတယ် (အပိုင်းတိုလေ timestamp တိကျလေ);
# (2) အသံဆက်နေတဲ့ clip တွေအတွက် 6-စက္ကန့် ပြတင်းပေါက်တွေနဲ့ ခွဲတယ်;
# (3) cue တွေရဲ့ အစ/အဆုံးကို အသံစတင်/ရပ်တဲ့ နေရာတွေနဲ့ ကပ်ပေးတယ်။
# Chunk တစ်ခု မရရင် တစ်ခုလုံး နားထောင်တဲ့ နည်းလမ်း (အဟောင်း) ကို ပြန်သုံးတယ်။

def detect_speech_segments(audio_path, duration):
    """ffmpeg silencedetect -> speech intervals [(start, end)]."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-i", audio_path, "-af",
             "silencedetect=noise=-35dB:d=0.5", "-f", "null", "-"],
            capture_output=True, text=True, errors="ignore", timeout=300)
    except Exception:
        return []
    silences = []
    cur_start = None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m:
            cur_start = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m and cur_start is not None:
            silences.append((cur_start, float(m.group(1))))
            cur_start = None
    if cur_start is not None:
        silences.append((cur_start, duration))
    segments = []
    pos = 0.0
    for s, e in silences:
        if s > pos:
            segments.append((pos, min(s, duration)))
        pos = max(pos, e)
    if pos < duration:
        segments.append((pos, duration))
    return [(s, e) for s, e in segments if e - s >= 0.3]


def snap_cues_to_speech(cues, segments, duration, window=0.6):
    """Snap each cue's start/end to the nearest speech-segment boundary
    within `window` seconds (fixes subtitles appearing in silence)."""
    if not segments or not cues:
        return cues
    starts = [s for s, _ in segments]
    ends = [e for _, e in segments]
    out = []
    prev_end = 0.0
    for start, end, text in cues:
        ns = start
        best = min(starts, key=lambda b: abs(b - start))
        if abs(best - start) <= window:
            ns = best
        ne = end
        best_e = min(ends, key=lambda b: abs(b - end))
        if abs(best_e - end) <= window:
            ne = best_e
        ns = max(prev_end, min(ns, duration))
        ne = max(ns + 0.2, min(ne, duration))
        out.append((ns, ne, text))
        prev_end = ne
    return out


def transcribe_cues(key, audio_path, duration, workdir):
    """Audio -> (model name, cues) with tighter timestamps.
    Chunked transcription for short clips (VAD segments, else 6s windows),
    whole-audio fallback, then boundary snapping."""
    segments = detect_speech_segments(audio_path, duration)
    usable = [seg for seg in segments if seg[1] - seg[0] >= 0.8]
    merged = []
    for s, e in usable:
        if merged and s - merged[-1][1] < 0.5:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    windows = None
    if duration <= 90 and 1 < len(merged) <= 12:
        windows = merged
    elif duration <= 60:
        # Continuous speech: fixed 6s windows (last one absorbs <2s tail).
        windows = []
        t = 0.0
        while t < duration:
            nxt = t + 6.0
            if duration - nxt < 2.0:
                nxt = duration
            windows.append((t, nxt))
            t = nxt
        if len(windows) > 10:
            windows = None
    if windows:
        try:
            all_cues = []
            model_name = None
            for idx, (s, e) in enumerate(windows):
                seg_path = os.path.join(workdir, f"chunk{idx}.mp3")
                seg_dur = e - s
                r = subprocess.run(
                    ["ffmpeg", "-y", "-ss", f"{s:.3f}", "-i", audio_path,
                     "-t", f"{seg_dur:.3f}", "-c:a", "libmp3lame", "-q:a", "4",
                     seg_path],
                    capture_output=True, text=True, errors="ignore", timeout=300)
                if r.returncode != 0 or not os.path.exists(seg_path):
                    raise RuntimeError("segment extract failed")
                m, raw = transcribe_with_gemini(key, seg_path, seg_dur)
                model_name = model_name or m
                seg_cues = split_long_cues(split_long_cues(
                    parse_srt_text(raw, seg_dur)))
                for (cs, ce, t) in seg_cues:
                    all_cues.append((cs + s, min(ce + s, duration), t))
            if all_cues:
                all_cues.sort(key=lambda c: c[0])
                return model_name, snap_cues_to_speech(all_cues, segments, duration)
        except Exception:
            pass  # fall through to whole-audio below
    model_name, raw_text = transcribe_with_gemini(key, audio_path, duration)
    cues = split_long_cues(split_long_cues(parse_srt_text(raw_text, duration)))
    return model_name, snap_cues_to_speech(cues, segments, duration)


def transcribe_video_file(video_path, api_key=None):
    """Video file -> (model name, SRT text). Used by the /api/transcribe
    endpoint (Android app). Same pipeline as Tab 1, without the burn step:
    extract audio -> Gemini transcribe/translate -> parse -> short cues."""
    key = (api_key or "").strip() or SECRET_KEY
    if not key:
        raise RuntimeError("GEMINI_API_KEY not configured on the server")
    workdir = tempfile.mkdtemp(prefix="api_transcribe_")
    audio_path = os.path.join(workdir, "audio.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "libmp3lame", "-q:a", "4", audio_path],
                       capture_output=True, text=True, errors="ignore", timeout=600)
    if r.returncode != 0 or not os.path.exists(audio_path):
        raise RuntimeError("Could not extract audio — does the video have sound?")
    if os.path.getsize(audio_path) > 15_000_000:
        raise RuntimeError("Video too long — try a clip under 10 minutes")
    _, _, duration = probe_video(video_path)
    model_name, cues = transcribe_cues(key, audio_path, duration, workdir)
    parts = []
    for k, (start, end, text) in enumerate(cues):
        parts.append(f"{k + 1}\n{format_time(start)} --> {format_time(end)}\n{text}\n")
    return model_name, "\n".join(parts)


def process_subtitle(api_key, video):
    srt_text = ""
    srt_path = None
    try:
        key = (api_key or "").strip() or SECRET_KEY
        if not key:
            yield "⚠️ Gemini API Key ထည့်ပါ (သို့) Secrets မှာ GEMINI_API_KEY သိမ်းပါ။", "", None, None
            return
        if isinstance(video, dict):
            video = video.get("path") or video.get("name")
        if not video or not os.path.exists(video):
            yield "⚠️ ဗီဒီယို တင်ပါ။", "", None, None
            return
        workdir = tempfile.mkdtemp(prefix="subtitle_app_")
        base = os.path.splitext(os.path.basename(video))[0]
        audio_path = os.path.join(workdir, "audio.mp3")
        r = subprocess.run(["ffmpeg", "-y", "-i", video, "-vn", "-ac", "1", "-ar", "16000",
                            "-c:a", "libmp3lame", "-q:a", "4", audio_path],
                           capture_output=True, text=True, errors="ignore", timeout=600)
        if r.returncode != 0 or not os.path.exists(audio_path):
            yield "❌ အသံ ထုတ်လို့ မရဘူး။ video မှာ အသံပါလား စစ်ပါ။", "", None, None
            return
        if os.path.getsize(audio_path) > 15_000_000:
            yield "⚠️ Video အရမ်းရှည်တယ် — ၁၀ မိနစ်အောက် clip နဲ့ စမ်းပါ။", "", None, None
            return
        _, _, duration = probe_video(video)
        model_name, cues = transcribe_cues(key, audio_path, duration, workdir)
        srt_path = os.path.join(workdir, f"{base}_burmese.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            for k, (start, end, text) in enumerate(cues):
                f.write(f"{k + 1}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")
        with open(srt_path, encoding="utf-8") as f:
            srt_text = f.read()
        yield f"⏳ စာတန်း ရပြီ (model: {model_name}) — video ထဲ ထည့်နေတယ်…", srt_text, None, srt_path
        font_path = find_myanmar_font()
        if font_path is None:
            yield "⚠️ မြန်မာစာလုံး (font) ရှာမတွေ့ဘူး။ Cell ကို ပြန် run ပါ။", srt_text, None, srt_path
            return
        out_video = os.path.join(workdir, f"{base}_subtitled.mp4")
        burn_subtitles(video, cues, out_video, font_path)
        status = f"✅ ပြီးပါပြီ။ model: {model_name} — စာတန်း {len(cues)} ပိုင်း။"
        yield status, srt_text, out_video, srt_path
    except Exception as e:
        yield f"❌ Error: {e}", srt_text, None, srt_path


# ---------------- Tab 2: စာရိုက် → အသံဖတ်ပြ + စာတန်း ----------------

def split_sentences(text):
    parts = re.split(r"(?<=[။.?!])\s*", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text, max_chars=900):
    chunks, cur = [], ""
    for s in split_sentences(text):
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            while len(s) > max_chars:
                chunks.append(s[:max_chars])
                s = s[max_chars:]
            cur = s
    if cur:
        chunks.append(cur)
    return chunks


async def _edge_run(text, voice, rate, pitch):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    audio = bytearray()
    bounds = []
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            start = chunk["offset"] / 1e7
            bounds.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return bytes(audio), bounds


def edge_synthesize(text, voice, rate, pitch):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(asyncio.run, _edge_run(text, voice, rate, pitch))
        return fut.result(timeout=600)


def build_tts_cues(text, bounds, total_duration):
    sentences = split_sentences(text)
    if not sentences:
        sentences = [text.strip()]
    if not bounds:
        n = len(sentences)
        return [(total_duration * k / n, total_duration * (k + 1) / n, s)
                for k, s in enumerate(sentences)]

    def norm(s):
        return re.sub(r"\s+", "", s)

    # စာကြောင်းနဲ့ အသံ စကားလုံး အချိန်တွေ တိုက်စစ်ခြင်း (တိကျတဲ့ နည်း)
    cues = []
    wi = 0
    ok = True
    for s in sentences:
        target = norm(s)
        acc = ""
        start = bounds[wi][0] if wi < len(bounds) else total_duration
        end = start
        while wi < len(bounds) and len(acc) < len(target):
            acc += norm(bounds[wi][2])
            end = bounds[wi][1]
            wi += 1
        if acc != target:
            ok = False
            break
        cues.append((start, end, s))
    if ok and cues:
        return cues
    # တိုက်စစ် မရရင် စာလုံးအရေအတွက်အလိုက် အချိန်ခွဲခြင်း (အရန်နည်း)
    total_chars = sum(len(s) for s in sentences)
    n_words = len(bounds)
    cues = []
    used = 0
    for k, s in enumerate(sentences):
        if k < len(sentences) - 1:
            cnt = max(1, round(len(s) / total_chars * n_words))
            cnt = min(cnt, n_words - used)
        else:
            cnt = n_words - used
        if cnt <= 0:
            cues.append((total_duration, total_duration, s))
            continue
        cues.append((bounds[used][0], bounds[used + cnt - 1][1], s))
        used += cnt
    return cues


def synthesize_tts(text, voice, rate, pitch):
    """Text -> (mp3 path, SRT path, SRT text, total seconds, cue count, workdir).
    Shared by the Gradio Tab 2 UI and the /api/tts endpoint (Android app).
    Raises on failure; the caller formats the error for its own UI.
    `voice` is an edge-tts voice id (my-MM-NilarNeural / my-MM-ThihaNeural);
    `rate`/`pitch` are ints in [-50, 50]. The workdir is left on disk so the
    API can serve the mp3 afterwards; the job-pruning code deletes it."""
    text = (text or "").strip()
    if not text:
        raise RuntimeError("စာသား ရိုက်ထည့်ပါ။")
    rate_str = f"{int(rate):+d}%"
    pitch_str = f"{int(pitch):+d}Hz"
    workdir = tempfile.mkdtemp(prefix="tts_app_")
    chunks = chunk_text(text)
    chunk_files = []
    all_bounds = []
    shift = 0.0
    for i, ch in enumerate(chunks):
        audio, bounds = edge_synthesize(ch, voice, rate_str, pitch_str)
        if not audio:
            raise RuntimeError("အသံ ထုတ်လို့ မရဘူး။ ထပ်စမ်းကြည့်ပါ။")
        cf = os.path.join(workdir, f"part{i}.mp3")
        with open(cf, "wb") as f:
            f.write(audio)
        chunk_files.append(cf)
        dur = probe_duration(cf)
        for (s, e, w) in bounds:
            all_bounds.append((s + shift, e + shift, w))
        shift += dur
    list_path = os.path.join(workdir, "parts.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"file '{cf}'\n")
    out_mp3 = os.path.join(workdir, "narration.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                        "-c:a", "libmp3lame", "-q:a", "4", out_mp3],
                       capture_output=True, text=True, errors="ignore", timeout=600)
    if r.returncode != 0 or not os.path.exists(out_mp3):
        raise RuntimeError("အသံဖိုင် ပေါင်းလို့ မရဘူး: " + r.stderr[-200:])
    total = probe_duration(out_mp3)
    cues = build_tts_cues(text, all_bounds, total)
    srt_path = os.path.join(workdir, "narration.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for k, (start, end, s) in enumerate(cues):
            f.write(f"{k + 1}\n{format_time(start)} --> {format_time(end)}\n{s}\n\n")
    with open(srt_path, encoding="utf-8") as f:
        srt_text = f.read()
    return out_mp3, srt_path, srt_text, total, len(cues), workdir


# ---------------- Auto voice split by character (v20) ----------------
# AI က စာသားကို ဇာတ်ကောင် အလိုက် အပိုင်းခွဲပြီး မိန်းကလေး/ယောက်ျားလေး
# အသံ သင့်တော်ရာကို ခွဲပေးတယ်။ Gemini TEXT သုံးတယ် (Key လိုတယ်)။
# ခွဲတာ မအောင်မြင်ရင် အသံတစ်မျိုး (fallback voice) နဲ့ ဖတ်ပြတယ်။

VOICE_FEMALE = "my-MM-NilarNeural"
VOICE_MALE = "my-MM-ThihaNeural"


def split_voices(api_key, text):
    """Text -> [(segment_text, voice_id)] in order. Raises RuntimeError
    if no Gemini model returns a usable split; the caller falls back to
    a single voice. The joined segments must equal the original text
    (ignoring whitespace) — anything added, dropped or reworded fails."""
    import json
    instruction = (
        "You split a Myanmar (Burmese) story text into speaking parts by character, "
        "so each part can be read aloud in a suitable male or female voice. "
        "Rules: 1) Split ONLY at speaker changes (dialogue turns, or narration vs "
        "dialogue). Keep each part as long as possible — do not split every sentence. "
        "2) Copy the text EXACTLY, character for character — never add, remove or "
        "change a single word or punctuation mark. The parts joined together must "
        "equal the original text exactly. "
        "3) For each part choose \"female\" or \"male\": dialogue uses the speaking "
        "character's gender (infer from names, pronouns, and context); narration "
        "uses the main character's voice if clear, otherwise \"female\". "
        "4) If the text has only one speaker or no dialogue, return it as ONE part. "
        "Return ONLY valid JSON: a list of objects with keys \"text\" and \"voice\". "
        "No other text."
    )
    payload = {
        "contents": [{"parts": [{"text": instruction + "\n\nText:\n" + text}]}],
        "generationConfig": {"responseMimeType": "application/json"},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    def norm(s):
        return re.sub(r"\s+", "", s)

    want = norm(text)
    for name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
        except requests.exceptions.RequestException:
            continue
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                continue
            cands = data.get("candidates", [])
            parts = cands[0].get("content", {}).get("parts", []) if cands else []
            texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
            if not texts:
                continue
            raw = "\n".join(texts).strip()
            parsed = None
            try:
                parsed = json.loads(raw)
            except ValueError:
                try:
                    parsed = json.loads(re.sub(r"```\w*", "", raw).strip())
                except ValueError:
                    continue
            if not isinstance(parsed, list) or not parsed or len(parsed) > 80:
                continue
            segments = []
            ok = True
            for item in parsed:
                if not isinstance(item, dict):
                    ok = False
                    break
                seg = str(item.get("text", "")).strip()
                v = str(item.get("voice", "")).strip().lower()
                if not seg:
                    ok = False
                    break
                if v.startswith("f"):
                    voice = VOICE_FEMALE
                elif v.startswith("m"):
                    voice = VOICE_MALE
                else:
                    ok = False
                    break
                segments.append((seg, voice))
            if not ok:
                continue
            if norm("".join(t for t, _v in segments)) != want:
                continue
            return segments
        if resp.status_code in (400, 404, 503, 429):
            continue
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    raise RuntimeError("အသံခွဲလို့ မရဘူး။")


def synthesize_voiced_segments(segments, rate):
    """[(text, voice_id)] -> same 6-tuple as synthesize_tts.
    Each segment is chunked and synthesized with its own voice; the audio
    is concatenated and one SRT is built over the whole text."""
    full_text = " ".join(t.strip() for t, _v in segments).strip()
    if not full_text:
        raise RuntimeError("စာသား ရိုက်ထည့်ပါ။")
    rate_str = f"{int(rate):+d}%"
    pitch_str = "+0Hz"
    workdir = tempfile.mkdtemp(prefix="tts_app_")
    chunk_files = []
    all_bounds = []
    shift = 0.0
    idx = 0
    for seg_text, voice in segments:
        for ch in chunk_text(seg_text):
            audio, bounds = edge_synthesize(ch, voice, rate_str, pitch_str)
            if not audio:
                raise RuntimeError("အသံ ထုတ်လို့ မရဘူး။ ထပ်စမ်းကြည့်ပါ။")
            cf = os.path.join(workdir, f"part{idx}.mp3")
            with open(cf, "wb") as f:
                f.write(audio)
            chunk_files.append(cf)
            dur = probe_duration(cf)
            for (s, e, w) in bounds:
                all_bounds.append((s + shift, e + shift, w))
            shift += dur
            idx += 1
    list_path = os.path.join(workdir, "parts.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"file '{cf}'\n")
    out_mp3 = os.path.join(workdir, "narration.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                        "-c:a", "libmp3lame", "-q:a", "4", out_mp3],
                       capture_output=True, text=True, errors="ignore", timeout=600)
    if r.returncode != 0 or not os.path.exists(out_mp3):
        raise RuntimeError("အသံဖိုင် ပေါင်းလို့ မရဘူး: " + r.stderr[-200:])
    total = probe_duration(out_mp3)
    cues = build_tts_cues(full_text, all_bounds, total)
    srt_path = os.path.join(workdir, "narration.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for k, (start, end, s) in enumerate(cues):
            f.write(f"{k + 1}\n{format_time(start)} --> {format_time(end)}\n{s}\n\n")
    with open(srt_path, encoding="utf-8") as f:
        srt_text = f.read()
    return out_mp3, srt_path, srt_text, total, len(cues), workdir


def process_tts(text, voice_label, rate, pitch):
    try:
        voice = VOICES.get(voice_label, "my-MM-NilarNeural")
        out_mp3, srt_path, srt_text, total, n_cues, _workdir = synthesize_tts(
            text, voice, rate, pitch)
        status = f"✅ ပြီးပါပြီ။ အသံ {total:.1f} စက္ကန့် — စာတန်း {n_cues} ပိုင်း။"
        return status, out_mp3, srt_path, srt_text
    except Exception as e:
        return f"❌ Error: {e}", None, None, ""


# ---------------- Prompt -> Video (v17) ----------------
# Prompt တစ်ခု ရိုက်ထည့်ရုံနဲ့ Video တစ်ပုဒ် ထွက်တယ် (အခမဲ့ လမ်းကြောင်း):
# 1) Gemini TEXT (free tier) က prompt ကို 3-scene ဇာတ်လမ်းတို ချဲ့ပေးတယ်
#    (အင်္ဂလိပ် image prompt + မြန်မာ narration တစ်ပိုင်းစီ)
# 2) ပုံတွေကို Pollinations အခမဲ့ image service က ထုတ်တယ် (Key မလိုဘူး) —
#    Gemini image model တွေက billing-enabled key လိုတယ် (free tier quota = 0)
#    ဆိုတာ 2026-11-13 မှာ အတည်ပြုပြီးသား၊ ဒါကြောင့် Gemini ပုံထုတ်တာ မသုံးဘူး
# 3) edge-tts မြန်မာအသံ + ဖြည်းဖြည်း zoom-in လှုပ်ရှားမှု + မြန်မာစာတန်း burn-in

def generate_script(api_key, prompt):
    """User idea -> 3 scenes: [{"image_prompt": ..., "narration": ...}].
    Raises RuntimeError on failure."""
    import json
    instruction = (
        "You are a short-video scriptwriter. The user gives a video idea in any language. "
        "Write a 3-scene short video script (each scene lasts 10 seconds). "
        "For each scene give: 1) image_prompt: one detailed ENGLISH image-generation prompt "
        "(cinematic, vertical 9:16) describing a single clear picture for the scene, keeping "
        "the same main character and setting across all 3 scenes; "
        "2) narration: 1-2 short sentences in Myanmar (Burmese) script that a narrator will "
        "read aloud during the scene (about 8-12 words, natural spoken Myanmar). "
        "The 3 scenes must tell one complete tiny story with a beginning, middle and end. "
        "Return ONLY valid JSON: a list of exactly 3 objects with keys "
        "\"image_prompt\" and \"narration\". No other text."
    )
    payload = {
        "contents": [{"parts": [{"text": instruction + "\n\nIdea: " + prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    for name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
        except requests.exceptions.RequestException:
            continue
        if resp.status_code == 200:
            try:
                data = resp.json()
            except ValueError:
                continue
            cands = data.get("candidates", [])
            parts = cands[0].get("content", {}).get("parts", []) if cands else []
            texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
            if not texts:
                continue
            raw = "\n".join(texts).strip()
            scenes = None
            try:
                scenes = json.loads(raw)
            except ValueError:
                try:
                    scenes = json.loads(re.sub(r"```\w*", "", raw).strip())
                except ValueError:
                    continue
            if (isinstance(scenes, list) and len(scenes) == 3
                    and all(isinstance(s, dict) and s.get("image_prompt")
                            and s.get("narration") for s in scenes)):
                return [{"image_prompt": str(s["image_prompt"]).strip(),
                         "narration": str(s["narration"]).strip()} for s in scenes]
            continue
        if resp.status_code in (400, 404, 503, 429):
            continue
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
    raise RuntimeError("ဇာတ်လမ်း ရေးလို့ မရဘူး။ ခဏစောင့်ပြီး ထပ်နှိပ်ပါ။")


def fetch_scene_image(image_prompt, out_path, width=576, height=1024):
    """Free image generation (Pollinations, no API key needed)."""
    from urllib.parse import quote
    url = ("https://image.pollinations.ai/prompt/" + quote(image_prompt)
           + f"?width={width}&height={height}&nologo=true")
    last_err = "unknown"
    for _ in range(2):
        try:
            r = requests.get(url, timeout=150)
            ctype = r.headers.get("content-type", "")
            if r.status_code == 200 and ctype.startswith("image/") and len(r.content) > 10000:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return
            last_err = f"HTTP {r.status_code} ({ctype})"
        except requests.exceptions.RequestException as e:
            last_err = str(e)[:100]
    raise RuntimeError(f"ပုံ ထုတ်လို့ မရဘူး ({last_err})။ ခဏစောင့်ပြီး ထပ်နှိပ်ပါ။")


def build_prompt_video(workdir, scenes, voice, rate, pitch):
    """Scenes -> (finished mp4 path, SRT text).
    Per scene: Myanmar narration (edge-tts) + slow zoom-in on the image
    (10s minimum, longer if the narration needs it). Segments are joined
    and the narration lines are burned in as Myanmar subtitles."""
    import shutil
    font_path = find_myanmar_font()
    if font_path is None:
        raise RuntimeError("မြန်မာစာလုံး (font) မတွေ့ဘူး။")
    scene_files = []
    all_cues = []
    offset = 0.0
    for i, scene in enumerate(scenes):
        img_path = os.path.join(workdir, f"scene{i}.jpg")
        fetch_scene_image(scene["image_prompt"], img_path)
        out_mp3, _srt_path, srt_text, total, _n, tts_dir = synthesize_tts(
            scene["narration"], voice, rate, pitch)
        narr_path = os.path.join(workdir, f"narr{i}.mp3")
        shutil.copyfile(out_mp3, narr_path)
        shutil.rmtree(tts_dir, ignore_errors=True)
        for (s, e, t) in parse_srt_text(srt_text, total):
            all_cues.append((s + offset, e + offset, t))
        dur = max(10.0, total + 0.8)
        frames = int(math.ceil(dur * 25))
        dur = frames / 25.0
        seg_path = os.path.join(workdir, f"seg{i}.mp4")
        filt = ("[0:v]zoompan=z='min(zoom+0.0012,1.4)':x='iw/2-(iw/zoom/2)'"
                f":y='ih/2-(ih/zoom/2)':d={frames}:s=576x1024:fps=25[v];[1:a]apad[a]")
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", img_path, "-i", narr_path,
             "-filter_complex", filt,
             "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
             "-c:a", "aac", "-b:a", "128k", seg_path],
            capture_output=True, text=True, errors="ignore", timeout=900)
        if r.returncode != 0 or not os.path.exists(seg_path):
            raise RuntimeError("Video အပိုင်း ထုတ်လို့ မရဘူး: " + r.stderr[-200:])
        scene_files.append(seg_path)
        offset += dur
    list_path = os.path.join(workdir, "segments.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")
    joined = os.path.join(workdir, "joined.mp4")
    r = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
         "-c", "copy", joined],
        capture_output=True, text=True, errors="ignore", timeout=300)
    if r.returncode != 0 or not os.path.exists(joined):
        raise RuntimeError("Video အပိုင်းတွေ ပေါင်းလို့ မရဘူး: " + r.stderr[-200:])
    out_mp4 = os.path.join(workdir, "voiceover.mp4")
    burn_subtitles(joined, all_cues, out_mp4, font_path)
    srt_text = ""
    for k, (s, e, t) in enumerate(all_cues):
        srt_text += f"{k + 1}\n{format_time(s)} --> {format_time(e)}\n{t}\n\n"
    # Narration-only mp3 too (served by the /audio download route).
    nlist = os.path.join(workdir, "narrs.txt")
    with open(nlist, "w", encoding="utf-8") as f:
        for i in range(len(scenes)):
            f.write(f"file '{os.path.join(workdir, f'narr{i}.mp3')}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", nlist,
                    "-c:a", "libmp3lame", "-q:a", "4",
                    os.path.join(workdir, "narration.mp3")],
                   capture_output=True, text=True, errors="ignore", timeout=300)
    return out_mp4, srt_text


# ---------------- Gemini TTS (v22) ----------------
# edge-tts မြန်မာအသံ (Nilar/Thiha) က ဖတ်ပုံ ပြားတယ် — စိတ်ခံစားမှု/
# အသံနိမ့်အမြင့် ထိန်းလို့ မရဘူး။ Gemini TTS က style ညွှန်ကြားချက်နဲ့
# အသက်ပါပါ ဖတ်ပြနိုင်တယ် (spooky/natural)။ အားနည်းချက်: word-level
# timestamp မပေးဘူး → SRT က စာကြောင်းအလိုက် အချိန်ခွဲတဲ့ အရန်နည်း။
# 2.5 TTS မော်ဒယ်တွေက 2026-11-17 မှာ ပိတ်မယ် + key အသစ်တွေမှာ 404
# ဖြစ်နိုင်လို့ 3.x TTS မော်ဒယ်တွေပဲ သုံးတယ်။
GEMINI_TTS_MODELS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview",
                      "gemini-3.8-flash-lite-tts"]
GEMINI_TTS_STYLES = {
    "natural": ("Say with lively, expressive intonation and varied pitch, "
                "like a warm storyteller, in the Myanmar language:"),
    "spooky": ("Say in a slow, spooky, dramatic storytelling voice with "
               "varied pitch and suspenseful pauses, like telling a ghost "
               "story, in the Myanmar language:"),
}
# edge-tts အသံ -> Gemini အသံ အမည် (Nilar = မိန်းကလေး, Thiha = ယောက်ျားလေး)
GEMINI_VOICE_MAP = {"my-MM-NilarNeural": "Sulafat",
                    "my-MM-ThihaNeural": "Kore"}


def gemini_tts_chunk(api_key, chunk, voice_name, style_prompt):
    """One text chunk -> WAV bytes. Tries the TTS models in order."""
    import base64
    import io
    import wave
    body = {"contents": [{"parts": [{"text": f"{style_prompt} {chunk}"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig":
                                                 {"voiceName": voice_name}}}}}
    last_err = None
    for model in GEMINI_TTS_MODELS:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                json=body, headers={"x-goog-api-key": api_key}, timeout=300)
        except requests.exceptions.RequestException as e:
            last_err = e
            continue
        if resp.status_code in (400, 404, 503, 429):
            last_err = RuntimeError(f"{model}: HTTP {resp.status_code}")
            continue
        if resp.status_code != 200:
            raise RuntimeError(
                f"Gemini TTS error {resp.status_code}: {resp.text[:200]}")
        try:
            part = resp.json()["candidates"][0]["content"]["parts"][0]
            inline = part["inlineData"]
            raw = base64.b64decode(inline["data"])
            mime = inline.get("mimeType", "")
        except (KeyError, IndexError, ValueError) as e:
            last_err = e
            continue
        if "wav" in mime.lower():
            return raw
        # PCM L16: wrap in a WAV header (sample rate from the mime type).
        m = re.search(r"rate=(\d+)", mime)
        rate = int(m.group(1)) if m else 24000
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(raw)
        return buf.getvalue()
    raise RuntimeError("Gemini အသံ ထုတ်လို့ မရဘူး။" +
                       (f" ({last_err})" if last_err else ""))


def synthesize_gemini_tts(text, voice_name, style, api_key):
    """Text -> same 6-tuple as synthesize_tts, via Gemini TTS.
    Cues are per-sentence, split proportionally within each chunk's
    measured duration (Gemini returns no word timestamps)."""
    text = (text or "").strip()
    if not text:
        raise RuntimeError("စာသား ရိုက်ထည့်ပါ။")
    if not (api_key or "").strip():
        raise RuntimeError("Gemini API Key လိုတယ်။ App မှာ Key ထည့်ပါ။")
    style_prompt = GEMINI_TTS_STYLES.get(style, GEMINI_TTS_STYLES["natural"])
    workdir = tempfile.mkdtemp(prefix="tts_app_")
    chunk_files = []
    all_cues = []
    shift = 0.0
    idx = 0
    for ch in chunk_text(text):
        wav = gemini_tts_chunk(api_key, ch, voice_name, style_prompt)
        if not wav:
            raise RuntimeError("အသံ ထုတ်လို့ မရဘူး။ ထပ်စမ်းကြည့်ပါ။")
        cf = os.path.join(workdir, f"part{idx}.wav")
        with open(cf, "wb") as f:
            f.write(wav)
        chunk_files.append(cf)
        dur = probe_duration(cf)
        for (s, e, t) in build_tts_cues(ch, [], dur):
            all_cues.append((s + shift, e + shift, t))
        shift += dur
        idx += 1
    list_path = os.path.join(workdir, "parts.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"file '{cf}'\n")
    out_mp3 = os.path.join(workdir, "narration.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
                        "-c:a", "libmp3lame", "-q:a", "4", out_mp3],
                       capture_output=True, text=True, errors="ignore", timeout=600)
    if r.returncode != 0 or not os.path.exists(out_mp3):
        raise RuntimeError("အသံဖိုင် ပေါင်းလို့ မရဘူး: " + r.stderr[-200:])
    total = probe_duration(out_mp3)
    srt_path = os.path.join(workdir, "narration.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        for k, (start, end, s) in enumerate(all_cues):
            f.write(f"{k + 1}\n{format_time(start)} --> {format_time(end)}\n{s}\n\n")
    with open(srt_path, encoding="utf-8") as f:
        srt_text = f.read()
    return out_mp3, srt_path, srt_text, total, len(all_cues), workdir


# ---------------- Image + narration -> Video (v21) ----------------
# သုံးစွဲသူက ပုံ တစ်ပုံ ထည့်ပြီး စာသား ရိုက်ထည့်ရုံနဲ့ Video တစ်ပုဒ် ထွက်တယ်:
# ပုံ (ဖြည်းဖြည်း zoom-in) + မြန်မာ AI အသံ + မြန်မာစာတန်း burn-in။
# အသံကို manual (အသံတစ်မျိုး) သို့မဟုတ် auto (ဇာတ်ကောင် အလိုက် ခွဲ) နဲ့ ထုတ်နိုင်တယ်။

def build_narrated_image_video(workdir, img_path, text, voice, rate, pitch,
                               mode, api_key, engine="edge", style="natural"):
    """(image, text) -> (finished mp4 path, SRT text). The narration mp3 is
    also left in the workdir as narration.mp3 for the /audio route.
    engine "gemini" uses expressive Gemini TTS (manual voice only; the
    auto split is an edge-tts feature and is ignored for Gemini)."""
    import shutil
    font_path = find_myanmar_font()
    if font_path is None:
        raise RuntimeError("မြန်မာစာလုံး (font) မတွေ့ဘူး။")
    if engine == "gemini":
        key = (api_key or "").strip() or SECRET_KEY
        gemini_voice = GEMINI_VOICE_MAP.get(voice, "Sulafat")
        out_mp3, _srt_path, srt_text, total, _n, tts_dir = \
            synthesize_gemini_tts(text, gemini_voice, style, key)
    elif mode == "auto":
        key = (api_key or "").strip() or SECRET_KEY
        if not key:
            raise RuntimeError("Gemini API Key လိုတယ်။ App မှာ Key ထည့်ပါ။")
        try:
            segments = split_voices(key, text)
        except Exception:
            segments = [(text, voice)]
        out_mp3, _srt_path, srt_text, total, _n, tts_dir = \
            synthesize_voiced_segments(segments, rate)
    else:
        out_mp3, _srt_path, srt_text, total, _n, tts_dir = synthesize_tts(
            text, voice, rate, pitch)
    narr_path = os.path.join(workdir, "narration.mp3")
    shutil.copyfile(out_mp3, narr_path)
    shutil.rmtree(tts_dir, ignore_errors=True)
    cues = parse_srt_text(srt_text, total)
    # Normalize any user image to vertical 576x1024 (cover crop) so the
    # zoom math below always works, whatever shape the upload is.
    norm_path = os.path.join(workdir, "image_norm.jpg")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", img_path, "-vf",
         "scale=576:1024:force_original_aspect_ratio=increase,crop=576:1024",
         "-frames:v", "1", norm_path],
        capture_output=True, text=True, errors="ignore", timeout=300)
    if r.returncode != 0 or not os.path.exists(norm_path):
        raise RuntimeError("ပုံ ဖတ်လို့ မရဘူး။ JPG/PNG ပုံ ထည့်ပါ။")
    dur = total + 0.8
    frames = int(math.ceil(dur * 25))
    dur = frames / 25.0
    seg_path = os.path.join(workdir, "seg.mp4")
    filt = ("[0:v]zoompan=z='min(zoom+0.0012,1.4)':x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2)':d={frames}:s=576x1024:fps=25[v];[1:a]apad[a]")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", norm_path, "-i", narr_path,
         "-filter_complex", filt,
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k", seg_path],
        capture_output=True, text=True, errors="ignore", timeout=900)
    if r.returncode != 0 or not os.path.exists(seg_path):
        raise RuntimeError("Video ထုတ်လို့ မရဘူး: " + r.stderr[-200:])
    out_mp4 = os.path.join(workdir, "voiceover.mp4")
    burn_subtitles(seg_path, cues, out_mp4, font_path)
    return out_mp4, srt_text


# ---------------- UI ----------------

if SECRET_KEY:
    key_note = "✅ Secrets Key ရှိတယ် — ထပ်ထည့်စရာ မလိုဘူး။"
else:
    key_note = "⚠️ Secrets မှာ GEMINI_API_KEY သိမ်းထားရင် ထပ်ထည့်စရာ မလိုဘူး။"

with gr.Blocks(title="Zhang Studio") as demo:
    if BANNER_PATH:
        gr.Image(value=BANNER_PATH, show_label=False)
    gr.Markdown("# Zhang Studio")
    gr.Markdown("မြန်မာစာတန်းထိုး + အသံဖတ်ပြ · v23 (video preview on top + Gemini expressive voice + image narration)")
    with gr.Tab("🎬 Video စာတန်းထိုး"):
        gr.Markdown("video တင် → Gemini က အသံနားထောင်ပြီး မြန်မာစာတန်း ထိုးပေးမယ်။")
        gr.Markdown(key_note)
        key_box = gr.Textbox(label="Gemini API Key", type="password",
                             placeholder="AQ. နဲ့ စတဲ့ Key (Secrets မှာ သိမ်းထားရင် ချန်ထားလို့ ရတယ်)")
        video_in = gr.Video(label="ဗီဒီယို တင်ပါ")
        btn1 = gr.Button("စာတန်းထိုးမယ်")
        status1 = gr.Textbox(label="အခြေအနေ")
        # v23: ထွက်လာတဲ့ video ကို SRT box အပေါ်မှာ ပြထားတယ် —
        # scroll ဆွဲစရာ မလိုပဲ ရလဒ်ကို တန်း ကြည့်လို့ ရအောင်။
        video_out = gr.Video(label="စာတန်းထိုးပါတဲ့ video")
        srt_out1 = gr.Textbox(label="SRT စာသား", lines=10)
        file_out1 = gr.File(label="SRT ဖိုင် download")
        btn1.click(fn=process_subtitle, inputs=[key_box, video_in],
                   outputs=[status1, srt_out1, video_out, file_out1])
    with gr.Tab("🎙️ အသံဖတ်ပြ + စာတန်း"):
        gr.Markdown("စာရိုက်ထည့် → AI က အသံဖတ်ပြမယ် + အသံနဲ့ ကိုက်တဲ့ စာတန်း (SRT) ပါ ထုတ်ပေးမယ်။ (Key မလိုဘူး)")
        text_in = gr.Textbox(label="ဖတ်ပြစေချင်တဲ့ စာသား", lines=8,
                             placeholder="မြန်မာစာသား ဒီမှာ ရိုက်ထည့်ပါ...")
        voice_in = gr.Dropdown(choices=list(VOICES.keys()), value=list(VOICES.keys())[0],
                               label="အသံ ရွေးပါ")
        rate_in = gr.Slider(minimum=-50, maximum=50, step=5, value=0,
                            label="အမြန် / အနှေး (- = နှေး, + = မြန်)")
        pitch_in = gr.Slider(minimum=-50, maximum=50, step=5, value=0,
                             label="အသံ အနိမ့် / အမြင့် (- = နိမ့်, + = မြင့်)")
        btn2 = gr.Button("အသံထုတ်မယ်")
        status2 = gr.Textbox(label="အခြေအနေ")
        audio_out = gr.Audio(label="အသံဖိုင် (နားထောင်ရန် / download)")
        file_out2 = gr.File(label="SRT ဖိုင် download")
        srt_out2 = gr.Textbox(label="SRT စာသား", lines=10)
        btn2.click(fn=process_tts, inputs=[text_in, voice_in, rate_in, pitch_in],
                   outputs=[status2, audio_out, file_out2, srt_out2])

# Spaces/Render မှာ share မလိုဘူး (အမြဲ link ရှိပြီးသား); Colab မှာ share လိုတယ်
# Render: RENDER=true + PORT env ပါတယ် — Gradio UI + Android API (/api/transcribe)
# ကို port တစ်ခုတည်းမှာ FastAPI mount လုပ်ပြီး run ရမယ်
# v14: transcription က async job — client က upload တင်တာနဲ့ job_id ရမယ်,
# server က နောက်ကွယ်မှာ လုပ်မယ်, client က /api/status/{job_id} ကို ခဏခဏ
# မေးမယ် (slow connection မှာ timeout မဖြစ်အောင်)
# v15: TTS လည်း async job ပဲ — POST /api/tts → job_id → poll → done မှာ
# audio_url ပါမယ် (GET /api/download/{job_id}/audio ကနေ mp3 ယူရမယ်)
# v16: Voiceover လည်း async job — POST /api/voiceover → job_id → poll →
# done မှာ video_url ပါမယ် (GET /api/download/{job_id}/video ကနေ mp4 ယူရမယ်)
# v17: Prompt-to-video async job — POST /api/prompt-video → job_id → poll →
# done မှာ video_url + srt ပါမယ် (ဇာတ်လမ်း Gemini TEXT, ပုံ Pollinations,
# အသံ edge-tts, motion + စာတန်း ffmpeg)
# v18: အချိန်တိကျအောင် chunked transcription (VAD အပိုင်း / 6s ပြတင်းပေါက်)
# + cue အစ/အဆုံး အသံနဲ့ ကပ်ခြင်း — transcribe_cues() က Tab 1 ရော API ရော သုံးတယ်
if os.environ.get("RENDER"):
    from fastapi import FastAPI, File, Form, UploadFile
    from fastapi.responses import FileResponse, JSONResponse
    import shutil
    import threading
    import uuid
    import uvicorn

    api_app = FastAPI()
    _jobs = {}
    _job_files = {}  # job_id -> workdir holding the finished TTS mp3
    _jobs_lock = threading.Lock()

    def _prune_jobs():
        # Keep the job table small: drop oldest finished jobs (and delete
        # their TTS workdirs so mp3 files don't pile up on disk).
        # Called OUTSIDE _jobs_lock (threading.Lock is not reentrant).
        with _jobs_lock:
            if len(_jobs) <= 50:
                return
            finished = [k for k, v in _jobs.items() if v.get("status") != "pending"]
            for k in finished[: len(_jobs) - 50]:
                del _jobs[k]
                workdir = _job_files.pop(k, None)
                if workdir:
                    shutil.rmtree(workdir, ignore_errors=True)

    def _run_job(job_id, tmp_path, api_key):
        try:
            model_name, srt_text = transcribe_video_file(tmp_path, api_key)
            result = {"status": "done", "srt": srt_text, "model": model_name}
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        with _jobs_lock:
            _jobs[job_id] = result

    def _run_tts_job(job_id, text, voice, rate, pitch, mode="manual", api_key=None):
        try:
            if mode == "auto":
                key = (api_key or "").strip() or SECRET_KEY
                if not key:
                    raise RuntimeError("Gemini API Key လိုတယ်။ App မှာ Key ထည့်ပါ။")
                try:
                    segments = split_voices(key, text)
                except Exception:
                    segments = [(text, voice)]
                out_mp3, _srt_path, srt_text, _total, _n, workdir = \
                    synthesize_voiced_segments(segments, rate)
            else:
                out_mp3, _srt_path, srt_text, _total, _n, workdir = synthesize_tts(
                    text, voice, rate, pitch)
            result = {"status": "done", "srt": srt_text,
                      "audio_url": f"/api/download/{job_id}/audio"}
            with _jobs_lock:
                _job_files[job_id] = workdir
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        with _jobs_lock:
            _jobs[job_id] = result

    def _run_voiceover_job(job_id, tmp_path, api_key, voice, rate, pitch, mode="manual"):
        try:
            _model_name, srt_text = transcribe_video_file(tmp_path, api_key)
            # Narration text = the transcribed/translated lines in order.
            narration = " ".join(
                line.strip()
                for line in srt_text.splitlines()
                if line.strip() and "-->" not in line and not line.strip().isdigit()
            ).strip()
            if not narration:
                raise RuntimeError("ဒီ Video မှာ အသံမတွေ့ဘူး။")
            if mode == "auto":
                key = (api_key or "").strip() or SECRET_KEY
                if not key:
                    raise RuntimeError("Gemini API Key လိုတယ်။ App မှာ Key ထည့်ပါ။")
                try:
                    segments = split_voices(key, narration)
                except Exception:
                    segments = [(narration, voice)]
                out_mp3, _srt_path, tts_srt, _total, _n, workdir = \
                    synthesize_voiced_segments(segments, rate)
            else:
                out_mp3, _srt_path, tts_srt, _total, _n, workdir = synthesize_tts(
                    narration, voice, rate, pitch)
            out_mp4 = os.path.join(workdir, "voiceover.mp4")
            # Video stream copied (no re-encode = fast); narration becomes
            # the audio track. Original audio is replaced so the old
            # language doesn't clash with the Myanmar narration.
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, "-i", out_mp3,
                 "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", out_mp4],
                capture_output=True, text=True, errors="ignore", timeout=600)
            if r.returncode != 0 or not os.path.exists(out_mp4):
                raise RuntimeError("Video နဲ့ အသံ တွဲလို့ မရဘူး: " + r.stderr[-200:])
            result = {"status": "done", "srt": tts_srt,
                      "audio_url": f"/api/download/{job_id}/audio",
                      "video_url": f"/api/download/{job_id}/video"}
            with _jobs_lock:
                _job_files[job_id] = workdir
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        with _jobs_lock:
            _jobs[job_id] = result

    def _run_prompt_video_job(job_id, prompt, api_key, voice, rate, pitch):
        import shutil
        workdir = tempfile.mkdtemp(prefix="prompt_video_")
        try:
            key = (api_key or "").strip() or SECRET_KEY
            if not key:
                raise RuntimeError("Gemini API Key လိုတယ်။ App မှာ Key ထည့်ပါ။")
            scenes = generate_script(key, prompt)
            _out_mp4, srt_text = build_prompt_video(workdir, scenes, voice, rate, pitch)
            result = {"status": "done", "srt": srt_text,
                      "audio_url": f"/api/download/{job_id}/audio",
                      "video_url": f"/api/download/{job_id}/video"}
            with _jobs_lock:
                _job_files[job_id] = workdir
        except Exception as e:
            result = {"status": "error", "error": str(e)}
            shutil.rmtree(workdir, ignore_errors=True)
        with _jobs_lock:
            _jobs[job_id] = result

    def _run_narrate_image_job(job_id, img_tmp_path, text, api_key,
                               voice, rate, pitch, mode,
                               engine="edge", style="natural"):
        import shutil
        workdir = tempfile.mkdtemp(prefix="narrate_image_")
        try:
            _out_mp4, srt_text = build_narrated_image_video(
                workdir, img_tmp_path, text, voice, rate, pitch, mode,
                api_key, engine, style)
            result = {"status": "done", "srt": srt_text,
                      "audio_url": f"/api/download/{job_id}/audio",
                      "video_url": f"/api/download/{job_id}/video"}
            with _jobs_lock:
                _job_files[job_id] = workdir
        except Exception as e:
            result = {"status": "error", "error": str(e)}
            shutil.rmtree(workdir, ignore_errors=True)
        finally:
            try:
                os.unlink(img_tmp_path)
            except Exception:
                pass
        with _jobs_lock:
            _jobs[job_id] = result

    def _run_gemini_tts_job(job_id, text, api_key, voice, style):
        import shutil
        try:
            key = (api_key or "").strip() or SECRET_KEY
            _out_mp3, _srt_path, srt_text, total, n_cues, workdir = \
                synthesize_gemini_tts(text, voice, style, key)
            result = {"status": "done", "srt": srt_text,
                      "audio_url": f"/api/download/{job_id}/audio"}
            with _jobs_lock:
                _job_files[job_id] = workdir
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        with _jobs_lock:
            _jobs[job_id] = result

    @api_app.post("/api/transcribe")
    def api_transcribe(video: UploadFile = File(...), api_key: str = Form(None)):
        tmp = None
        try:
            suffix = os.path.splitext(video.filename or "video.mp4")[1] or ".mp4"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            while True:
                chunk = video.file.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp.close()
            job_id = uuid.uuid4().hex
            with _jobs_lock:
                _jobs[job_id] = {"status": "pending"}
            _prune_jobs()
            t = threading.Thread(target=_run_job, args=(job_id, tmp.name, api_key), daemon=True)
            t.start()
            return JSONResponse(status_code=202, content={"job_id": job_id})
        except Exception as e:
            if tmp is not None:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            return JSONResponse(status_code=500, content={"error": str(e)})

    @api_app.post("/api/tts")
    def api_tts(text: str = Form(...), voice: str = Form("my-MM-NilarNeural"),
                rate: int = Form(0), pitch: int = Form(0),
                mode: str = Form("manual"), api_key: str = Form(None)):
        # Manual mode needs no Gemini key (edge-tts is free); auto mode
        # splits voices by character with Gemini, so it needs a key.
        text = (text or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"error": "empty text"})
        # v19: စာရှည်တွေ (ပုံပြင်အပြည့်အစုံ) လည်း ရအောင် 15000 အထိ ခွင့်ပြုသည်။
        if len(text) > 15000:
            return JSONResponse(status_code=400,
                                content={"error": "စာသား အရမ်းရှည်ပါတယ်။ အက္ခရာ 15000 ထက် မပိုအောင် လျှော့ပါ။"})
        if voice not in ("my-MM-NilarNeural", "my-MM-ThihaNeural"):
            voice = "my-MM-NilarNeural"
        rate = max(-50, min(50, rate))
        pitch = max(-50, min(50, pitch))
        if mode not in ("manual", "auto"):
            mode = "manual"
        job_id = uuid.uuid4().hex
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending"}
        _prune_jobs()
        t = threading.Thread(target=_run_tts_job,
                             args=(job_id, text, voice, rate, pitch, mode, api_key),
                             daemon=True)
        t.start()
        return JSONResponse(status_code=202, content={"job_id": job_id})

    @api_app.get("/api/download/{job_id}/audio")
    def api_download_audio(job_id: str):
        with _jobs_lock:
            workdir = _job_files.get(job_id)
        if not workdir:
            return JSONResponse(status_code=404, content={"error": "unknown job"})
        mp3_path = os.path.join(workdir, "narration.mp3")
        if not os.path.exists(mp3_path):
            return JSONResponse(status_code=404, content={"error": "audio not ready"})
        return FileResponse(mp3_path, media_type="audio/mpeg", filename="narration.mp3")

    @api_app.post("/api/gemini-tts")
    def api_gemini_tts(text: str = Form(...), api_key: str = Form(None),
                       voice: str = Form("Sulafat"),
                       style: str = Form("natural")):
        text = (text or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"error": "empty text"})
        if len(text) > 15000:
            return JSONResponse(status_code=400,
                                content={"error": "စာသား အရမ်းရှည်ပါတယ်။ အက္ခရာ 15000 ထက် မပိုအောင် လျှော့ပါ။"})
        if voice not in ("Sulafat", "Kore", "Aoede", "Charon",
                         "Zephyr", "Fenrir", "Leda", "Puck"):
            voice = "Sulafat"
        if style not in ("natural", "spooky"):
            style = "natural"
        job_id = uuid.uuid4().hex
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending"}
        _prune_jobs()
        t = threading.Thread(target=_run_gemini_tts_job,
                             args=(job_id, text, api_key, voice, style),
                             daemon=True)
        t.start()
        return JSONResponse(status_code=202, content={"job_id": job_id})

    @api_app.post("/api/voiceover")
    def api_voiceover(video: UploadFile = File(...), api_key: str = Form(None),
                      voice: str = Form("my-MM-NilarNeural"),
                      rate: int = Form(0), pitch: int = Form(0),
                      mode: str = Form("manual")):
        tmp = None
        try:
            suffix = os.path.splitext(video.filename or "video.mp4")[1] or ".mp4"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            while True:
                chunk = video.file.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
            tmp.close()
            if voice not in ("my-MM-NilarNeural", "my-MM-ThihaNeural"):
                voice = "my-MM-NilarNeural"
            rate = max(-50, min(50, rate))
            pitch = max(-50, min(50, pitch))
            if mode not in ("manual", "auto"):
                mode = "manual"
            job_id = uuid.uuid4().hex
            with _jobs_lock:
                _jobs[job_id] = {"status": "pending"}
            _prune_jobs()
            t = threading.Thread(target=_run_voiceover_job,
                                 args=(job_id, tmp.name, api_key, voice, rate, pitch, mode),
                                 daemon=True)
            t.start()
            return JSONResponse(status_code=202, content={"job_id": job_id})
        except Exception as e:
            if tmp is not None:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            return JSONResponse(status_code=500, content={"error": str(e)})

    @api_app.post("/api/prompt-video")
    def api_prompt_video(prompt: str = Form(...), api_key: str = Form(None),
                         voice: str = Form("my-MM-NilarNeural"),
                         rate: int = Form(0), pitch: int = Form(0)):
        prompt = (prompt or "").strip()
        if not prompt:
            return JSONResponse(status_code=400, content={"error": "empty prompt"})
        if len(prompt) > 1000:
            return JSONResponse(status_code=400,
                                content={"error": "prompt too long — keep it under 1000 characters"})
        if voice not in ("my-MM-NilarNeural", "my-MM-ThihaNeural"):
            voice = "my-MM-NilarNeural"
        rate = max(-50, min(50, rate))
        pitch = max(-50, min(50, pitch))
        job_id = uuid.uuid4().hex
        with _jobs_lock:
            _jobs[job_id] = {"status": "pending"}
        _prune_jobs()
        t = threading.Thread(target=_run_prompt_video_job,
                             args=(job_id, prompt, api_key, voice, rate, pitch),
                             daemon=True)
        t.start()
        return JSONResponse(status_code=202, content={"job_id": job_id})

    @api_app.post("/api/narrate-image")
    def api_narrate_image(image: UploadFile = File(...),
                          text: str = Form(...), api_key: str = Form(None),
                          voice: str = Form("my-MM-NilarNeural"),
                          rate: int = Form(0), pitch: int = Form(0),
                          mode: str = Form("manual"),
                          engine: str = Form("edge"),
                          style: str = Form("natural")):
        text = (text or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"error": "empty text"})
        if len(text) > 15000:
            return JSONResponse(status_code=400,
                                content={"error": "စာသား အရမ်းရှည်ပါတယ်။ အက္ခရာ 15000 ထက် မပိုအောင် လျှော့ပါ။"})
        if voice not in ("my-MM-NilarNeural", "my-MM-ThihaNeural"):
            voice = "my-MM-NilarNeural"
        rate = max(-50, min(50, rate))
        pitch = max(-50, min(50, pitch))
        if mode not in ("manual", "auto"):
            mode = "manual"
        if engine not in ("edge", "gemini"):
            engine = "edge"
        if style not in ("natural", "spooky"):
            style = "natural"
        tmp = None
        try:
            data = image.file.read()
            if not data or len(data) > 15 * 1024 * 1024:
                return JSONResponse(status_code=400,
                                    content={"error": "ပုံ အရမ်းကြီးပါတယ်။ 15MB အောက် ထားပါ။"})
            suffix = os.path.splitext(image.filename or "image.jpg")[1] or ".jpg"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(data)
            tmp.close()
            job_id = uuid.uuid4().hex
            with _jobs_lock:
                _jobs[job_id] = {"status": "pending"}
            _prune_jobs()
            t = threading.Thread(target=_run_narrate_image_job,
                                 args=(job_id, tmp.name, text, api_key,
                                       voice, rate, pitch, mode,
                                       engine, style),
                                 daemon=True)
            t.start()
            return JSONResponse(status_code=202, content={"job_id": job_id})
        except Exception as e:
            if tmp is not None:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            return JSONResponse(status_code=500, content={"error": str(e)})

    @api_app.get("/api/download/{job_id}/video")
    def api_download_video(job_id: str):
        with _jobs_lock:
            workdir = _job_files.get(job_id)
        if not workdir:
            return JSONResponse(status_code=404, content={"error": "unknown job"})
        mp4_path = os.path.join(workdir, "voiceover.mp4")
        if not os.path.exists(mp4_path):
            return JSONResponse(status_code=404, content={"error": "video not ready"})
        return FileResponse(mp4_path, media_type="video/mp4", filename="voiceover.mp4")

    @api_app.get("/api/status/{job_id}")
    def api_status(job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if job is None:
            return JSONResponse(status_code=404, content={"error": "unknown job"})
        return dict(job)

    app = gr.mount_gradio_app(api_app, demo, path="/")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
else:
    _launch_kwargs = {"favicon_path": FAVICON_PATH}
    _launch_kwargs["share"] = not bool(os.environ.get("SPACE_ID"))
    demo.launch(**_launch_kwargs)
