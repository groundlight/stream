FROM alpine:3
RUN apk add \
    aws-cli \
    g++ \
    gfortran \
    groundlight \
    openblas-dev \
    python3-dev \
    py3-pip
ADD requirements.txt /src/
WORKDIR /src
RUN aws codeartifact login --domain positronix --repository internal --tool pip
RUN pip3 install -r requirements.txt
ADD . /src/
CMD ["python3","astro.py"]
