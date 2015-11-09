import unittest
from textwrap import dedent

import boto3
from mock import Mock, patch, ANY
from botocore.exceptions import ClientError
from moto import mock_sns

from crassus.deployer import (
    parse_event, load_stack, update_stack, deploy_stack, notify,
    NOTIFICATION_SUBJECT, StackUpdateParameter, init_output_sns_topic,
    ResultMessage,)

PARAMETER = 'ANY_PARAMETER'
ARN_ID = 'ANY_ARN'
STACK_NAME = 'ANY_STACK'

CRASSUS_CFN_PARAMETERS = [
    {
        "updateParameterKey": "ANY_NAME1",
        "updateParameterValue": "ANY_VALUE1"
    },
    {
        "updateParameterKey": "ANY_NAME2",
        "updateParameterValue": "ANY_VALUE2"
    }
]

SAMPLE_EVENT = {
    'Records': [
        {
            'EventVersion': '1.0',
            'EventSubscriptionArn': '<SUBSCRIPTION ARN>',
            'EventSource': 'aws: sns',
            'Sns': {
                'SignatureVersion': '1',
                'Timestamp': '2015-10-23T11: 01: 16.140Z',
                'Signature': '<SIGNATURE>',
                'SigningCertUrl': '<SIGNING URL>',
                'MessageId': '<MESSAGE ID>',
                'Message': '{"version": "1", "stackName": "ANY_STACK","region": "eu-west-1","parameters": [{"updateParameterKey": "ANY_NAME1", "updateParameterValue": "ANY_VALUE1"}, {"updateParameterKey": "ANY_NAME2", "updateParameterValue": "ANY_VALUE2"}]}',
                'MessageAttributes': {
                },
                'Type': 'Notification',
                'UnsubscribeUrl': '<UNSUBSCRIBE URL>',
                'TopicArn': '<TOPIC ARN>',
                'Subject': None
            }
        }
    ]
}


class TestDeployStack(unittest.TestCase):

    @patch('crassus.deployer.init_output_sns_topic')
    @patch('crassus.deployer.parse_event')
    @patch('crassus.deployer.load_stack')
    @patch('crassus.deployer.update_stack')
    def test_should_call_all_necessary_stuff(
            self, update_stack_mock, load_stack_mock, parse_event_mock,
            init_mock):
        stack_update_parameter_mock = Mock()
        stack_update_parameter_mock.stack_name = STACK_NAME
        stack_update_parameter_mock.parameters = PARAMETER
        parse_event_mock.return_value = stack_update_parameter_mock
        load_stack_mock.return_value = 'ANY_STACK_ID'

        deploy_stack(SAMPLE_EVENT, None)

        parse_event_mock.assert_called_once_with(SAMPLE_EVENT)
        load_stack_mock.assert_called_once_with(STACK_NAME)
        update_stack_mock.assert_called_once_with('ANY_STACK_ID',
                                                  stack_update_parameter_mock)


class TestParseParameters(unittest.TestCase):

    def test_parse_valid_event(self):
        stack_update_parameters = parse_event(SAMPLE_EVENT)

        self.assertEqual(stack_update_parameters.stack_name, 'ANY_STACK')


class TestNotify(unittest.TestCase):
    STATUS = 'success'
    MESSAGE = 'ANY MESSAGE'

    @patch('crassus.deployer.output_sns_topics', ['ANY_ARN'])
    @patch('boto3.resource')
    def test_should_notify_sns(self, resource_mock):
        topic_mock = Mock()
        sns_mock = Mock()
        sns_mock.Topic.return_value = topic_mock
        resource_mock.return_value = sns_mock

        notify(self.STATUS, self.MESSAGE)

        topic_mock.publish.assert_called_once_with(
            Message=('{"status": "success", '
                     '"message": "ANY MESSAGE", '
                     '"version": "1.0"}'),
            Subject=NOTIFICATION_SUBJECT,
            MessageStructure='string')

    @patch('crassus.deployer.output_sns_topics', None)
    def test_should_do_gracefully_nothing(self):
        notify('status', 'message')

class TestUpdateStack(unittest.TestCase):

    def setUp(self):
        self.stack_mock = Mock()
        self.stack_mock.parameters = [
            {"ParameterKey": "KeyOne",
             "ParameterValue": "OriginalValueOne",
             },
            {"ParameterKey": "KeyTwo",
             "ParameterValue": "OriginalValueTwo",
             }
        ]

        self.update_parameters = {
            "version": 1,
            "stackName": "ANY_STACK",
            "region": "ANY_REGION",
            "parameters":
                {"KeyOne": "UpdateValueOne"},
        }

        self.expected_parameters = [
            {"ParameterKey": "KeyOne",
             "ParameterValue": "UpdateValueOne",
             },
            {"ParameterKey": "KeyTwo",
             "UsePreviousValue": True
             }
        ]

    def test_update_stack_should_call_update(self):
        update_parameters = StackUpdateParameter(self.update_parameters)
        update_stack(self.stack_mock, update_parameters)

        self.stack_mock.update.assert_called_once_with(
            UsePreviousTemplate=True,
            Parameters=self.expected_parameters,
            Capabilities=['CAPABILITY_IAM'])

    @patch('crassus.deployer.logger')
    def test_update_stack_load_throws_clienterror_exception(self, logger_mock):
        update_parameters = StackUpdateParameter(self.update_parameters)
        self.stack_mock.update.side_effect = ClientError(
            {'Error': {'Code': 'ExpectedException', 'Message': ''}},
            'test_deploy_stack_should_notify_error_in_case_of_client_error')
        update_stack(self.stack_mock, update_parameters)
        logger_mock.error.assert_called_once_with(ANY)

    """@patch('crassus.deployer.notify')
    def test_update_stack_should_notify_in_case_of_error(self, notify_mock):
        self.stack_mock.update.side_effect = ClientError(
            {'Error': {'Code': 'ExpectedException', 'Message': ''}},
            'test_deploy_stack_should_notify_error_in_case_of_client_error')

        update_stack(self.stack_mock, self.update_parameters, 'ANY_ARN')

        notify_mock.assert_called_once_with(ANY, 'ANY_ARN')"""


