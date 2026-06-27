import boto3
import logging
from typing import List, Dict, Optional
from botocore.exceptions import ClientError
from backend.core.config import settings

logger = logging.getLogger(__name__)


class AWSAlertsService:
    def __init__(self):
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.cloudwatch = boto3.client(
                'cloudwatch',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.sns = boto3.client(
                'sns',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        else:
            self.cloudwatch = None
            self.sns = None
            logger.warning("AWS credentials not configured. AWS alerts service will be disabled.")
    
    def send_pipeline_failure_alert(self, run_id: str, branch: str, error: str) -> bool:
        if not self.sns or not settings.SNS_ALERT_TOPIC_ARN:
            logger.warning("SNS not configured. Skipping alert.")
            return False
        
        try:
            message = f"""
SAPFlow Pipeline Failure Alert
===============================
Run ID: {run_id}
Branch: {branch}
Error: {error}
Timestamp: {self._get_timestamp()}
            """
            
            self.sns.publish(
                TopicArn=settings.SNS_ALERT_TOPIC_ARN,
                Subject=f"SAPFlow Pipeline Failure - {run_id}",
                Message=message.strip()
            )
            logger.info(f"Pipeline failure alert sent for run {run_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to send SNS alert: {e}")
            return False
    
    def create_cloudwatch_metric(self, metric_name: str, value: float, unit: str = 'Count') -> bool:
        if not self.cloudwatch:
            logger.warning("CloudWatch not configured. Skipping metric.")
            return False
        
        try:
            self.cloudwatch.put_metric_data(
                Namespace='SAPFlow',
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': self._get_timestamp()
                }]
            )
            logger.info(f"CloudWatch metric {metric_name} recorded with value {value}")
            return True
        except ClientError as e:
            logger.error(f"Failed to put CloudWatch metric: {e}")
            return False
    
    def check_alarm_states(self) -> List[Dict]:
        if not self.cloudwatch:
            logger.warning("CloudWatch not configured. Returning empty alarm list.")
            return []
        
        try:
            response = self.cloudwatch.describe_alarms()
            alarms = []
            for alarm in response['MetricAlarms']:
                alarms.append({
                    'alarm_name': alarm['AlarmName'],
                    'state': alarm['StateValue'],
                    'metric': alarm['MetricName'],
                    'threshold': alarm['Threshold'],
                    'period': alarm['Period']
                })
            return alarms
        except ClientError as e:
            logger.error(f"Failed to describe CloudWatch alarms: {e}")
            return []
    
    def _get_timestamp(self):
        from datetime import datetime
        return datetime.utcnow()
