import argparse
import os

from . import Project

def run(path):

    project = Project(path)

    def deploy(args):
        project.deploy()


    def destroy(args):
        project.destroy()


    def refresh(args):
        project.refresh_state()


    parser = argparse.ArgumentParser(description="Deploy fly.io apps")

    parser.set_defaults()

    parser.add_argument('--token', type=str)


    subparsers = parser.add_subparsers()

    deploy_parser = subparsers.add_parser('deploy')

    destroy_parser = subparsers.add_parser('destroy')

    refresh_parser = subparsers.add_parser('refresh')


    destroy_parser.set_defaults(func=destroy)

    deploy_parser.set_defaults(func=deploy)

    refresh_parser.set_defaults(func=refresh)


    args = parser.parse_args()

    if args.token:
        os.environ['FLY_ACCESS_TOKEN'] = args.token

    if hasattr(args, 'func'):
        args.func(args)

    else:
        parser.print_help()
