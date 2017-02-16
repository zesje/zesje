FROM debian:jessie

RUN apt-get update && apt-get install -y curl libzbar-dev imagemagick poppler-utils build-essential && curl https://deb.nodesource.com/setup_6.x | bash && apt-get install nodejs && curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh && bash miniconda.sh -b && rm miniconda.sh
RUN /root/miniconda3/bin/conda config --system --add channels conda-forge && /root/miniconda3/bin/conda install -y pony opencv pillow ipywidgets notebook jupyter_kernel_gateway pyyaml pandas -c conda-forge
RUN npm install jupyter-dashboards-server
RUN apt-get -y --quiet install supervisor

COPY grade.ipynb validate_nr.ipynb /dashboards/
COPY db.py number_widget.svg /grader_app/
COPY supervisord.conf /etc/supervisor/

EXPOSE 3000
ENTRYPOINT ["/usr/bin/supervisord"]

# jupyter kernelgateway&
# /root/node_modules/jupyter-dashboards-server/bin/jupyter-dashboards-server --IP 0.0.0.0 --KERNEL_GATEWAY_URL http://127.0.0.1:8888
