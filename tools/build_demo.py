"""Build an honestly labelled, local-only screenshot walkthrough.

Requires Pillow, ffmpeg/ffprobe, and (by default) Windows System.Speech.
No browser access, network request, generated application screens, or upload.
The inputs are actual UI captures and successful, independently checked receipts.
Pass tool paths as arguments; machine-specific paths are never written to output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
W, H, FPS = 1920, 1080, 24
PAPER, INK, MUTED = '#f2f0e6', '#29352b', '#647065'
ACCENT, LINE, CARD = '#dceba3', '#cbd1be', '#fafaf4'
CAPTURE_NAMES = ('overview', 'running', 'result', 'citation', 'details')


@dataclass
class Chapter:
    key: str
    title: str
    caption: str
    capture: str
    seconds: float
    narration: str
    focus: tuple[float, float, float, float] | None = None


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        # Do not copy private absolute paths from subprocess output to artifacts.
        raise RuntimeError(f'{Path(args[0]).name} failed ({result.returncode}). '
                           'Inspect the local command output before retrying.')
    return result.stdout


def checked_receipt(path: Path, *, require_clean: bool = False) -> dict:
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    assert data['status'] == 'succeeded', f'{path.name}: run did not succeed'
    assert data['typed_output_valid'] is True, f'{path.name}: typed check failed'
    assert data['semantic_validation']['valid'] is True, f'{path.name}: evidence check failed'
    events = data['tool_events']
    assert events, f'{path.name}: actual tool events required'
    succeeded = sum(e['status'] == 'succeeded' for e in events)
    rejected = len(events) - succeeded
    if require_clean:
        assert rejected == 0, f'{path.name}: frozen clean-run facts changed'
    states = {claim['id']: claim['status'] for claim in data['report']['claims']}
    assert states == {'C01': 'supported', 'C02': 'contradicted', 'C03': 'unknown'}, (
        f'{path.name}: expected fixture classifications changed')
    return {'receipt': relative(path), 'sha256': sha256(path),
            'elapsed_ms': data['elapsed_ms'], 'total_tool_calls': len(events),
            'successful_tool_calls': succeeded, 'rejected_tool_calls': rejected,
            'tool_collection_turns': len(data['runtime']['tool_collection_turns']),
            'typed_output_valid': True, 'semantic_validation_valid': True,
            'sdk': data['sdk']['version'], 'model': data['model']['name']}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # System font lookup only; these filesystem locations are not exported.
    candidates = [Path('C:/Windows/Fonts') / ('segoeuib.ttf' if bold else 'segoeui.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu') /
                  ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    raise RuntimeError('Provide a readable system font before rendering.')


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int],
                 max_width: int, face: ImageFont.FreeTypeFont, fill: str,
                 spacing: int = 10) -> int:
    x, y = xy
    words, current, lines = text.split(), '', []
    for word in words:
        candidate = f'{current} {word}'.strip()
        if current and draw.textlength(candidate, font=face) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    for line in lines:
        draw.text((x, y), line, fill=fill, font=face)
        y += face.size + spacing
    return y


def render_frame(chapter: Chapter, index: int, count: int,
                 capture_dir: Path, output: Path) -> None:
    image = Image.new('RGB', (W, H), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((48, 33, 154, 76), radius=18, fill=ACCENT)
    draw.text((67, 37), 'H / L', font=font(26, True), fill=INK)
    draw.text((175, 34), 'HANDOFF LEDGER', font=font(29, True), fill=INK)
    draw.text((W - 218, 40), f'{index + 1:02d} / {count:02d}', font=font(25), fill=MUTED)
    draw.text((50, 96), chapter.title, font=font(39, True), fill=INK)

    source_path = capture_dir / f'{chapter.capture}.png'
    with Image.open(source_path) as source:
        source = source.convert('RGB')
        if chapter.focus:
            left, top, right, bottom = chapter.focus
            source = source.crop((round(left * source.width), round(top * source.height),
                                  round(right * source.width), round(bottom * source.height)))
        fitted = ImageOps.contain(source, (1816, 718), Image.Resampling.LANCZOS)
    x, y = (W - fitted.width) // 2, 170 + (718 - fitted.height) // 2
    draw.rounded_rectangle((x-2, y-2, x+fitted.width+2, y+fitted.height+2),
                           radius=6, fill=LINE)
    # The application image is proportionally resized, never redrawn or replaced.
    image.paste(fitted, (x, y))
    draw = ImageDraw.Draw(image)
    draw.text((52, 914), chapter.caption, font=font(28, True), fill=INK)
    draw.line((52, 958, W-52, 958), fill=LINE, width=2)
    draw.text((52, 1042), 'EDITED SCREENSHOT WALKTHROUGH', font=font(19, True), fill=MUTED)
    disclosure = 'Synthetic fixture  /  Real local model output  /  Waiting time abbreviated'
    if chapter.focus:
        disclosure += '  /  Detail crop'
    face = font(19)
    draw.text((W - 52 - draw.textlength(disclosure, font=face), 1042),
              disclosure, font=face, fill=MUTED)
    image.save(output)


def subtitle_chunks(text: str, max_chars: int = 87) -> list[str]:
    """Approximate speech timing is disclosed in the exported manifest."""
    sentences = re.split(r'(?<=[.!?;])\s+', text)
    result: list[str] = []
    for sentence in sentences:
        words, line = sentence.split(), ''
        for word in words:
            candidate = f'{line} {word}'.strip()
            if line and len(candidate) > max_chars:
                result.append(line)
                line = word
            else:
                line = candidate
        if line:
            result.append(line)
    return result


def ass_time(seconds: float) -> str:
    centis = round(seconds * 100)
    hours, centis = divmod(centis, 360000)
    minutes, centis = divmod(centis, 6000)
    secs, centis = divmod(centis, 100)
    return f'{hours}:{minutes:02d}:{secs:02d}.{centis:02d}'


def srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}'


def subtitles(chapters: list[Chapter], durations: list[float],
              speech_seconds: list[float], output: Path) -> None:
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Segoe UI,30,&H002B3529,&H002B3529,&H00E6F0F2,&H00E6F0F2,0,0,0,0,100,100,0,0,1,1,0,2,95,95,62,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    ass_lines, srt_lines = [header], []
    offset, serial = 0.0, 1
    for chapter, duration, spoken in zip(chapters, durations, speech_seconds, strict=True):
        chunks = subtitle_chunks(chapter.narration)
        weights = [len(chunk.split()) for chunk in chunks]
        total = sum(weights)
        # Captions follow narration approximately, with a short final reading hold.
        active = min(duration - 0.8, spoken if spoken else duration - 1.0)
        cursor = offset + 0.25
        for chunk, weight in zip(chunks, weights, strict=True):
            end = min(offset + duration - 0.5, cursor + active * weight / total)
            safe = chunk.replace('{', '(').replace('}', ')')
            ass_lines.append(f'Dialogue: 0,{ass_time(cursor)},{ass_time(end)},Default,,0,0,0,,{safe}\n')
            srt_lines.append(f'{serial}\n{srt_time(cursor)} --> {srt_time(end)}\n{chunk}\n\n')
            serial += 1
            cursor = end
        offset += duration
    (output / 'subtitles.ass').write_text(''.join(ass_lines), encoding='utf-8')
    (output / 'subtitles.srt').write_text(''.join(srt_lines), encoding='utf-8')


def chapters_for(demo: dict) -> list[Chapter]:
    elapsed = f"{demo['elapsed_ms'] / 1000:.1f}"
    calls = demo['successful_tool_calls']
    total_calls = demo['total_tool_calls']
    rejected = demo['rejected_tool_calls']
    # This video is a documentary of the approved capture set, not a template
    # which silently changes the account of any future failed tool request.
    assert (total_calls, calls, rejected) == (6, 5, 1), 'Revise the narration for a different captured run.'
    assert demo['tool_collection_turns'] == 2, 'Revise the documented coverage-recovery account.'
    return [
        Chapter('01-introduction', 'A handoff someone else can inspect',
                'Original SampleDock fixture. Saved baseline first; then a separate captured execution.',
                'overview', 18,
                'HANDOFF Ledger makes a release handoff inspectable. This is an edited screenshot '
                'walkthrough of saved, verified local model executions. SampleDock is our original '
                'fictional fixture. The screens and receipts come from the actual application, '
                'with waiting time abbreviated.'),
        Chapter('02-evidence', 'One announcement. Three different decisions.',
                'Saved baseline: C01 supported     /     C02 contradicted     /     C03 unknown',
                'overview', 24,
                'A release announcement says every check passed. The records show three different '
                'decisions: blank display names are rejected, an upgrade loses the saved locale, '
                'and the Japanese language review has not run. This is synthetic evidence, designed '
                'to expose the difference between a failure and missing evidence.',
                focus=(0.10, 0.47, 0.89, 1.0)),
        Chapter('03-execution', 'Real model execution, bounded read-only tools',
                'Captured running view. This edited walkthrough abbreviates waiting time.',
                'running', 20,
                'The running view is a captured moment, not continuous video. Waiting time is '
                'abbreviated. OpenMinion collects evidence through three read-only tools. Its '
                'official schema interface then generates a report. Pydantic and independent '
                'evidence checks decide whether it succeeds.'),
        Chapter('04-handoff', 'Keep failure and uncertainty visible',
                'Model-written findings are checked before the application reports success.',
                'citation', 24,
                'The model preserves all three states: supported, contradicted, and unknown. '
                'It writes concrete findings for the next owner: investigate locale loss and '
                'perform the missing Japanese review. The application does not fill in a '
                'successful fallback report when the model omits those findings.',
                focus=(0.335, 0.59, 0.70, 0.93)),
        Chapter('05-citation', 'Follow a conclusion to its exact source',
                'Source hash + exact excerpt + classification. A citation is an inspectable trail.',
                'citation', 22,
                'The migration citation leads to the exact failed check. Independent validation '
                'checks the source hash, the quoted excerpt, and the claim classification. '
                'A reviewer can inspect the evidence behind the conclusion, instead of treating '
                'a persuasive summary as proof.', focus=(0.11, 0.41, 0.70, 0.72)),
        Chapter('06-receipts', 'Measure the workflow. Retain the evidence.',
                f'Captured: {elapsed}s / {calls} succeeded / {rejected} rejected / 2 Agent turns. Frozen repeats: 1 turn each.',
                'details', 24,
                f'The captured run took {elapsed} seconds. Five calls succeeded; a zero-index '
                'read was rejected. The coverage guard required a bounded second Agent turn, '
                'which read a valid span. Both validation layers passed. Earlier fresh sessions '
                'needed no recovery: six successful calls in fifty-five seconds, then seven '
                'in fifty-three. These are fixture measurements, not general reliability.'),
        Chapter('07-limits', 'Useful failures. Honest boundaries.',
                'Small structured files. Human review required. Codex-assisted development.',
                'result', 22,
                'An earlier valid JSON answer omitted unknowns and risks; our verifier rejected it. '
                'This prototype reads small structured files. It does not run project tests '
                'or approve a release. Its explanations still need human review. '
                'Codex assisted development. HANDOFF Ledger leaves the next owner '
                'a handoff they can inspect.'),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', required=True, type=Path)
    parser.add_argument('--ffprobe', required=True, type=Path)
    parser.add_argument('--captures', default=ROOT / 'artifacts/demo/captures', type=Path)
    parser.add_argument('--receipt', default=ROOT / 'artifacts/demo/demo-run.json', type=Path)
    parser.add_argument('--output', default=ROOT / 'artifacts/demo', type=Path)
    parser.add_argument('--voice', default='Microsoft Zira Desktop')
    parser.add_argument('--no-voice', action='store_true', help='Use subtitles and silent AAC audio')
    parser.add_argument('--prepare-only', action='store_true', help='Validate inputs and make frames/audio only')
    parser.add_argument('--keep-edit', action='store_true', help='Retain regenerable intermediate files for local QA')
    args = parser.parse_args()
    for tool in (args.ffmpeg, args.ffprobe):
        if not tool.is_file():
            raise FileNotFoundError(f'Required tool missing: {tool.name}')
    # Refuse outputs outside the project and require real supplied source images.
    relative(args.output)
    missing = [name for name in CAPTURE_NAMES if not (args.captures / f'{name}.png').is_file()]
    if missing:
        raise FileNotFoundError('Actual UI captures required: ' + ', '.join(missing))
    receipt_paths = [args.receipt, ROOT / 'artifacts/attempt-7.json', ROOT / 'artifacts/repeat-2.json']
    receipts = [checked_receipt(path, require_clean=index > 0)
                for index, path in enumerate(receipt_paths)]
    if [(r['successful_tool_calls'], r['elapsed_ms']) for r in receipts[1:]] != [(6, 55317), (7, 53411)]:
        raise ValueError('Frozen validation facts changed; revise the narrative.')
    assert all(r['tool_collection_turns'] == 1 for r in receipts[1:]), 'Frozen runs did not need recovery.'
    chapters = chapters_for(receipts[0])
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    work = output / 'edit'
    work.mkdir(exist_ok=True)
    durations, speech_lengths, chapter_manifest = [], [], []
    for index, chapter in enumerate(chapters):
        still = work / f'{chapter.key}.png'
        speech_text, audio = work / f'{chapter.key}.txt', work / f'{chapter.key}.wav'
        render_frame(chapter, index, len(chapters), args.captures, still)
        speech_text.write_text(chapter.narration, encoding='utf-8')
        if not args.no_voice:
            run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                 str(ROOT / 'tools/synthesize_demo.ps1'), '-TextPath', str(speech_text),
                 '-OutputPath', str(audio), '-Voice', args.voice])
            with wave.open(str(audio)) as stream:
                spoken = stream.getnframes() / stream.getframerate()
        else:
            spoken = 0.0
        duration = math.ceil(max(chapter.seconds, spoken + 1.5) * FPS) / FPS
        durations.append(duration)
        speech_lengths.append(spoken)
        chapter_manifest.append({'chapter': chapter.key, 'title': chapter.title,
                                 'capture': relative(args.captures / f'{chapter.capture}.png'),
                                 'detail_crop_normalized': chapter.focus,
                                 'duration_seconds': duration, 'speech_seconds': spoken,
                                 'narration': chapter.narration})
    total = sum(durations)
    if not 120 <= total <= 180:
        raise ValueError(f'{total:.2f}s is outside the approved 120-180s cut. Edit narration first.')
    subtitles(chapters, durations, speech_lengths, work)
    manifest = {'format': 'edited screenshot walkthrough of saved real executions',
                'fixture': 'Original fictional SampleDock fixture',
                'waiting_time': 'abbreviated', 'continuous_screen_recording': False,
                'audio': 'Local Windows System.Speech' if not args.no_voice else 'Silent AAC / English captions',
                'subtitle_timing': 'Approximate word-weight timing against local narration duration',
                'receipts': receipts,
                'captures': [{'file': relative(args.captures / f'{name}.png'),
                              'sha256': sha256(args.captures / f'{name}.png')}
                             for name in CAPTURE_NAMES],
                'chapters': chapter_manifest, 'planned_duration_seconds': total}
    (output / 'media-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (output / 'narration.txt').write_text('\n\n'.join(c.narration for c in chapters) + '\n', encoding='utf-8')
    (output / 'subtitles.srt').write_text((work / 'subtitles.srt').read_text(encoding='utf-8'), encoding='utf-8')
    print(f'Prepared {len(chapters)} chapters, {total:.3f} seconds; actual screenshots only.')
    if args.prepare_only:
        return
    for chapter, duration in zip(chapters, durations, strict=True):
        audio_args = (['-i', f'{chapter.key}.wav'] if not args.no_voice else
                      ['-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono'])
        run([str(args.ffmpeg), '-hide_banner', '-loglevel', 'error', '-y',
             '-loop', '1', '-framerate', str(FPS), '-i', f'{chapter.key}.png', *audio_args,
             '-vf', 'format=yuv420p', '-af', 'apad', '-t', f'{duration:.6f}',
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-tune', 'stillimage',
             '-r', str(FPS), '-c:a', 'aac', '-b:a', '128k', '-ar', '48000',
             '-movflags', '+faststart', f'{chapter.key}.mp4'], cwd=work)
    concat = ''.join(f"file '{chapter.key}.mp4'\n" for chapter in chapters)
    (work / 'concat.txt').write_text(concat, encoding='ascii')
    run([str(args.ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat',
         '-safe', '1', '-i', 'concat.txt', '-c', 'copy', 'joined.mp4'], cwd=work)
    final = output / 'handoff-ledger-demo.mp4'
    run([str(args.ffmpeg), '-hide_banner', '-loglevel', 'error', '-y', '-i', 'joined.mp4',
         '-vf', 'ass=subtitles.ass', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
         '-c:a', 'copy', '-movflags', '+faststart', str(final)], cwd=work)
    probe = json.loads(run([str(args.ffprobe), '-v', 'error', '-show_entries',
                          'format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate',
                          '-of', 'json', str(final)]))
    duration = float(probe['format']['duration'])
    assert 120 <= duration <= 180, 'Encoded duration out of range'
    assert any(s['codec_type'] == 'video' and s['codec_name'] == 'h264' for s in probe['streams'])
    assert any(s['codec_type'] == 'audio' and s['codec_name'] == 'aac' for s in probe['streams'])
    manifest['output'] = {'file': relative(final), 'sha256': sha256(final), 'probe': probe}
    (output / 'media-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    if not args.keep_edit:
        owned_names = {'joined.mp4', 'concat.txt', 'subtitles.ass', 'subtitles.srt'}
        owned_names.update(f'{chapter.key}{suffix}' for chapter in chapters
                           for suffix in ('.png', '.txt', '.wav', '.mp4'))
        for name in owned_names:
            (work / name).unlink(missing_ok=True)
        if not any(work.iterdir()):
            work.rmdir()
    print(json.dumps(manifest['output'], indent=2))


if __name__ == '__main__':
    main()
