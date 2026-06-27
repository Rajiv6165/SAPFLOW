#!/usr/bin/env python3
import boto3
import json
import os

def setup_sns_topic():
    sns = boto3.client('sns', region_name='ap-south-1')
    
    topic_name = 'SAPFlow-Alerts'
    
    try:
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        print(f"Created SNS topic: {topic_arn}")
        
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=os.getenv('ALERT_EMAIL', 'devops@example.com')
        )
        print(f"Subscribed email to topic")
        
        sns.set_topic_attributes(
            TopicArn=topic_arn,
            AttributeName='DisplayName',
            AttributeValue='SAPFlow Pipeline Alerts'
        )
        
        return topic_arn
        
    except sns.exceptions.TopicAlreadyExistsException:
        response = sns.list_topics()
        for topic in response['Topics']:
            if topic_name in topic['TopicArn']:
                print(f"Topic already exists: {topic['TopicArn']}")
                return topic['TopicArn']
    except Exception as e:
        print(f"Error setting up SNS: {e}")
        raise

if __name__ == '__main__':
    topic_arn = setup_sns_topic()
    print(f"\nSNS Topic ARN: {topic_arn}")
    print("Add this ARN to your .env as SNS_ALERT_TOPIC_ARN")
