# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-bullseye AS compile-image

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install pip requirements
COPY . .

RUN python3.11 -m venv /app/venv
ENV PATH=/app/venv/bin:$PATH
RUN /app/venv/bin/pip3 install build
RUN /app/venv/bin/python -m build --wheel
RUN /app/venv/bin/pip3 install dist/*.whl

FROM python:3.11-slim-bullseye as build-image
WORKDIR /app
COPY --from=compile-image /app/venv /app/venv

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd -d /app appuser && chown -R appuser /app
USER appuser

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["retriever"]
