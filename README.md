# OpenAPI Resolver

[![CircleCI](https://circleci.com/gh/ioggstream/openapi-resolver.svg?style=svg)](https://circleci.com/gh/ioggstream/openapi-resolver)

This module recursively parses openapi specs resolving references.

## Test

Tests run locally via 

        tox

Or via [circleci-local](https://circleci.com/docs/2.0/local-cli/)

        circleci build 


## Usage

The module has an embedded script that can be run via

        $ python -m openapi_resolver --help

        usage: __main__.py [-h] src_file [dst_file]

        Recursively resolves and bundles OpenAPI v3 files.

        positional arguments:
          src_file    An OpenAPI v3 yaml file.
          dst_file    Destination file, default is stdout.

        optional arguments:
          -h, --help  show this help message and exit

To create an openapi bundle from a spec file just run

        $ python -m openapi_resolver sample.yaml

You can use this module to normalize two specs before diffing, eg:

        $ python -m openapi_resolver one.yaml normal-one.yaml
        $ python -m openapi_resolver two.yaml normal-two.yaml
        $ diff normal-one.yaml normal-two.yaml
