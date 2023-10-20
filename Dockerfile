# A Dockerfile containing the production deployment for Zesje

FROM mambaorg/micromamba:1.5-jammy

USER root

RUN apt-get update && \
    apt-get install -y libdmtx-dev && \
    apt-get install -y git supervisor nginx cron

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml
USER $MAMBA_USER
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
USER root
WORKDIR /app
ADD . .
RUN yarn install
RUN yarn build

RUN rm -rf node_modules

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "/usr/bin/bash"]
