#!/bin/bash
yarn install
yarn build
export ZESJE_SETTINGS=$(pwd)/zesje.prod.cfg
exec /root/miniconda3/bin/python zesje
