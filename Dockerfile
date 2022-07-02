# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10.5-bullseye AS compile-image

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install pip requirements
COPY requirements.txt .

RUN curl https://sh.rustup.rs -sSf -o install-rust.sh
RUN sh install-rust.sh -q -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN python -m pip install --user -r requirements.txt

FROM python:3.10.5-slim-bullseye as build-image
WORKDIR /app
COPY --from=compile-image /root/.local /app/.local

COPY . /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd -d /app appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "retriever.py"]
