# A Dockerfile containing the production deployment for Zesje

FROM continuumio/miniconda3

RUN apt-get -o Acquire::Check-Valid-Until=false update && \
    apt-get install -y \
        curl \
        poppler-utils build-essential libgl1-mesa-glx \
        imagemagick libsm-dev libdmtx-dev libdmtx0b \
        && \
    apt-get -y --quiet install git supervisor nginx

WORKDIR /app

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

CMD bash
