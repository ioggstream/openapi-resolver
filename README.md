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

	python -m openapi_resolver --help

To create an openapi bundle from a spec file just run

	python -m openapi_resolver sample.yaml

You can use this module to normalize two specs before diffing, eg:

	python -m openapi_resolver one.yaml > normal-one.yaml
	python -m openapi_resolver two.yaml > normal-two.yaml
        diff normal-one.yaml normal-two.yaml
