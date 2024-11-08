FROM python:3.11-slim

# Install dependencies
COPY pyproject.toml README.md* ./
RUN pip install .

# Add source code
WORKDIR /src
COPY ./src/ ./

# Run the application
ENTRYPOINT ["python", "stream.py"]
