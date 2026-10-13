FROM python:3.11-slim

ENV PORT=8000 \
    MAX_CONCURRENT_ENVS=1 \
    DEFAULT_TASK_ID=191 \
    ENABLE_WEB_INTERFACE=true \
    ALFWORLD_DATA=/opt/alfworld \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl git zstd \
    && rm -rf /var/lib/apt/lists/*

COPY runtime-data/alfworld-runtime-assets-json-2.1.1.tar.zst /tmp/alfworld-runtime/
COPY runtime-data/alfworld-runtime-assets-json-2.1.1.tar.zst.sha256 /tmp/alfworld-runtime/
RUN cd /tmp/alfworld-runtime \
    && sha256sum --check alfworld-runtime-assets-json-2.1.1.tar.zst.sha256 \
    && mkdir -p /opt/alfworld \
    && tar --extract --use-compress-program=unzstd \
        --file alfworld-runtime-assets-json-2.1.1.tar.zst \
        --directory /opt/alfworld \
    && test -f /opt/alfworld/logic/alfred.pddl \
    && test -f /opt/alfworld/logic/alfred.twl2 \
    && test -d /opt/alfworld/json_2.1.1/train \
    && test -d /opt/alfworld/json_2.1.1/valid_seen \
    && test -d /opt/alfworld/json_2.1.1/valid_unseen \
    && rm -rf /tmp/alfworld-runtime

RUN useradd --create-home --uid 1000 user
WORKDIR /home/user/app
COPY --chown=user:user pyproject.toml constraints.txt /home/user/app/
COPY --chown=user:user src /home/user/app/src
RUN pip install --no-cache-dir --no-compile -c constraints.txt ".[server]" \
    && python -c 'from pathlib import Path; p=Path("/usr/local/lib/python3.11/site-packages/alfworld/agents/expert/__init__.py"); expected=["from alfworld.agents.expert.handcoded_expert import HandCodedAgentTimeout, HandCodedAgentFailed", "from alfworld.agents.expert.handcoded_expert_tw import HandCodedTWAgent", "from alfworld.agents.expert.handcoded_expert_thor import HandCodedThorAgent"]; actual=p.read_text().splitlines(); assert actual == expected, f"unexpected ALFWorld expert import surface: {actual!r}"; p.write_text("\n".join(expected[:2]) + "\n")' \
    && python -c 'import sys; import alfworld.agents.environment.alfred_tw_env; assert "ai2thor" not in sys.modules; assert "torch" not in sys.modules; assert "torchvision" not in sys.modules' \
    && apt-get purge -y --auto-remove build-essential curl git \
    && rm -rf /var/lib/apt/lists/* /root/.cache/pip

USER user
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

CMD ["sh", "-c", "uvicorn alfworld_env.server.app:app --host 0.0.0.0 --port ${PORT}"]
