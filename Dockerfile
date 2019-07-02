FROM python:3-alpine 

LABEL maintainer="Valentino Lauciani <valentino.lauciani@ingv.it>"

ENV DEBIAN_FRONTEND=noninteractive
ENV INITRD No
ENV FAKE_CHROOT 1

# install packages
RUN pip install --user openapi_resolver 

# Run python module
ENTRYPOINT ["python", "-m", "openapi_resolver"]
