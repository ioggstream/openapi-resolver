import logging
from collections import defaultdict
from os import environ
from pathlib import Path

import pytest
import yaml
from openapi_resolver import OpenapiResolver

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

# To integrate with circle.ci we check the existence of
# the CIRCLECI repo url https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables.
REPO_URL = "https://raw.githubusercontent.com/{username}/{project}/{branch}/tests/data".format(
    username=environ.get("CIRCLE_PROJECT_USERNAME", "ioggstream"),
    project=environ.get("CIRCLE_PROJECT_REPONAME", "openapi-resolver"),
    branch=environ.get("CIRCLE_BRANCH", "master"),
)


def yaml_load_file(fpath):
    with open(fpath) as fh:
        return yaml.safe_load(fh.read())


def yaml_dump(dict_):
    return yaml.dump(dict(dict_), default_flow_style=0)


@pytest.mark.skip
def test_resolve_file():
    oat = yaml.safe_load(Path("tests/data/simple.yaml").read_text())
    resolver = OpenapiResolver(oat)
    resolver.resolve()

    out = yaml.safe_load(resolver.dump())
    Path("data/simple.out.yaml").write_text(resolver.dump())
    assert "Problem" in out["components"]["schemas"]


def test_yaml_reference():
    resolver = OpenapiResolver({}, None)
    ref = resolver.get_yaml_reference(
        "data/headers/subheaders.yaml#/headers/Retry-After"
    )
    assert "description" in ref
    assert "schema" in ref


def test_resolve_subreference_fix7_1():
    fpath = Path("data/subreference.yaml")
    oat = yaml_load_file(str(fpath))
    resolver = OpenapiResolver(oat, str(fpath.resolve()))
    resolver.resolve()
    yaml_ = resolver.dump_yaml()
    components = defaultdict(dict, yaml_.pop("components"))
    log.debug(yaml_dump(components))
    assert components["schemas"]["TaxCode"]


def test_resolve_subreference_fix6_2():
    fpath = Path("data/subreference.yaml")
    oat = yaml_load_file(str(fpath))
    resolver = OpenapiResolver(oat, str(fpath.resolve()))
    resolver.resolve()
    yaml_ = resolver.dump_yaml()
    components = defaultdict(dict, yaml_.pop("components"))
    log.debug(yaml_dump(components))
    assert components["responses"]["429TooManyRequests"]
    assert components["schemas"]["Problem"]
    assert components["headers"]["Retry-After"]


def test_resolve_subreference_fix6_1():
    oat = {
        "components": {
            "headers": {
                "X-Foo": {"$ref": "data/headers/subheaders.yaml#/headers/Retry-After"}
            }
        }
    }
    resolver = OpenapiResolver(oat, None)
    resolver.resolve()
    yaml_ = resolver.dump_yaml()
    components = defaultdict(dict, yaml_.pop("components"))
    log.debug(yaml_dump(components))
    assert components["headers"]["Retry-After"]


def test_resolve_subreference_fix6():
    # preserve nested objects.
    fpath = Path("data/headers/subheaders.yaml")
    oat = yaml_load_file(str(fpath))
    resolver = OpenapiResolver(oat, str(fpath))
    resolver.resolve()
    yaml_ = resolver.dump_yaml()

    components = defaultdict(dict, yaml_.pop("components"))
    components[fpath.parent.name].update(yaml_)
    log.debug(yaml_dump(components))
    assert components["headers"]["headers"]


def test_resolve_local_3():
    # load files from different paths
    # and resolve relative references.
    fpath = Path("data/parameters/parameters.yaml")
    oat = yaml_load_file(str(fpath))
    resolver = OpenapiResolver(oat, str(fpath))
    resolver.resolve()
    yaml_ = resolver.dump_yaml()

    components = defaultdict(dict, yaml_.pop("components"))
    components[fpath.parent.name].update(yaml_)
    log.debug(yaml_dump(components))
    assert components["schemas"]["Person"]
    assert (
        components["schemas"]["Person"]["properties"]["given_name"]["$ref"]
        == "#/components/schemas/GivenName"
    )
    assert components["parameters"]["citizen"]["schema"]
    assert components["schemas"]["TaxCode"]
    assert components["schemas"]["GivenName"]


def test_resolve_local_2():
    # load files from different paths
    # and resolve relative references.
    fpath = Path("data/responses/responses.yaml")
    oat = yaml_load_file(str(fpath))
    resolver = OpenapiResolver(oat, str(fpath))
    resolver.resolve()
    yaml_ = resolver.dump_yaml()

    components = defaultdict(dict, yaml_.pop("components"))
    components[fpath.parent.name].update(yaml_)
    log.debug(yaml_dump(components))
    assert components["headers"]["Retry-After"]
    assert components["schemas"]["Problem"]


def test_resolve_local():
    with open("testcase.yaml") as fh:
        oat = yaml.safe_load(fh.read())
    resolver = OpenapiResolver(oat["test_resolve_local"])
    resolver.resolve()

    out = yaml.safe_load(resolver.dump())
    assert "Problem" in out["components"]["schemas"]


def test_resolve_relative_2():
    oat = {"citizen": {"$ref": REPO_URL + "/parameters/parameters.yaml#/citizen"}}
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert "schemas" in resolver.yaml_components
    assert "Person" in resolver.yaml_components["schemas"]
    log.debug(resolver.dump())


def test_resolve_relative():
    oat = {
        "429TooManyRequests": {
            "$ref": REPO_URL + "/responses/responses.yaml#/429TooManyRequests"
        }
    }
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert "schemas" in resolver.yaml_components
    assert "Problem" in resolver.yaml_components["schemas"]
    assert "headers" in resolver.yaml_components
    assert "Retry-After" in resolver.yaml_components["headers"]
    log.debug(resolver.dump())


