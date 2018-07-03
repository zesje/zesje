FROM base/archlinux

RUN pacman -Sy --noconfirm nodejs python-pip git libdmtx libsm libxrender libxext gcc libmagick6 imagemagick; \
pacman -U --noconfirm https://archive.archlinux.org/packages/y/yarn/yarn-1.6.0-1-any.pkg.tar.xz

ADD requirements*.txt ./
ADD package.json .
RUN pip install -r requirements.txt -r requirements-dev.txt
RUN yarn install

EXPOSE 8881
CMD yarn dev