FROM archlinux/base

## Install packages and clear the cache after installation. Yarn is fixed at 1.6.0 untill 1.8.0 is released due to a critical bug.
RUN pacman -Sy --noconfirm nodejs python-pip git libdmtx libsm libxrender libxext gcc libmagick6 imagemagick; \
    pacman -U --noconfirm https://archive.archlinux.org/packages/y/yarn/yarn-1.6.0-1-any.pkg.tar.xz

WORKDIR ~
ADD requirements*.txt ./
ADD package.json .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt; \
    rm requirements*.txt
RUN yarn install; \
    yarn cache clean; \
    rm package.json

CMD bash