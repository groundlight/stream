FROM alpine:3
RUN apk add \
    python3 \
    py3-pip
ADD requirements.txt /src/
WORKDIR /src
RUN pip3 install -r requirements.txt
ADD . /src/
CMD ["python3","astro.py"]
