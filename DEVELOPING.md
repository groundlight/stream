# Groundlight Stream Processor

A containerized python application that uses the Groundlight SDK to process frames from a video stream.
This can connect to a web cam over RTSP, a local video file, or a youtube URL.

## Releases

Releases created in Github will automatically get built and pushed to [dockerhub](https://hub.docker.com/r/groundlight/stream/tags). These are multi-architecture builds including x86 and ARM.

## Build locally

To build locally:

``` shell
docker build -t stream:local .
```

alternatively, run:
```shell
make build
```

## Run locally after building

Now you can run it

``` shell
docker run stream:local -h
```


## Testing

To run the tests, you can run:

```shell
make install-dev
make test
```