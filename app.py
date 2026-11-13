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

CANDIDATE_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite",
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
        "The audio is in Burmese (Myanmar language). Transcribe EXACTLY what is said, word for word, "
        "in Myanmar (Burmese) script. Do not translate, do not summarize, do not add explanations. "
        "Return ONLY a valid SRT subtitle file: numbered cues, each with start --> end timestamps "
        "in HH:MM:SS,mmm format. Use MANY SHORT cues: each cue at most 5 seconds, one short phrase "
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
        resp = requests.post(url, json=payload, headers=headers, timeout=300)
        if resp.status_code == 200:
            data = resp.json()
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
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)
    lines = wrap_text(draw, text, font, int(w * 0.9))
    line_h = font_size + int(font_size * 0.35)
    y = h - int(h * 0.08) - line_h * len(lines)
    stroke = max(2, font_size // 16)
    for ln in lines:
        tw = draw.textlength(ln, font=font)
        x = (w - tw) / 2
        draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        y += line_h
    img.save(out_path)


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
        render_cue_png(text, sw, sh, font_path, font_size, p)
        pngs.append((p, start, end))
    cmd = ["ffmpeg", "-y", "-i", video_path]
    for p, _, _ in pngs:
        cmd += ["-loop", "1", "-t", str(duration), "-i", p]
    filt = f"[0:v]scale={sw}:{sh}[base];"
    prev = "base"
    for k, (_, start, end) in enumerate(pngs):
        out = f"v{k}"
        filt += f"[{prev}][{k + 1}:v]overlay=0:0:enable='between(t,{start:.3f},{end:.3f})'[{out}];"
        prev = out
    cmd += ["-filter_complex", filt.rstrip(";"),
            "-map", f"[{prev}]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "copy", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="ignore", timeout=1800)
    if r.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError("video ထဲ စာတန်း ထည့်လို့ မရဘူး: " + r.stderr[-300:])


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
        model_name, raw_text = transcribe_with_gemini(key, audio_path, duration)
        cues = parse_srt_text(raw_text, duration)
        cues = split_long_cues(cues)
        cues = split_long_cues(cues)  # ဒုတိယအကြိမ် — ကျန်နေတဲ့ ရှည်တဲ့ cue တွေ ထပ်ခွဲ
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


def process_tts(text, voice_label, rate, pitch):
    try:
        text = (text or "").strip()
        if not text:
            return "⚠️ စာသား ရိုက်ထည့်ပါ။", None, None, ""
        voice = VOICES.get(voice_label, "my-MM-NilarNeural")
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
        status = f"✅ ပြီးပါပြီ။ အသံ {total:.1f} စက္ကန့် — စာတန်း {len(cues)} ပိုင်း။"
        return status, out_mp3, srt_path, srt_text
    except Exception as e:
        return f"❌ Error: {e}", None, None, ""


# ---------------- UI ----------------

if SECRET_KEY:
    key_note = "✅ Secrets Key ရှိတယ် — ထပ်ထည့်စရာ မလိုဘူး။"
else:
    key_note = "⚠️ Secrets မှာ GEMINI_API_KEY သိမ်းထားရင် ထပ်ထည့်စရာ မလိုဘူး။"

with gr.Blocks(title="Zhang Studio") as demo:
    if BANNER_PATH:
        gr.Image(value=BANNER_PATH, show_label=False)
    gr.Markdown("# Zhang Studio")
    gr.Markdown("မြန်မာစာတန်းထိုး + အသံဖတ်ပြ · v9 (မြန်နှုန်း မြှင့်)")
    with gr.Tab("🎬 Video စာတန်းထိုး"):
        gr.Markdown("video တင် → Gemini က အသံနားထောင်ပြီး မြန်မာစာတန်း ထိုးပေးမယ်။")
        gr.Markdown(key_note)
        key_box = gr.Textbox(label="Gemini API Key", type="password",
                             placeholder="AQ. နဲ့ စတဲ့ Key (Secrets မှာ သိမ်းထားရင် ချန်ထားလို့ ရတယ်)")
        video_in = gr.Video(label="ဗီဒီယို တင်ပါ")
        btn1 = gr.Button("စာတန်းထိုးမယ်")
        status1 = gr.Textbox(label="အခြေအနေ")
        srt_out1 = gr.Textbox(label="SRT စာသား", lines=10)
        video_out = gr.Video(label="စာတန်းထိုးပါတဲ့ video")
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
# Render: RENDER=true + PORT env ပါတယ် — 0.0.0.0:$PORT မှာ run ရမယ်
_launch_kwargs = {"favicon_path": FAVICON_PATH}
if os.environ.get("RENDER"):
    _launch_kwargs.update({"server_name": "0.0.0.0",
                           "server_port": int(os.environ.get("PORT", "7860")),
                           "share": False})
else:
    _launch_kwargs["share"] = not bool(os.environ.get("SPACE_ID"))
demo.launch(**_launch_kwargs)