def test_traverse():
    oat = {
        "a": 1,
        "list_of_refs": [{"$ref": REPO_URL + "/parameters/parameters.yaml#/sort"}],
        "object": {"$ref": REPO_URL + "/parameters/parameters.yaml#/sort"},
    }
    resolver = OpenapiResolver(oat)
    ret = resolver.resolve()
    assert ret == {
        "a": 1,
        "list_of_refs": [
            {
                "name": "sort",
                "in": "query",
                "description": "Sorting order",
                "schema": {"type": "string", "example": "+name"},
            }
        ],
        "object": {
            "name": "sort",
            "in": "query",
            "description": "Sorting order",
            "schema": {"type": "string", "example": "+name"},
        },
    }
    log.debug(resolver.dump())


def test_traverse_list():
    oat = [{"$ref": REPO_URL + "/parameters/parameters.yaml#/sort"}]
    resolver = OpenapiResolver(oat)
    ret = resolver.resolve()
    assert ret == [
        {
            "name": "sort",
            "in": "query",
            "description": "Sorting order",
            "schema": {"type": "string", "example": "+name"},
        }
    ]
    log.debug(resolver.dump())


def test_traverse_object():
    oas = {
        "components": {
            "parameters": {
                "limit": {"$ref": REPO_URL + "/parameters/parameters.yaml#/limit"},
                "sort": {"$ref": REPO_URL + "/parameters/parameters.yaml#/sort"},
            },
            "headers": {
                "X-RateLimit-Limit": {
                    "$ref": REPO_URL + "/headers/headers.yaml#/X-RateLimit-Limit"
                },
                "Retry-After": {
                    "$ref": REPO_URL + "/headers/headers.yaml#/Retry-After"
                },
            },
        }
    }
    resolver = OpenapiResolver(oas)
    ret = resolver.resolve()
    log.debug(resolver.dump())


def test_nested_reference():
    oat = {
        "400BadRequest": {"$ref": REPO_URL + "/responses/responses.yaml#/400BadRequest"}
    }
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert "schemas" in resolver.yaml_components
    assert "Problem" in resolver.yaml_components["schemas"]
    log.debug(resolver.dump())


def test_dump():
    oat = {
        "openapi": "3.0.1",
        "x-commons": {},
        "components": {
            "responses": {
                "400BadRequest": {
                    "$ref": REPO_URL + "/responses/responses.yaml#/400BadRequest"
                }
            }
        },
    }
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert "400BadRequest:" in resolver.dump()
    assert "x-commons" not in resolver.dump()


def test_dump_noanchor():
    oat = {
        "/organization_list": {
            "get": {
                "description": "List or search all datasets\n",
                "operationId": "listOrgs",
                "responses": {
                    "200": {"$ref": "#/components/responses/CkanResponse"},
                    "400": {"$ref": "#/components/responses/400BadRequest"},
                    "429": {"$ref": "#/components/responses/429TooManyRequests"},
                    "503": {"$ref": "#/components/responses/503ServiceUnavailable"},
                    "default": {"$ref": "#/components/responses/default"},
                },
                "summary": "List all groups within given parameters",
                "tags": ["public"],
            }
        },
        "/package_list": {
            "get": {
                "description": "List or search all datasets\n",
                "operationId": "listInventory",
                "responses": {
                    "200": {"$ref": "#/components/responses/CkanResponse"},
                    "400": {"$ref": "#/components/responses/400BadRequest"},
                    "429": {"$ref": "#/components/responses/429TooManyRequests"},
                    "503": {"$ref": "#/components/responses/503ServiceUnavailable"},
                    "default": {"$ref": "#/components/responses/default"},
                },
                "summary": "List all datasets within given limit",
                "tags": ["public"],
            }
        },
        "/package_search": {
            "get": {
                "description": "List or search all datasets\n",
                "operationId": "searchInventory",
                "responses": {
                    "200": {"$ref": "#/components/responses/CkanResponse"},
                    "400": {"$ref": "#/components/responses/400BadRequest"},
                    "409": {
                        "description": "Conflict (can result e.g. from incorrectly formatted solr query)"
                    },
                    "429": {"$ref": "#/components/responses/429TooManyRequests"},
                    "503": {"$ref": "#/components/responses/503ServiceUnavailable"},
                    "default": {"$ref": "#/components/responses/default"},
                },
                "summary": "Search among all datasets",
                "tags": ["public"],
            }
        },
        "/package_show": {
            "get": {
                "description": "List or search all datasets\n",
                "operationId": "showInventory",
                "responses": {
                    "200": {"$ref": "#/components/responses/CkanResponse"},
                    "400": {"$ref": "#/components/responses/400BadRequest"},
                    "429": {"$ref": "#/components/responses/429TooManyRequests"},
                    "503": {"$ref": "#/components/responses/503ServiceUnavailable"},
                    "default": {"$ref": "#/components/responses/default"},
                },
                "summary": "Get details of one package",
                "tags": ["public"],
            }
        },
        "/user_list": {
            "get": {
                "description": "List or search all datasets\n",
                "operationId": "listUsers",
                "responses": {
                    200: {"$ref": "#/components/responses/CkanResponse"},
                    "400": {"$ref": "#/components/responses/400BadRequest"},
                    "429": {"$ref": "#/components/responses/429TooManyRequests"},
                    "503": {"$ref": "#/components/responses/503ServiceUnavailable"},
                    "default": {"$ref": "#/components/responses/default"},
                },
                "summary": "List all groups within given parameters",
                "tags": ["consumers"],
            }
        },
    }

    resolver = OpenapiResolver(oat)
    resolver.resolve()
    log.debug(resolver.dump())
    assert "*id" not in resolver.dump()
