# streamlight
A containerized python application that uses the [groundlight](https://www.groundlight.ai/) sdk to
process frames from a video file, device or stream.

## run
The entrypoint of the image is the CLI which will process the input video.
``` shell
docker run groundlight/stream -h

Captures frames from a video file, device or stream and sends frames as
image queries to a configured detector using the Groundlight API

usage: stream [options] -t TOKEN -d DETECTOR

options:
  -d, --detector=ID      detector id to which the image queries are sent
  -e, --endpoint=URL     api endpoint [default: https://device.positronix.ai/device-api]
  -f, --framerate=FPS    number of frames to capture per second.
  -h, --help             show this message.
  -s, --stream=STREAM    id, filename or URL of a video stream (e.g. rtsp://host:port/script?params) [default: 0]
  -t, --token=TOKEN      token to authenticate with the Groundlight API
  -v, --verbose
```
Start sending frames and getting predictions and labels using your own API token and detector ID
``` shell
docker run groundlight/stream -t api_29imEXAMPLE -d 772d5b0EXAMPLE -s https://www.youtube.com/watch?v=21X5lGlDOfg -f 1
```
# license
This image includes the [groundlight
sdk](https://pypi.org/project/groundlight/) which is published under
the MIT license

As with all Docker images, this image also contains other software
which may be under other licenses (along with any direct or indirect
dependencies of the primary software being contained) all of which is
published under open source licenses.

As for any pre-built image usage, it is the image user's
responsibility to ensure that any use of this image complies with any
relevant licenses for all software contained within.
