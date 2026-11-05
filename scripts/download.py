#!/usr/bin/env python3
"""Download HLS with yt-dlp, preserve resumable state, and verify the MP4."""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import yt_dlp
from yt_dlp.downloader import fragment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--referer', required=True)
    parser.add_argument('--origin')
    parser.add_argument('--user-agent')
    parser.add_argument('--job', required=True, help='Stable ID for this video only')
    parser.add_argument('--output', type=Path, default=Path('outputs'))
    parser.add_argument('--ffmpeg-location', type=Path)
    parser.add_argument('--recover-ts', action='store_true', help='Opt in to lossy TS recovery')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.job):
        parser.error('--job must contain only letters, digits, _ and -')
    for url in (args.url, args.referer):
        if not url.startswith(('https://', 'http://')):
            parser.error('Only HTTP(S) URLs are supported')
    media_dir = args.ffmpeg_location
    if media_dir and media_dir.is_file():
        media_dir = media_dir.parent
    ffprobe = str(media_dir / 'ffprobe') if media_dir else shutil.which('ffprobe')
    ffmpeg = str(media_dir / 'ffmpeg') if media_dir else shutil.which('ffmpeg')
    if not ffprobe or not ffmpeg:
        parser.error('Install FFmpeg and ffprobe, or use --ffmpeg-location')
    for executable in (ffmpeg, ffprobe):
        subprocess.run([executable, '-version'], check=True, stdout=subprocess.DEVNULL)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / '.video-down' / args.job
    temporary.mkdir(parents=True, exist_ok=True)
    # Serialize writers for a job, including FFmpeg postprocessing.
    import fcntl
    lock = (temporary / 'download.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('This job is already downloading')
    recovery_log = temporary / 'recovery.jsonl'
    original_decrypt = fragment.aes_cbc_decrypt_bytes

    def recover_decrypt(data, key, iv):
        remainder = len(data) % 16
        if not remainder:
            return original_decrypt(data, key, iv)
        plaintext = original_decrypt(data[:-remainder], key, iv)
        usable = len(plaintext) // 188 * 188
        if not usable or any(plaintext[i] != 0x47 for i in range(0, usable, 188)):
            raise ValueError('Malformed fragment has no valid aligned MPEG-TS payload')
        with recovery_log.open('a') as record:
            record.write(json.dumps({'bytes_received': len(data), 'bytes_kept': usable}) + '\n')
        print('WARNING: recovered complete TS packets from a damaged fragment')
        # yt-dlp removes PKCS7 padding after this callback.
        return plaintext[:usable] + b'\x01'

    headers = {'Referer': args.referer}
    if args.origin:
        headers['Origin'] = args.origin
    if args.user_agent:
        headers['User-Agent'] = args.user_agent
    options = {
        'http_headers': headers,
        'paths': {'home': str(output), 'temp': str(temporary)},
        'outtmpl': args.job + '.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'postprocessors': [{'key': 'FFmpegVideoRemuxer', 'preferedformat': 'mp4'}],
        'concurrent_fragment_downloads': 6,
        'socket_timeout': 20,
        'retries': 2,
        'fragment_retries': 3,
        'skip_unavailable_fragments': False,
        'continuedl': True,
        'overwrites': False,
        'noplaylist': True,
    }
    if media_dir:
        options['ffmpeg_location'] = str(media_dir)
    if args.recover_ts:
        fragment.aes_cbc_decrypt_bytes = recover_decrypt
    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([args.url])
    finally:
        fragment.aes_cbc_decrypt_bytes = original_decrypt
    result = output / (args.job + '.mp4')
    probe = subprocess.run([
        ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(result),
    ], check=True, capture_output=True, text=True)
    metadata = json.loads(probe.stdout)
    if not any(s['codec_type'] == 'video' for s in metadata['streams']):
        raise RuntimeError('No video stream in downloaded file')
    if float(metadata['format'].get('duration', 0)) <= 0:
        raise RuntimeError('Invalid output duration')
    metadata['recovered_fragments'] = len(recovery_log.read_text().splitlines()) if recovery_log.exists() else 0
    metadata['validation'] = 'Container and streams checked. Full decode not performed.'
    report = output / (args.job + '.verification.json')
    report.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(f'File saved to {result}')
    print(f'Recovered fragments: {metadata["recovered_fragments"]}')


if __name__ == '__main__':
    main()
