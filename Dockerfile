# Agenthon 2026 Track 2 forecaster. Run scripts/assemble.sh first (CI does).
FROM python:3.13-slim-bookworm
LABEL qfbench2.interface_version=2.0
LABEL qfbench2.track=forecasting
LABEL qfbench2.verb=forecast
LABEL org.opencontainers.image.source=https://github.com/jeremyam/agenthon-t2-forecaster
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN pip install --no-cache-dir "numpy==2.1.3" "pandas==2.2.3" "pyarrow==18.1.0" "jsonschema==4.23.0" \
    "qfbench2-common @ https://github.com/Agenthon-2026/Agenthon2026-public/archive/refs/tags/v2.6.0.tar.gz#subdirectory=common"
WORKDIR /work
COPY qfbench2_track_forecasting /opt/qfbench2_track_forecasting
ENV PYTHONPATH=/opt
RUN printf '#!/bin/sh\nexec python3 -m qfbench2_track_forecasting.cli "$@"\n' > /usr/local/bin/forecast \
 && chmod +x /usr/local/bin/forecast
RUN useradd --create-home --uid 1000 runner
USER runner
CMD ["forecast", "--help"]
