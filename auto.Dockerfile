# A Dockerfile containing everything to run Zesje automatically

FROM continuumio/miniconda3

RUN apt-get update -y && apt-get install -y libdmtx0b nginx

RUN echo "server { listen 80; location / { proxy_pass http://127.0.0.1:8881; } }" > /etc/nginx/sites-enabled/proxy.conf
RUN rm /etc/nginx/sites-enabled/default

WORKDIR /app

COPY . /app

RUN conda env create -n zesje-dev

# From https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
RUN echo "source activate zesje-dev" > ~/.bashrc
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

RUN yarn install

CMD service nginx restart && yarn migrate:dev && yarn dev
