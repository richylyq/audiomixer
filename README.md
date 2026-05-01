# audiomixer
The audio mixer is a software application that allows users to import multiple audio files and combine them into a single, cohesive album playlist.

## Instructions
1. Download the [ffmpeg.exe](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-github) file and dump it into the `bin` folder
2. Install [pyinstaller](https://pypi.org/project/pyinstaller/) to build the audiomixer executable `pip install pyinstaller`
3. Build the executable with this command 

```pyinstaller --onefile --noconsole \
--icon "music.ico" \
--add-binary "bin/ffmpeg.exe;bin" \
audio_playlist.py```