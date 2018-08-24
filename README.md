# OpenAPI Resolver

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
