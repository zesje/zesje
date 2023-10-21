# A Dockerfile containing the production deployment for Zesje

FROM mambaorg/micromamba:1.5-jammy

USER root

RUN apt-get update && \
    apt-get install -y libdmtx-dev

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/env.yaml
USER $MAMBA_USER
RUN micromamba install -y -n base -f /tmp/env.yaml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

USER root
WORKDIR /yarn
ADD package.json .
RUN yarn install
RUN rm package.json

WORKDIR /app

CMD bash
