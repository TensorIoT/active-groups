import boto3
iotClient = boto3.client('iot')

def get_truth(inp,relate,cut):
    if eval("%s%s%s" % (inp,relate,cut)):
        return True
    else:
        return False

def process(jsonString):
    print jsonString
    groupName = jsonString['groupname']
    operator = jsonString['operator']
    threshold = jsonString['threshold']
    value = jsonString['value']
    thingName = jsonString['topic']
    attribute = jsonString['attribute']
    decision = get_truth(value, operator, threshold)
    if decision:
        print "add to group"
        try:
            response = iotClient.add_thing_to_thing_group(
                thingGroupName=groupName,
                thingName=thingName,
            )
        except Exception as e:
            print e
    else:
        print "remove from group"
        try:
            response = iotClient.remove_thing_from_thing_group(
                thingGroupName=groupName,
                thingName=thingName,
            )
        except Exception as e:
            print e
    print "All Done"

def lambda_handler(event, context):
    # TODO implement
    print event
    process(event)
    return 'Lambda Completed Successfully'
