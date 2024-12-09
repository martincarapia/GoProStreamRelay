# GoPro Stream Relay

This project allows you to manage and relay GoPro streams.

## Build instructions

Ensure that you have Python <3.12, >=3.9 installed.

```sh
python --version
```

Clone project and Install python requirements

```sh
git clone https://github.com/martincarapia/GoProStreamRelay.git
cd GoProStreamRelay
pip install -r requirements.txt
```

Build executable based on your operating system

```sh
pyinstaller buildspecfiles/(win|mac|linux)build.spec
```

Look in the dist folder and run the built executable and enjoy!

## Usage

Follow this easy youtube video and following along with setup
VIDEO HERE

Install <https://github.com/martincarapia/DynamicStreamManager.git> on a server and get it running \
Then install latest release of GoPro Stream Relay.

This is made possible due to [Medical Informatics Engineering](https://github.com/mieweb) for who I'm developing this for.
