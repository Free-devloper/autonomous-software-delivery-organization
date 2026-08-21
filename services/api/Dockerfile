FROM docker.io/library/python:3.13.13-slim-bookworm@sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN groupadd --system --gid 10001 asdo \
  && useradd --system --uid 10001 --gid asdo --home-dir /nonexistent --shell /usr/sbin/nologin asdo

COPY dist/asdo-api-requirements.txt /tmp/asdo-api-requirements.txt
COPY dist/*.whl /tmp/
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/asdo-api-requirements.txt \
  && python -m pip install --no-cache-dir --no-deps /tmp/*.whl \
  && rm /tmp/*.whl /tmp/asdo-api-requirements.txt

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "autonomous_sdo_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
