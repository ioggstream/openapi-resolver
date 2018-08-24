from sys import argv
import yaml
from . import OpenapiResolver
import argparse



def main(src_file, dst_file):

    with open(src_file) as fh_src, open(dst_file, 'w') as fh_dst:
        ret = yaml.safe_load(fh_src)

        # Resolve nodes.
        # TODO: this behavior could be customized eg.
        #  to strip some kind of nodes.
        resolver = OpenapiResolver(ret)
        resolver.resolve()

        # Serialize file.
        fh_dst.write(resolver.dump())


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Recursively resolves and bundles OpenAPI v3 files.')
    parser.add_argument('src_file', type=str, 
                        help='An OpenAPI v3 yaml file.')
    parser.add_argument('dst_file', type=str, default='/dev/stdout', nargs='?',
                        help='Destination file, default is stdout.')
    args = parser.parse_args()

    main(args.src_file, args.dst_file)

