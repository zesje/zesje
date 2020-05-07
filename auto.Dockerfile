# A Dockerfile containing everything to run Zesje automatically

FROM continuumio/miniconda3

RUN apt-get update -y && apt-get install -y libdmtx0b nginx sudo

RUN echo "server { listen 80; location / { proxy_pass http://127.0.0.1:5000; } }" > /etc/nginx/sites-enabled/proxy.conf
RUN rm /etc/nginx/sites-enabled/default

RUN groupadd -r zesje && useradd --no-log-init -r -g zesje zesje
RUN echo 'zesje ALL= NOPASSWD: /usr/sbin/service nginx restart,/bin/chown -R zesje\:zesje /app/data-dev' | sudo EDITOR='tee -a' visudo

WORKDIR /app
COPY . /app

RUN conda env create -n zesje-dev
ENV PATH /opt/conda/envs/zesje-dev/bin:$PATH

RUN yarn install
RUN yarn build

USER zesje
VOLUME /app/data-dev
EXPOSE 80

CMD sudo service nginx restart && \
    sudo chown -R zesje:zesje /app/data-dev && \
    yarn dev:mysql-init && yarn dev:backend
