"""This script resolves references in a yaml file and dumps it
    removing all of them.

    It expects references are defined in `x-commons` object.
    This object will be removed before serialization.
"""
from __future__ import print_function
from pathlib import Path
import yaml
from six.moves.urllib.parse import urldefrag, urljoin
from six.moves.urllib.request import urlopen
import logging
from collections import defaultdict
from os.path import join, basename, normpath, abspath

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()


ROOT_NODE = object()
COMPONENTS_MAP = {
    "schema": "schemas",
    "headers": "headers",
    "parameters": "parameters",
    "responses": "responses",
}


def deepcopy(item):
    return yaml.safe_load(yaml.safe_dump(item))


def finddict(_dict, keys):
    # log.debug(f"search {keys} in {_dict}")
    p = _dict
    for k in keys:
        p = p[k]
    return p


def should_use_block(value):
    for c in u"\u000a\u000d\u001c\u001d\u001e\u0085\u2028\u2029":
        if c in value:
            return True
    return False


def my_represent_scalar(self, tag, value, style=None):
    if should_use_block(value):
        style = "|"
    else:
        style = self.default_style

    node = yaml.representer.ScalarNode(tag, value, style=style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    return node


def open_file_or_url(host):
    if host.startswith("http"):
        return urlopen(host).read()
    host = normpath(abspath(host))
    with open(host) as fh:
        return fh.read()


class NoAnchorDumper(yaml.dumper.SafeDumper):
    """A yaml Dumper that does not replace duplicate entries
       with yaml anchors.
    """

    def ignore_aliases(self, *args):
        return True


def fragment_to_keys(fragment):
    """Split a fragment, eg. #/components/headers/Foo
        in a list of keys ("components", "headers", "Foo")
    """
    return fragment.strip("#").strip("/").split("/")


class OpenapiResolver(object):
    """Resolves an OpenAPI v3 spec file replacing
       yaml-references and json-$ref from
       the web.
    """

    def __init__(self, openapi, context=None):
        self.openapi = deepcopy(openapi)
        # Global variables used by the parser.
        self.context = context
        self.is_subschema = False
        self.yaml_cache = {}
        self.yaml_components = defaultdict(dict)

    def resolve(self):
        self.traverse(self.openapi, cb=self.resolve_node)
        return self.openapi

    def check_traverse_and_set_context(self, key, node):
        """This method checks if we need to resolve a $ref.

        Decision is based on the node (eg. if it's a remote reference, starting with http),
        or if it's a local one.

        As both local and remote references can be relative to the given file, a
        self.context attribute is used to distinguish if the $ref is in the original
        file or in an external source.

        :param key:
        :param node:
        :return: True if I have to resolve the node.
        """
        if key != "$ref":
            return False, None

        if node.startswith("#/"):  # local reference
            try:
                is_local_ref = finddict(self.openapi, fragment_to_keys(node))
            except KeyError:
                is_local_ref = False

            # Don't resolve local references already in the spec.
            if is_local_ref:
                return False, None
            # Resolve local references in external files.
            if self.context:
                return True, None

            return False, None

        if node.startswith("http"):  # url reference
            host, fragment = urldefrag(node)
            return True, host

        if node.startswith("file://"):
            raise NotImplementedError

        host, fragment = urldefrag(node)
        if self.context:
            if self.context.startswith("http"):
                p = urljoin(self.context, host)
                # log.info(f"trying to set context {p}. Was {self.context}. host is: {host}.")
                return True, p

            p = Path(self.context).parent.joinpath(host)
            # log.info(f"trying to set context {p}. Was {self.context}. host is: {host}. resolved is {p.resolve()}")
            if p.is_file():
                return True, str(p.resolve())
            else:
                log.warning("can't set context %r. Retains %r", p, self.context)

        # Remote reference should use previous
        #  context. Better should be to track
        #  nodes with their context.
        return True, None

    def get_component_name(self, needle, parents):
        # We need to check both `needle` and `granny`
        # because $ref appears in `schema` and `headers`
        # at different nesting levels.
        needle_alias = None
        granny = parents[0] if isinstance(parents[0], str) else None
        if needle in COMPONENTS_MAP:
            needle_alias = COMPONENTS_MAP[needle]
        elif granny in COMPONENTS_MAP:
            needle_alias = COMPONENTS_MAP[granny]

        # $ref under `schemas` should be always treated
        #  as `schemas` and added to components.
        #  Reset is_subschema when needle_alias changes.
        if needle_alias == "schemas":
            self.is_subschema = True
        elif needle_alias is not None:
            self.is_subschema = False

        return "schemas" if self.is_subschema else needle_alias

    def traverse(self, node, key=ROOT_NODE, parents=None, cb=print, context=None):
        """ Recursively call nested elements."""

        # Trim parents breadcrumb as 4 will suffice.
        parents = parents[-4:] if parents else []

        # Unwind items as a dict or an enumerated list
        # to simplify traversal.
        if isinstance(node, (dict, list)):
            valuelist = node.items() if isinstance(node, dict) else enumerate(node)
            if key is not ROOT_NODE:
                parents.append(key)
            parents.append(node)
            for k, i in valuelist:
                self.traverse(i, k, parents, cb, context)
            return

        # Resolve HTTP references adding fragments
        # to 'schema', 'headers' or 'parameters'
        do_traverse, new_context = self.check_traverse_and_set_context(key, node)
        # If the context changes, update the global pointer too.
        # TODO: we would eventually get rid of self.context completely.
        if new_context:
            self.context = new_context
            context = new_context
        # log.info(f"test node context {key}, {node}, {do_traverse}")
        log.debug("test node context %r, %r, %r", key, node, do_traverse)
        if do_traverse:
            ancestor, needle = parents[-3:-1]
            # log.info(f"replacing: {needle} in {ancestor} with ref {node}. Parents are {parents}")
            ancestor[needle] = cb(key, node, context)

            # Get the component where to store the given item.
            component_name = self.get_component_name(needle, parents)

            # Use a pre and post traversal functions.
            # - before: append the reference to yaml_components.
            # - traverse
            # - after: deepcopy the resulting item in the yaml_components
            #          then replace it with the reference in the specs
            if component_name:
                # log.info(f"needle {needle} in components_map.")
                host, fragment = urldefrag(node)
                fragment = basename(fragment.strip("/"))
                self.yaml_components[component_name][fragment] = ancestor[needle]

            if isinstance(ancestor[needle], (dict, list)):
                self.traverse(ancestor[needle], key, parents, cb, context)

            if component_name:
                # Now the node is fully resolved. I can replace it with the
                # Deepcopy
                self.yaml_components[component_name][fragment] = deepcopy(
                    ancestor[needle]
                )
                ancestor[needle] = {
                    "$ref": "#" + join("/components", component_name, fragment)
                }

    def get_yaml_reference(self, f):
        # log.info(f"Downloading {f}")
        host, fragment = urldefrag(f)
        if host not in self.yaml_cache:
            self.yaml_cache[host] = open_file_or_url(host)

        f_yaml = yaml.safe_load(self.yaml_cache[host])
        if fragment.strip("/"):
            f_yaml = finddict(f_yaml, fragment_to_keys(fragment))
        return f_yaml

    def resolve_node(self, key, node, context):
        """This is the callback.
        """
        # log.info(f"Resolving {node}, {context}")
        n = node
        if not node.startswith("http"):
            # Check if self.context already points to node
            host, fragment = urldefrag(n)

            if context and context.endswith(host):
                n = urljoin(context, "#" + fragment)
            else:
                n = urljoin(context, node)
        _yaml = self.get_yaml_reference(n)
        return _yaml

    def dump(self, remove_tags=("x-commons",)):
        """Dump the OpenAPI spec removing yaml anchors.

           Anchor removal is done via NoAnchorDumper.
        """
        openapi_tags = ("openapi", "info", "servers", "tags", "paths", "components")

        # Dump long lines as "|".
        yaml.representer.SafeRepresenter.represent_scalar = my_represent_scalar

        openapi = deepcopy(self.openapi)

        # If it's not a dict, just dump the standard yaml
        if not isinstance(openapi, dict):
            return yaml.dump(
                openapi,
                default_flow_style=False,
                allow_unicode=True,
                Dumper=NoAnchorDumper,
            )

        # Eventually remove some tags, eg. containing references and aliases.
        for tag in remove_tags:
            if tag in openapi:
                del openapi[tag]

        # Add resolved schemas.
        # XXX: check if the schema hash is the same in case
        #      of multiple entries.
        components = openapi.setdefault("components", {})
        for k, items in self.yaml_components.items():
            if k not in components:
                components[k] = {}

            components[k].update(items)

        # Order yaml keys for a nice
        # dumping.
        yaml_keys = set(openapi.keys())
        first_keys = [x for x in openapi_tags if x in yaml_keys]
        remaining_keys = list(yaml_keys - set(first_keys))
        sorted_keys = first_keys + remaining_keys

        content = ""
        for k in sorted_keys:
            content += yaml.dump(
                {k: openapi[k]},
                default_flow_style=False,
                allow_unicode=True,
                Dumper=NoAnchorDumper,
            )

        return content

    def dump_yaml(self, *args, **kwargs):
        return yaml.safe_load(self.dump(*args, **kwargs))

    @staticmethod
    def yaml_dump_pretty(openapi):
        # Dump long lines as "|".
        yaml.representer.SafeRepresenter.represent_scalar = my_represent_scalar
        return yaml.dump(
            openapi, default_flow_style=False, allow_unicode=True, Dumper=NoAnchorDumper
        )
