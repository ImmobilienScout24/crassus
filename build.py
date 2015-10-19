from pybuilder.core import use_plugin, init, task

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
#use_plugin("python.coverage")

name = "crassus"
default_task = "publish"
version = 0.1


@init
def set_properties(project):
    project.depends_on("boto3")
    project.depends_on("unittest2")
    project.build_depends_on("mock")
    #project.set_property('coverage_break_build', False)

    project.set_property('distutils_classifiers', [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration'
    ])


@init(environments='teamcity')
def set_properties_for_teamcity_builds(project):
    import os
    project.set_property('teamcity_output', True)
    project.version = '%s-%s' % (project.version,
                                 os.environ.get('BUILD_NUMBER', 0))
    project.default_task = [
        'clean',
        'install_build_dependencies',
        'publish',
        'package_lambda_code'
    ]
    project.set_property('install_dependencies_index_url',
                         os.environ.get('PYPIPROXY_URL'))


@task
def package_lambda_code():
    print "HELLO WORLD!"
