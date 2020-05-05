# A Dockerfile containing the production deployment for Zesje

FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get install -y libdmtx0b && \
    apt-get install -y git supervisor nginx

WORKDIR /app

ADD environment.yml /app/environment.yml
RUN conda env create

RUN echo "source activate zesje-dev" > ~/.bashrc
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

ADD . .
RUN yarn install
RUN yarn build

ENTRYPOINT [ "/bin/bash" ]
