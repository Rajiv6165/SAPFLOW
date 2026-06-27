#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
from abap_inspector import ABAPInspector
from transport_validator import TransportValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="SAP Transport Validation Runner")
    parser.add_argument("--transport-id", required=True, help="Transport request ID")
    parser.add_argument("--source-system", default="DEV", help="Source system (DEV/QA)")
    parser.add_argument("--mock", action="store_true", help="Force mock mode")
    
    args = parser.parse_args()
    
    if args.mock:
        os.environ["SAP_MOCK_MODE"] = "true"
    
    sap_host = os.getenv("SAP_BTP_HOST", "https://mock.sap.btp.com")
    client_id = os.getenv("SAP_CLIENT_ID", "mock_client_id")
    client_secret = os.getenv("SAP_CLIENT_SECRET", "mock_secret")
    
    logger.info(f"Starting validation for transport {args.transport_id}")
    logger.info(f"Source system: {args.source_system}")
    logger.info(f"Mock mode: {os.getenv('SAP_MOCK_MODE', 'false')}")
    
    try:
        inspector = ABAPInspector(
            sap_host=sap_host,
            client_id=client_id,
            client_secret=client_secret
        )
        
        logger.info("Running ABAP code inspection...")
        inspection_result = inspector.run_code_inspection(args.transport_id)
        
        logger.info("Validating transport objects...")
        objects = inspector.validate_transport_objects(args.transport_id)
        
        logger.info("Running transport validator...")
        validator = TransportValidator(objects)
        validation_report = validator.generate_report()
        
        final_report = {
            "transport_id": args.transport_id,
            "source_system": args.source_system,
            "inspection": inspection_result,
            "validation": validation_report,
            "overall_passed": validation_report["is_valid"] and inspection_result["passed"]
        }
        
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        print(json.dumps(final_report, indent=2))
        print("="*60)
        
        if final_report["overall_passed"]:
            logger.info("All validations passed successfully")
            sys.exit(0)
        else:
            logger.error("Validation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
