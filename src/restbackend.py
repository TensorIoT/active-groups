from time import sleep
import boto3, json, os, uuid, logging, random, string

iotClient = boto3.client('iot')
functionARN = os.environ['functionARN']
REGION = os.environ['REGION']
ACCOUNT = os.environ['ACCOUNT']

def constructResponse(statusCode, responseBody):
    response = {
        "statusCode": statusCode,
        "headers": {"Content-Type": "application/json"},
        "body": responseBody
    }
    print(response)
    return response

def lambda_handler(event, context):
    print(event)
    inputBody = json.loads(event['body'])
    print(inputBody)

    if inputBody['Operation'] not in ['NEW', 'GET', 'DELETE'] :
        return constructResponse(400, "Operation "+inputBody['Operation']+" Not permitted")

    if inputBody['Operation'] == 'DELETE':
        if 'GroupName' not in inputBody:
            return constructResponse(400, "GroupName object not found")
        groupName = inputBody['GroupName']
        try:
            response = iotClient.delete_topic_rule(
                ruleName=groupName
            )
            response = iotClient.delete_thing_group(
                thingGroupName=groupName
            )
            return constructResponse(200, json.dumps({'response': 'Group Deleted'}))
        except Exception as e:
            print e
            return constructResponse(400, json.dumps({"Error": "Group Deletion Error"}))

    if inputBody['Operation'] == 'GET':
        if 'GroupName' not in inputBody:
            return constructResponse(400, "GroupName object not found")
        groupName = inputBody['GroupName']
        try:
            response = iotClient.describe_thing_group(
                thingGroupName=groupName
            )
            print response
            return constructResponse(200, json.dumps({"groupARN": response['thingGroupArn'], "groupID": response['thingGroupId']}))
        except Exception as e:
            print e
            return constructResponse(400, json.dumps({"Error": "Group Retrieval Error"}))

    if inputBody['Operation'] == 'NEW':
        if 'Operator' not in inputBody:
            return constructResponse(400, "Operator object not found")

        if 'Attribute' not in inputBody:
            return constructResponse(400, "Attribute object not found")

        if 'GroupName' not in inputBody:
            return constructResponse(400, "GroupName object not found")

        if 'Threshold' not in inputBody:
            return constructResponse(400, "Threshold object not found")

        ruleDesc = inputBody['GroupName']
        ruleName = inputBody['GroupName']
        attribute = inputBody['Attribute']
        operator = inputBody['Operator']
        threshold = inputBody['Threshold']
        groupName = inputBody['GroupName']

        try:
            response = iotClient.create_thing_group(
                thingGroupName=groupName,
                thingGroupProperties={
                    'attributePayload': {
                        'attributes': {
                            'attribute': str(attribute),
                            'threshold': str(threshold)
                        }
                    }
                }
            )
            print response
            response = iotClient.create_topic_rule(
                ruleName=ruleName,
                topicRulePayload={
                    'sql': "SELECT '"+attribute+"' as attribute, current.state.reported."+attribute+" as value, topic(3) as topic, '"+operator+"' as operator, "+str(threshold)+" as threshold, '"+groupName+"' as groupname FROM '$aws/things/+/shadow/update/documents' WHERE (current.state.reported."+attribute+" "+operator+" "+str(threshold)+" AND NOT (previous.state.reported."+attribute+" "+operator+" "+str(threshold)+")) OR (NOT (current.state.reported."+attribute+" "+operator+" "+str(threshold)+") AND previous.state.reported."+attribute+" "+operator+" "+str(threshold)+")",
                    'description': ruleDesc,
                    'awsIotSqlVersion': '2016-03-23',
                    'actions': [
                        {
                            'lambda': {
                                'functionArn': 'arn:aws:lambda:'+REGION+':'+ACCOUNT+':function:'+functionARN
                            }
                        }
                    ],
                    'ruleDisabled': False
                }
            )
            print response
            return constructResponse(200, json.dumps({'response': 'Group Created'}))
        except Exception as e:
            print e
            return constructResponse(400, json.dumps({"Error": "Group Creation Error"}))
