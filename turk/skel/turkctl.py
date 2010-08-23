#!/usr/bin/env python
from turk.turkctl import main
from os.path import join, abspath, dirname, exists

if __name__ == "__main__":
    project_dir = abspath(dirname(__file__))

    # Use [project directory]/turk.yaml as the default config file.
    # This can be overridden on the command line.
    config_file = join(project_dir, 'turk.yaml')

    main(config_file)

