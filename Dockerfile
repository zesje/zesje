FROM continuumio/miniconda3

RUN apt-get update -y && apt-get install -y libdmtx0a libmagickwand-dev

RUN apt-get update && \
    apt-get install -y \
        curl \
        poppler-utils build-essential libgl1-mesa-glx \
        imagemagick libsm-dev libdmtx-dev libdmtx0a libmagickwand-dev \
        && \
    apt-get -y --quiet install git supervisor nginx

WORKDIR /app

ADD environment.yml /app/environment.yml
RUN conda env create

# From https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
RUN echo "source activate $(head -1 /app/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /app/environment.yml | cut -d' ' -f2)/bin:$PATH

RUN rm /app/environment.yml

CMD bash
