# syntax=docker/dockerfile:1.7
FROM python:3.15-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.15-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Pick up OS security fixes published after the base image was built.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app
COPY --from=build /install /usr/local
# The runtime image needs no packaging tools. Removing pip also removes the libraries it
# vendors, which image scanners report (pip bundles an old setuptools).
RUN pip uninstall -y setuptools pip
WORKDIR /srv
COPY app ./app
USER 10001
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
