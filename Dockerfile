FROM debian:jessie

RUN apt-get update && \
    apt-get install -y \
    curl libzbar-dev imagemagick poppler-utils build-essential libgl1-mesa-glx && \
    apt-get -y --quiet install supervisor && \
    curl https://deb.nodesource.com/setup_6.x | bash && \
    apt-get install nodejs && \
    curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh && \
    bash miniconda.sh -b && \
    rm miniconda.sh

RUN /root/miniconda3/bin/conda config --system --add channels conda-forge && \
    /root/miniconda3/bin/conda install -y -c conda-forge \
    # our widgets depend on this
    ipywidgets==5.2.2 \
    widgetsnbextension==1.2.6\
    # avoid openpyxl regression
    "openpyxl!=2.5.0b1"\
    pony opencv pillow notebook jupyter_kernel_gateway pyyaml pandas seaborn openblas
RUN /root/miniconda3/bin/pip install zbar-py && \
    /root/miniconda3/bin/pip install "nbconvert>=5.2" # (not yet on conda)
RUN npm install jupyter-dashboards-server
RUN sed -i'' "s/body {/body { min-height: 100vh;/" /node_modules/jupyter-dashboards-server/public/css/style.css

EXPOSE 3000
VOLUME ["/app", "/dashboards"]  # also /etc/supervisor/supervisord.conf
ENTRYPOINT ["/usr/bin/supervisord"]
