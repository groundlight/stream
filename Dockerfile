FROM python:3.11-slim

# Install dependencies
ADD pyproject.toml Makefile
WORKDIR /src
RUN make install

# Add source code
ADD ./src/ /src/

# Run the application
ENTRYPOINT ["python","stream.py"]
