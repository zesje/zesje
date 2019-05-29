FROM continuumio/miniconda3

RUN apt-get update -y && apt-get install -y libdmtx0a 

WORKDIR /app

ADD environment.yml /app/environment.yml
RUN conda env create

# From https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
RUN echo "source activate $(head -1 /app/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /app/environment.yml | cut -d' ' -f2)/bin:$PATH

RUN rm -rf /app/environment.yml

CMD bash