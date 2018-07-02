#!/bin/bash

demo_dir="$(dirname ${BASH_SOURCE[0]})"

rm -rf "${demo_dir}/../data-dev"
cp -a "${demo_dir}/data-dev" "${demo_dir}/.."

