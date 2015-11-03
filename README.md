[![Build Status](https://travis-ci.org/ImmobilienScout24/crassus.svg?branch=master)](https://travis-ci.org/ImmobilienScout24/crassus)
[![Code Health](https://landscape.io/github/ImmobilienScout24/crassus/master/landscape.svg?style=flat)](https://landscape.io/github/ImmobilienScout24/crassus/master)
[![Coverage Status](https://coveralls.io/repos/ImmobilienScout24/crassus/badge.svg?branch=master&service=github)](https://coveralls.io/github/ImmobilienScout24/crassus?branch=master)

# crassus
Cross Account Smart Software Update Service

## Deployer
### Event interface
Actual a SNS with a json payload is used to trigger crassus. The payload should look like this:

```json
      {
        "version": 1,
        "stackName": "sample-stack",
        "region": "<AWS-REGION-ID>",
        "parameters": {
            "parameter1": "value1",
            "parameter2": "value2",
        }
      }
```


Sample event as expected from deployer
```json
{
  "Records": [
    {
      "EventVersion": "1.0",
      "EventSubscriptionArn": "<SUBSCRIPTION ARN>",
      "EventSource": "aws: sns",
      "Sns": {
        "SignatureVersion": "1",
        "Timestamp": "2015-10-23T11: 01: 16.140Z",
        "Signature": "<SIGNATURE>",
        "SigningCertUrl": "<SIGNING URL>",
        "MessageId": "<MESSAGE ID>",
        "Message": "{
        "version": 1,
        "stackName": "sample-stack",
        "region": "eu-west-1",
        "parameters": {
                      "InstanceType": "t2.micro"
                  }
      }",
      "MessageAttributes": {
      },
      "Type": "Notification",
      "UnsubscribeUrl": "<UNSUBSCRIBE URL>",
      "TopicArn": "<TOPIC ARN>",
      "Subject": None
    }
  }
  ]
}
```
