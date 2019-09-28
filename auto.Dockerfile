# A Dockerfile containing everything to run Zesje automatically

FROM continuumio/miniconda3

RUN apt-get update -y && apt-get install -y libdmtx0b nginx sudo

RUN echo "server { listen 80; location / { proxy_pass http://127.0.0.1:5000; } }" > /etc/nginx/sites-enabled/proxy.conf
RUN rm /etc/nginx/sites-enabled/default

RUN groupadd -r zesje && useradd --no-log-init -r -d /app -g zesje zesje
RUN echo 'zesje ALL= NOPASSWD: /usr/sbin/service nginx restart,/bin/chown -R zesje\:zesje /app/data-dev' | sudo EDITOR='tee -a' visudo
RUN chown -R zesje:zesje /opt/conda
RUN mkdir -p /app && chown -R zesje:zesje /app

USER zesje

WORKDIR /app
COPY --chown=zesje:zesje . /app

RUN conda env create -n zesje-dev

# From https://medium.com/@chadlagore/conda-environments-with-docker-82cdc9d25754
RUN echo "source activate zesje-dev" > ~/.bashrc
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

RUN yarn install
RUN yarn build

VOLUME /app/data-dev
EXPOSE 80

CMD sudo service nginx restart && \
    sudo chown -R zesje:zesje /app/data-dev && \
    yarn migrate:dev && yarn dev:backend
