# Image containing castep-lint at the version in this repository
#
# Lint files in the current directory with, eg:
#   docker run --rm -v "$PWD:/src" ghcr.io/byornski/castep-linter file.f90

# Build the package from source
FROM python:3.14-slim AS build

RUN pip install --no-cache-dir hatch

COPY . /src
WORKDIR /src
RUN hatch build -t wheel /dist

# Install it into a clean image
FROM python:3.14-slim

LABEL org.opencontainers.image.source="https://github.com/byornski/castep-linter"
LABEL org.opencontainers.image.description="Linter which checks CASTEP's Fortran source code against its coding conventions"
LABEL org.opencontainers.image.licenses="MIT"

COPY --from=build /dist /tmp/dist
RUN pip install --no-cache-dir /tmp/dist/*.whl && rm -r /tmp/dist

# Code to lint is mounted here
WORKDIR /src
ENTRYPOINT ["castep-lint"]
CMD ["--help"]
