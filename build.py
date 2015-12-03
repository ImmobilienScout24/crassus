#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from pybuilder.core import init, task, use_plugin
from pybuilder.vcs import VCSRevision

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("pypi:pybuilder_aws_plugin")
use_plugin("python.coverage")

name = 'crassus'
summary = 'AWS lambda function for deployment automation'
description = """
    AWS lambda function for deployment automation, which makes use of
    sns/sqs for trigger and backchannel."""
license = 'Apache License 2.0'
url = 'https://github.com/ImmobilienScout24/crassus'
version = VCSRevision().get_git_revision_count()

default_task = ['clean', 'analyze', 'package']


@init
def set_properties(project):
    project.depends_on("boto3")
    project.build_depends_on("moto")
    project.build_depends_on("unittest2")
    project.build_depends_on("mock")
    project.build_depends_on("cfn-sphere")
    project.set_property('coverage_break_build', False)
    project.set_property(
        'bucket_name', os.environ.get('BUCKET_NAME_FOR_UPLOAD'))
    project.set_property(
        'lambda_file_access_control',
        os.environ.get('LAMBDA_FILE_ACCESS_CONTROL'))

    project.set_property('template_files', [
        ('cfn-sphere/templates', 'crassus.yaml'),
        ('cfn-sphere/templates', 'crassus_integration_test_role.yaml'),
    ])
    project.set_property(
        'template_file_access_control',
        os.environ.get('LAMBDA_FILE_ACCESS_CONTROL'))

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
    project.set_property('teamcity_output', True)
    project.set_property('teamcity_parameter', 'crassus_filename')

    # project.version = '%s-%s' % (project.version,
    #                              os.environ.get('BUILD_NUMBER', 0))
    project.default_task = [
        'clean',
        'install_build_dependencies',
        'publish',
        'package_lambda_code',
        'upload_zip_to_s3',
        'upload_cfn_to_s3',
    ]
    project.set_property('install_dependencies_index_url',
                         os.environ.get('PYPIPROXY_URL'))


@init(environments='backchannel_temp')
def set_properties_for_backchannel_builds(project):
    # For upload_zip_to_s3
    project.set_property('bucket_prefix', 'backchannel_')
    # For upload_cfn_to_s3
    project.set_property('template_key_prefix', 'backchannel_')
    project.set_property('template_files', [
        ('cfn-sphere/templates', 'crassus.yaml'),
    ])

    project.version = '%s-%s' % (
        project.version, os.environ.get('BUILD_NUMBER', 0))
    project.set_property('bucket_name', 'crassus-lambda-zips')
    project.set_property('lambda_file_access_control', 'public-read')
    project.default_task = [
        'clean',
        'install_build_dependencies',
        'publish',
        'package_lambda_code',
        'upload_zip_to_s3',
        'upload_cfn_to_s3',
    ]
    project.set_property('install_dependencies_index_url',
                         os.environ.get('PYPIPROXY_URL'))


@init(environments='integration_env')
def set_properties_for_teamcity_integration_test(project):
    use_plugin("python.integrationtest")
    project.set_property('integrationtest_inherit_environment', True)
