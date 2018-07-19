FROM archlinux/base

RUN pacman -Sy --noconfirm python-conda

WORKDIR ~
ADD environment.yml .
ADD package.json .
RUN conda env create && \
    conda activate zesje-dev && \
    yarn install && \
    yarn cache clean \

CMD bash