class TestLoadStack(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.resource')
        self.resource_mock = self.patcher.start()

        self.cloudformation_mock = Mock()
        self.stack_mock = Mock()
        self.resource_mock.return_value = self.cloudformation_mock
        self.cloudformation_mock.Stack.return_value = self.stack_mock

    def tearDown(self):
        self.patcher.stop()

    def test_deploy_stack_should_load_stack(self):
        load_stack('ANY_STACK')
        self.stack_mock.load.assert_called_once_with()

    @patch('crassus.deployer.logger')
    def test_stack_load_throws_clienterror_exception(self, logger_mock):
        self.stack_mock.load.side_effect = ClientError(
            {'Error': {'Code': 'ExpectedException', 'Message': ''}},
            'test_deploy_stack_should_notify_error_in_case_of_client_error')
        load_stack('ANY_STACK')
        logger_mock.error.assert_called_once_with(ANY)

    """
    @patch('crassus.deployer.notify')
    def test_deploy_stack_should_notify_error_in_case_of_client_error(
        self, notify_mock):
        self.stack_mock.load.side_effect = ClientError(
            {'Error': {'Code': 'ExpectedException', 'Message': ''}},
            'test_deploy_stack_should_notify_error_in_case_of_client_error')
        load_stack('ANY_STACK', 'ANY_ARN')

        notify_mock.assert_called_once_with(ANY, 'ANY_ARN')
    """


class TestStackUpdateParameters(unittest.TestCase):

    def setUp(self):
        self.input_message = {
            "version": 1,
            "stackName": "ANY_STACK",
            "region": "ANY_REGION",
            "parameters": {
                "PARAMETER1": "VALUE1",
                "PARAMETER2": "VALUE2",
            }
        }

    def test_init(self):
        sup = StackUpdateParameter(self.input_message)
        self.assertEqual(sup.version, 1)
        self.assertEqual(sup.stack_name, "ANY_STACK")
        self.assertEqual(sup.region, "ANY_REGION")
        self.assertEqual(sup.items(), [
            ("PARAMETER1", "VALUE1"),
            ("PARAMETER2", "VALUE2")])

    def test_to_aws_format(self):
        expected_output = [{"ParameterKey": "PARAMETER1",
                            "ParameterValue": "VALUE1"},
                           {"ParameterKey": "PARAMETER2",
                            "ParameterValue": "VALUE2"}]
        sup = StackUpdateParameter(self.input_message)
        self.assertEqual(sup.to_aws_format(), expected_output)

    def test_merge(self):
        input_message = {
            "version": 1,
            "stackName": "ANY_STACK",
            "region": "ANY_REGION",
            "parameters": {
                "PARAMETER2": "UPDATED_VALUE2",
            }
        }
        expected_output = [{"ParameterKey": "PARAMETER1",
                            "UsePreviousValue": True},
                           {"ParameterKey": "PARAMETER2",
                            "ParameterValue": "UPDATED_VALUE2"}]
        stack_parameter = [{"ParameterKey": "PARAMETER1",
                            "ParameterValue": "VALUE1"},
                           {"ParameterKey": "PARAMETER2",
                            "ParameterValue": "VALUE2"}]
        sup = StackUpdateParameter(input_message)
        self.assertEqual(sup.merge(stack_parameter), expected_output)


class TestInitOutputSnsTopic(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('boto3.client')
        self.boto3_client = self.patcher.start()
        self.context_mock = Mock(invoked_function_arn="any_arn",
                                 function_version="any_version")

    def tearDown(self):
        self.patcher.stop()

    def test_init_output_sns_topic_returns_arn_list(self):
        self.boto3_client().get_function_configuration.return_value = {
            'Description': dedent("""
                {"topic_list":[
                    "arn:aws:sns:eu-west-1:123456789012:crassus-output",
                    "arn:aws:sns:eu-west-1:123456789012:random-topic"
                    ]}""")
        }
        topic_list = init_output_sns_topic(self.context_mock)
        expected = ["arn:aws:sns:eu-west-1:123456789012:crassus-output",
                    "arn:aws:sns:eu-west-1:123456789012:random-topic", ]
        self.assertEqual(expected, topic_list)

    @patch('crassus.deployer.logger')
    def test_init_output_sns_topic_handles_value_error(self, logger_mock):
        self.boto3_client().get_function_configuration.return_value = {
            'Description': "NO_SUCH_JSON"
        }
        topic_list = init_output_sns_topic(self.context_mock)
        self.assertEqual(None, topic_list)
        logger_mock.error.assert_called_once_with(ANY)

    @patch('crassus.deployer.logger')
    def test_init_output_sns_topic_handles_key_error(self, logger_mock):
        self.boto3_client().get_function_configuration.return_value = {
            'Description': '{"key": "value"}'
        }
        topic_list = init_output_sns_topic(self.context_mock)
        self.assertEqual(None, topic_list)
        logger_mock.error.assert_called_once_with(ANY)


class TestResultMessage(unittest.TestCase):

    def test_constructor(self):
        result_message = ResultMessage('my_status', 'my_message')
        self.assertEqual(result_message['version'], '1.0')
        self.assertEqual(result_message['status'], 'my_status')
        self.assertEqual(result_message['message'], 'my_message')
        self.assertNotEqual(result_message['message'], 'NO_SUCH_MESSAGE')
