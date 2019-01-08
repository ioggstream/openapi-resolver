from openapi_resolver import OpenapiResolver
import yaml
from nose import SkipTest
from pathlib import Path
import logging
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()


def yaml_load_file(fpath):
    with open(fpath) as fh:
        return yaml.load(fh.read())


def yaml_dump(dict_):
    return yaml.dump(dict(dict_), default_flow_style=0)


@SkipTest
def test_resolve_file():
    oat = yaml.load(Path("tests/data/simple.yaml").read_text())
    resolver = OpenapiResolver(oat)
    resolver.resolve()

    out = yaml.load(resolver.dump())
    Path("data/simple.out.yaml").write_text(resolver.dump())
    assert "Problem" in out["components"]["schemas"]


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
    yaml_dump(components)
    assert components["schemas"]["Person"]
    assert components["parameters"]["citizen"]["schema"]
    assert components["schemas"]["TaxCode"]


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
    yaml_dump(components)
    assert components["headers"]["Retry-After"]
    assert components["schemas"]["Problem"]


def test_resolve_local():
    with open("testcase.yaml") as fh:
        oat = yaml.load(fh.read())
    resolver = OpenapiResolver(oat["test_resolve_local"])
    resolver.resolve()

    out = yaml.load(resolver.dump())
    assert "Problem" in out["components"]["schemas"]


def test_resolve_relative_2():
    oat = {
        "citizen": {
            "$ref": "https://raw.githubusercontent.com/teamdigitale/openapi/1-reorganize-repo/docs/parameters/v3.yaml#/citizen"
        }
    }
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert "schemas" in resolver.yaml_components
    assert "Person" in resolver.yaml_components["schemas"]
    log.debug(resolver.dump())


def test_resolve_relative():
    oat = {
        "429TooManyRequests": {
            "$ref": "https://raw.githubusercontent.com/teamdigitale/openapi/1-reorganize-repo/docs/responses/v3.yaml#/429TooManyRequests"
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
        "list_of_refs": [
            {"$ref": "https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort"}
        ],
        "object": {
            "$ref": "https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort"
        },
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
    oat = [{"$ref": "https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort"}]
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
                "limit": {
                    "$ref": "https://teamdigitale.github.io/openapi/parameters/v3.yaml#/limit"
                },
                "sort": {
                    "$ref": "https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort"
                },
            },
            "headers": {
                "X-RateLimit-Limit": {
                    "$ref": "https://teamdigitale.github.io/openapi/headers/v3.yaml#/X-RateLimit-Limit"
                },
                "Retry-After": {
                    "$ref": "https://teamdigitale.github.io/openapi/headers/v3.yaml#/Retry-After"
                },
            },
        }
    }
    resolver = OpenapiResolver(oas)
    ret = resolver.resolve()
    log.debug(resolver.dump())


def test_nested_reference():
    oat = {
        "400BadRequest": {
            "$ref": "https://teamdigitale.github.io/openapi/responses/v3.yaml#/400BadRequest"
        }
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
                    "$ref": "https://teamdigitale.github.io/openapi/responses/v3.yaml#/400BadRequest"
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
