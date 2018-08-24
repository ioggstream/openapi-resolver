from openapi_resolver import *

def test_traverse():
    oat = {
        'a': 1,
        'list_of_refs': [
            {'$ref': 'https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort'}
        ],
        'object': {'$ref': 'https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort'}
    }
    resolver = OpenapiResolver(oat)
    ret = resolver.resolve()
    assert(ret == {'a': 1, 'list_of_refs': [{'name': 'sort', 'in': 'query', 'description': 'Sorting order', 'schema': {
           'type': 'string', 'example': '+name'}}], 'object': {'name': 'sort', 'in': 'query', 'description': 'Sorting order', 'schema': {'type': 'string', 'example': '+name'}}})
    print(resolver.dump())


def test_traverse_list():
    oat = [
        {'$ref': 'https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort'}
    ]
    resolver = OpenapiResolver(oat)
    ret = resolver.resolve()
    assert(ret == [{'name': 'sort', 'in': 'query', 'description': 'Sorting order', 'schema': {
           'type': 'string', 'example': '+name'}}])
    print(resolver.dump())


def test_traverse_object():
    oas = {'components': {'parameters': {'limit': {'$ref': 'https://teamdigitale.github.io/openapi/parameters/v3.yaml#/limit'},
                                         'sort': {'$ref': 'https://teamdigitale.github.io/openapi/parameters/v3.yaml#/sort'}},
                          'headers': {'X-RateLimit-Limit': {'$ref': 'https://teamdigitale.github.io/openapi/headers/v3.yaml#/X-RateLimit-Limit'},
                                      'Retry-After': {'$ref': 'https://teamdigitale.github.io/openapi/headers/v3.yaml#/Retry-After'}},
                          }}
    resolver = OpenapiResolver(oas)
    ret = resolver.resolve()
    print(resolver.dump())


def test_nested_reference():
    oat = {'400BadRequest': {
        '$ref': 'https://teamdigitale.github.io/openapi/responses/v3.yaml#/400BadRequest'}}
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert 'schemas' in resolver.yaml_components
    assert 'Problem' in resolver.yaml_components['schemas']
    print(resolver.dump())


def test_dump():
    oat = {
        'openapi': '3.0.1',
        'x-commons': {},
        'components': {
            'responses': {
                '400BadRequest': {
                    '$ref': 'https://teamdigitale.github.io/openapi/responses/v3.yaml#/400BadRequest'
                }
            }
        }
            
    }
    resolver = OpenapiResolver(oat)
    resolver.resolve()
    assert '400BadRequest:' in resolver.dump()
    assert 'x-commons' not in resolver.dump()


