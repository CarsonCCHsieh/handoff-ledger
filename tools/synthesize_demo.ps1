param(
    [Parameter(Mandatory=$true)][string]$TextPath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [string]$Voice = 'Microsoft Zira Desktop',
    [int]$Rate = 0
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$narration = [System.IO.File]::ReadAllText($TextPath, [System.Text.Encoding]::UTF8)
$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synthesizer.SelectVoice($Voice)
    $synthesizer.Rate = $Rate
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
        24000,
        [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono
    )
    $synthesizer.SetOutputToWaveFile($OutputPath, $format)
    $synthesizer.Speak($narration)
} finally {
    $synthesizer.Dispose()
}
