# Groundlight Stream Processor

A containerized python application that uses the [Groundlight](https://www.groundlight.ai/) [Python SDK](https://github.com/groundlight/python-sdk) to
process frames from a video file, device, or stream.

## Table of Contents
- [Groundlight Stream Processor](#groundlight-stream-processor)
  - [Table of Contents](#table-of-contents)
  - [Download](#download)
  - [Usage](#usage)
  - [Examples](#examples)
    - [Running with a Local MP4 File](#running-with-a-local-mp4-file)
    - [Using a YouTube URL](#using-a-youtube-url)
    - [Connecting an RTSP Stream](#connecting-an-rtsp-stream)
  - [Further Reading](#further-reading)

## Download

This application is easy to use on any system with Docker installed.

```shell
$ docker pull groundlight/stream
```

## Usage

Command line options are displayed like:

``` shell
$ docker run -it groundlight/stream -h
usage: python -m stream -t TOKEN -d DETECTOR [options]

Groundlight Stream Processor

A command-line tool that captures frames from a video source and sends them to a Groundlight detector for analysis.

Supports a variety of input sources including:
- Video devices (webcams)
- Video files (mp4, etc)
- RTSP streams
- YouTube videos
- Image directories
- Image URLs

options:
  -h, --help            show this help message and exit
  -t TOKEN, --token TOKEN
                        Groundlight API token for authentication.
  -d DETECTOR, --detector DETECTOR
                        Detector ID to send ImageQueries to.
  -e ENDPOINT, --endpoint ENDPOINT
                        API endpoint to target. For example, could be pointed at an edge-endpoint proxy server (https://github.com/groundlight/edge-endpoint).
  -s STREAM, --stream STREAM
                        Video source. A device ID, filename, or URL. Defaults to device ID '0'.
  -x {infer,device,directory,rtsp,youtube,file,image_url}, --streamtype {infer,device,directory,rtsp,youtube,file,image_url}
                        Source type. Defaults to 'infer' which will attempt to set this value based on --stream.
  -f FPS, --fps FPS     Frames per second to capture (0 for max rate). Defaults to 1 FPS.
  -v, --verbose         Enable debug logging.
  -m, --motion          Enables motion detection, which is disabled by default.
  -r THRESHOLD, --threshold THRESHOLD
                        Motion detection threshold (% pixels changed). Defaults to 1%.
  -p POSTMOTION, --postmotion POSTMOTION
                        Seconds to capture after motion detected. Defaults to 1 second.
  -i MAXINTERVAL, --maxinterval MAXINTERVAL
                        Max seconds between frames even without motion. Defaults to 1000 seconds.
  -w RESIZE_WIDTH, --width RESIZE_WIDTH
                        Resize width in pixels.
  -y RESIZE_HEIGHT, --height RESIZE_HEIGHT
                        Resize height in pixels.
  -c CROP, --crop CROP  Crop region, specified as fractions (0-1) of each dimension (e.g. '0.25,0.2,0.8,0.9').
```

Start sending frames and getting predictions and labels using your own API token and detector ID:

``` shell
docker run groundlight/stream \
    -t api_29imEXAMPLE \
    -d det_2MiD5Elu8bza7sil9l7KPpr694a \
    -s https://www.youtube.com/watch?v=210EXAMPLE \
    -f 1
```

## Examples
### Running with a Local MP4 File

To process frames from a local MP4 file, you need to mount the file from your host machine into the Docker container. Here's how to do it:

1. Place your MP4 file (e.g., `video.mp4`) in a directory on your host machine, such as `/path/to/video`.
2. Run the Docker container, mounting the directory containing the video file:

``` shell
docker run -v /path/to/video:/videos groundlight/stream \
    -t api_29imEXAMPLE \
    -d det_2MiD5Elu8bza7sil9l7KPpr694a \
    -s /videos/video.mp4 \
    -f 1
```

This command mounts the `/path/to/video` directory on your host machine to the `/videos` directory inside the Docker container. The `-s` parameter is then set to the path of the MP4 file inside the container (`/videos/video.mp4`).

### Using a YouTube URL
YouTube URLs can be used to send frames to a detector by passing the video URL to the `-s` parameter:

``` shell
# Live Video from the International Space Station (Official NASA Stream)
YOUTUBE_URL="https://www.youtube.com/watch?v=xAieE-QtOeM"

docker run groundlight/stream \
    -t api_29imEXAMPLE \
    -d det_2MiD5Elu8bza7sil9l7KPpr694a \
    -s "${YOUTUBE_URL}" \
    -f 1
```

Replace `YOUTUBE_URL` with the url of the YouTube video you are interested in.

### Connecting an RTSP Stream

To connect an RTSP stream from a camera or other source, you'll need the RTSP URL specific to your device. Check the instructions provided earlier in this document for obtaining the RTSP URL for your camera.

Once you have the RTSP URL, pass it to the `-s` parameter:

``` shell
docker run groundlight/stream \
    -t api_29imEXAMPLE \
    -d det_2MiD5Elu8bza7sil9l7KPpr694a \
    -s "rtsp://username:password@camera_ip_address:554/path/to/stream" \
    -f 1
```

Replace the RTSP URL with the one specific to your camera or streaming device.


## Further Reading

* [Camera types](CAMERAS.md) shows how to get RTSP stream URLs for many popular camera brands.
* [Developing](DEVELOPING.md) discusses how this code is built and maintained.
