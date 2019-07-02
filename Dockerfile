FROM python:3-alpine 

LABEL maintainer="Valentino Lauciani <valentino.lauciani@ingv.it>"

ENV DEBIAN_FRONTEND=noninteractive
ENV INITRD No
ENV FAKE_CHROOT 1

ADD . /openapi-resolver
RUN pip install --user /openapi-resolver

# External volume to use for mounting openapi specs
#  and as default workdir.
VOLUME /code
WORKDIR /code

ENTRYPOINT ["python", "-m", "openapi_resolver"]
