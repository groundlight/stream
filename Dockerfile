FROM alpine:3
RUN apk add \
    aws-cli \
    cmake \
    g++ \
    gfortran \
    linux-headers \
    make \
    openblas-dev \
    python3-dev \
    py3-pip
ADD requirements.txt /src/
WORKDIR /src
# authenticate to aws codeartifact - remove this once the groundlight sdk is public
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_ACCESS_KEY_ID
RUN aws codeartifact login --region us-west-2 --domain positronix --repository internal --tool pip
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD . /src/
CMD ["python3","astro.py"]
