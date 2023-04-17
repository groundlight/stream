# Groundlight Stream Processor

A containerized python application that uses the Groundlight SDK to
process frames from a video stream.  This can connect to a web cam over RTSP, a local video file, or a youtube URL.

## Releases

Releases created in Github will automatically get built and pushed to [dockerhub](https://hub.docker.com/r/groundlight/stream/tags).  These are multi-architecture builds including x86 and ARM.

## Test Builds

To build and test locally:

``` shell
docker build -t stream:local .
```

## Run
Now you can run it

``` shell
docker run stream:local -h
```


# Video Stream types - Local files

You can point to a local mp4 file.

# Video Stream types - Youtube

You can specify a youtube stream.

# Video Stream types - RTSP Cameras

Many WiFi and Ethernet cameras offer RTSP streams. Here are some common examples.

## Unifi Protect Cameras

To get an RTSP stream from a Unifi Protect camera, first open the Unifi Protect web application.
Then select "Unifi Devices", and find the device you want to connect to. In the right-panel, select "Settings"
Open the Advanced section, and you will find an RTSP section. Pick a resolution to stream at, and enable the stream. Then an RTSP url will appear below your selection.

## Hikvision Cameras

To get an RTSP stream from a Hikvision camera, follow these steps:

1. Open the camera's web interface by entering its IP address in your web browser.
2. Log in using your camera's username and password.
3. Go to Configuration > Network > Advanced Settings > Integration Protocol.
4. Enable the RTSP protocol and set the Authentication method to "digest/basic".
5. Construct the RTSP URL using the following format:
   rtsp://<username>:<password>@<camera_ip_address>:554/Streaming/Channels/<channel>

   Replace `<username>`, `<password>`, `<camera_ip_address>`, and `<channel>` with the appropriate values. The channel is typically 101 for the main stream and 102 for the substream.

## Axis Cameras

To get an RTSP stream from an Axis camera, follow these steps:

1. Open the camera's web interface by entering its IP address in your web browser.
2. Log in using your camera's username and password.
3. Go to Setup > Video > Stream Profiles.
4. Click "Add" to create a new profile, or edit an existing profile.
5. Configure the desired video and audio settings for the stream, and enable the RTSP protocol.
6. Click "Save" to save the settings.
7. Construct the RTSP URL using the following format:
   rtsp://<username>:<password>@<camera_ip_address>/axis-media/media.amp?videocodec=h264&streamprofile=<profile_name>

   Replace `<username>`, `<password>`, `<camera_ip_address>`, and `<profile_name>` with the appropriate values.

## Foscam Cameras

To get an RTSP stream from a Foscam camera, follow these steps:

1. Open the camera's web interface by entering its IP address in your web browser.
2. Log in using your camera's username and password.
3. Go to Settings > Network > IP Configuration.
4. Note the camera's IP address, HTTP port, and RTSP port.
5. Construct the RTSP URL using the following format:
   rtsp://<username>:<password>@<camera_ip_address>:<rtsp_port>/videoMain

   Replace `<username>`, `<password>`, `<camera_ip_address>`, and `<rtsp_port>` with the appropriate values.

## Amcrest Cameras

To get an RTSP stream from an Amcrest camera, follow these steps:

1. Open the camera's web interface by entering its IP address in your web browser.
2. Log in using your camera's username and password.
3. Go to Setup > Network > Connection.
4. Note the camera's RTSP port.
5. Construct the RTSP URL using the following format:
   rtsp://<username>:<password>@<camera_ip_address>:<rtsp_port>/cam/realmonitor?channel=1&subtype=<stream_type>

   Replace `<username>`, `<password>`, `<camera_ip_address>`, `<rtsp_port>`, and `<stream_type>` with the appropriate values. The stream type is typically 0 for the main stream and 1 for the substream.


