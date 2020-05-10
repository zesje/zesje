# A Dockerfile containing the production deployment for Zesje

FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get install -y libdmtx0b && \
    apt-get install -y git supervisor nginx cron

WORKDIR /app

ADD environment.yml .
RUN conda env create && conda clean --all

RUN echo "source activate zesje-dev" > ~/.bashrc
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

ADD . .
RUN yarn install
RUN yarn build

RUN rm -rf node_modules

ENTRYPOINT [ "/bin/bash" ]
