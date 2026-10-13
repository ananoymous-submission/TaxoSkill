# Build the minimal Java 11 runtime required by ScienceWorld.
FROM eclipse-temurin:11-jdk-jammy AS java-runtime
RUN jlink \
    --add-modules java.base,java.desktop,java.logging,java.management \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=2 \
    --output /opt/java-minimal

FROM python:3.11-slim

COPY --from=java-runtime /opt/java-minimal /opt/java

ENV JAVA_HOME=/opt/java \
    PATH="/opt/java/bin:${PATH}" \
    PORT=8000 \
    MAX_CONCURRENT_ENVS=1 \
    DEFAULT_TASK_ID=0 \
    ENABLE_WEB_INTERFACE=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 1000 user
WORKDIR /home/user/app
COPY --chown=user:user . /home/user/app
RUN pip install --no-cache-dir --no-compile ".[server]"

USER user
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

CMD ["sh", "-c", "uvicorn scienceworld_env.server.app:app --host 0.0.0.0 --port ${PORT}"]
