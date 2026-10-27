#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全片旁白配音（edge-tts，音色与仓库既有 62 集一致）+ 时长测量"""
import asyncio, os, sys, json, subprocess, importlib.util, time
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vf_safe import under

BUILD = '/workspace/build'
ADIR = f'{BUILD}/audio'
os.makedirs(ADIR, exist_ok=True)

spec = importlib.util.spec_from_file_location("ep18", f'{BUILD}/scripts/course-t18.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
EP = m.EPISODE
SLIDES = EP['slides']

VOICE = os.environ.get('TTS_VOICE', 'zh-CN-YunxiNeural')
RATE = os.environ.get('TTS_RATE', '+4%')
PITCH = os.environ.get('TTS_PITCH', '+0Hz')


def dur_of(p):
    out = subprocess.run(['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                          '-of', 'csv=p=0', p], capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


async def synth(idx, text, out, sem):
    import edge_tts
    async with sem:
        for attempt in range(8):
            try:
                c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, volume='+0%')
                await asyncio.wait_for(c.save(out), timeout=45)
                if os.path.getsize(out) > 1200:
                    return True, attempt + 1
            except Exception as e:
                last = f'{type(e).__name__}'
                await asyncio.sleep(1.2 + attempt * 1.5)
        return False, 0


async def main():
    import edge_tts
    sem = asyncio.Semaphore(3)
    tasks = []
    todo = []
    for i, s in enumerate(SLIDES):
        raw = f'{ADIR}/s{i:02d}.mp3'
        if os.path.exists(raw) and os.path.getsize(raw) > 1200:
            continue
        todo.append((i, s.get('narration', ''), raw))
    print(f'todo: {len(todo)} / {len(SLIDES)}', flush=True)
    for i, text, out in todo:
        tasks.append(synth(i, text, out, sem))
    if tasks:
        res = await asyncio.gather(*tasks)
        bad = [i for (i, _, _), (ok, _) in zip(todo, res) if not ok]
        print('failed segments:', bad, flush=True)
    rows = []
    total = 0.0
    chars = 0
    for i, s in enumerate(SLIDES):
        raw = f'{ADIR}/s{i:02d}.mp3'
        d = dur_of(raw)
        total += d
        chars += len(s.get('narration', ''))
        rows.append({'i': i, 'type': s['type'], 'dur': round(d, 2),
                     'chars': len(s.get('narration', '')),
                     'title': s.get('title', s.get('kicker', ''))[:28]})
    Path(under(ADIR, 'timing.json')).write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in rows:
        print(f"  {r['i']:02d} {r['type']:9s} {r['dur']:6.2f}s  {r['chars']:4d}字  {r['title']}")
    print(f'\nTOTAL 旁白 {total:.1f}s = {total/60:.2f} min |  字符 {chars} | 语速 {chars/total:.2f} 字/秒')


asyncio.run(main())
