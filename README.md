# Last.fm Timelapse

Display a bar chart race animation based on your last.fm scrobbles.

## Installation

### Prerequisites

* [Python >= 3.8](https://www.python.org/)
* [ffmpeg](https://www.ffmpeg.org/download.html)
* [lastfm-backup](https://github.com/D62/lastfm-backup)
* last.fm history file generated with [lastfm-backup](https://github.com/D62/lastfm-backup)

#### Installing ffmpeg

In order to save animations as mp4 files, you must install [ffmpeg](https://www.ffmpeg.org/download.html), which allows for conversion to many different formats of video and audio. For macOS users, installation may be [easier using Homebrew](https://trac.ffmpeg.org/wiki/CompilationGuide/macOS#ffmpegthroughHomebrew).

After installation, ensure that `ffmpeg` has been added to your path by going to your command line and entering `ffmepg -version`.

### Steps

1. Clone the repository:

```
git clone https://github.com/d62/lastfm-timelapse
```

2. Navigate to its root:

```
cd lastfm-timelapse
```

3. Create a new Python virtual environment:

```
python -m venv .venv
```

4. Activate the environment:

```bash
.venv/bin/activate
```

5. Install the requirements:

```
pip install -r requirements.txt
```

## How to use:
* Run `app.py`
* Follow the instructions