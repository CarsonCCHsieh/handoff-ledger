# HANDOFF Ledger demonstration

The final local video is [handoff-ledger-demo.mp4](handoff-ledger-demo.mp4):
165.416 seconds, 1920 x 1080 at 24 fps, H.264 video and AAC English narration.
English subtitles are burned into the video and supplied separately in
[subtitles.srt](subtitles.srt). Narration was synthesized locally with Windows
System.Speech, without a hosted API or paid service.

This is an **edited screenshot walkthrough of saved real executions**, not a
continuous screen recording. Waiting time is abbreviated. SampleDock is original
fictional evidence. All application images came from the actual local UI; detail
crops are labelled. The opening shows a saved baseline, followed by screenshots
of a separate, real UI-triggered model execution. No application result was
redrawn or substituted by the media builder.

The separate captured execution is preserved unchanged as
[demo-run.json](demo-run.json). It took 84.348 seconds and passed typed and
independent evidence validation. Of six actual tool calls, five succeeded and one
zero-index `read_span` was rejected. The coverage guard required a bounded second
Agent turn, which read a valid span. The two earlier frozen receipts remain
distinct: `attempt-7.json` has six successful calls in 55.317 seconds, and
`repeat-2.json` has seven in 53.411 seconds. Those earlier runs each used one
collection turn and did not require coverage recovery. These measurements concern
this fixture, not general reliability.

[media-manifest.json](media-manifest.json) records the final output hash,
ffprobe results, source-capture and receipt hashes, chapter timings, crop regions,
and the exact English narration. [qa/review.json](qa/review.json) records the
local verification, with extracted frames under `qa/` for review. Captions use
approximate word-weight timing against each locally generated narration clip.

To rebuild from the project root, provide existing ffmpeg and ffprobe binaries
and a Python environment with Pillow installed:

```powershell
python tools/build_demo.py --ffmpeg "<path-to-ffmpeg.exe>" --ffprobe "<path-to-ffprobe.exe>"
```

The builder requires the five real source images in `captures/` and all three
checked receipts. It rejects missing images or changed run facts. Windows uses
the installed Microsoft Zira Desktop voice; `--no-voice` creates an English
caption version with silent AAC audio. `--prepare-only` prepares local stills and
audio for inspection, while `--keep-edit` retains regenerable intermediates.
The default completed build removes its own intermediates. Nothing is uploaded.

Final MP4 SHA-256:

```text
d049804e85aedd672f312d26a9f00605a450107ce17858f5bd9da3956c14e4e7
```
