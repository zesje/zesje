# A Dockerfile containing the production deployment for Zesje

FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get install -y libdmtx0b gcc

WORKDIR /yarn

# Setup PYTHON packages

ADD environment.yml .
RUN conda env create && conda clean --all

# From https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
RUN echo "source activate zesje-dev" > ~/.bashrc
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

RUN rm environment.yml

# Setup YARN packages

ADD package.json .
RUN yarn install
RUN rm package.json

WORKDIR /app

CMD bash
