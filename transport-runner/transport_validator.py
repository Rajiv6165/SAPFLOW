import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransportValidator:
    def __init__(self, transport_objects: List[Dict]):
        self.transport_objects = transport_objects
        self.validation_results = {
            "naming_conventions": [],
            "dependencies": [],
            "overall_valid": True
        }
    
    def check_naming_conventions(self) -> List[Dict]:
        findings = []
        
        for obj in self.transport_objects:
            object_name = obj.get("object_name", "")
            object_type = obj.get("object_type", "")
            
            if not object_name.startswith(("Z", "Y")):
                finding = {
                    "object": object_name,
                    "type": object_type,
                    "issue": "Object name does not follow SAP custom namespace (Z/Y)",
                    "severity": "ERROR"
                }
                findings.append(finding)
                self.validation_results["overall_valid"] = False
                logger.warning(f"Naming convention violation: {object_name}")
            else:
                finding = {
                    "object": object_name,
                    "type": object_type,
                    "issue": "Object name follows SAP custom namespace",
                    "severity": "INFO"
                }
                findings.append(finding)
        
        self.validation_results["naming_conventions"] = findings
        return findings
    
    def check_dependencies(self) -> List[Dict]:
        findings = []
        
        for obj in self.transport_objects:
            object_name = obj.get("object_name", "")
            object_type = obj.get("object_type", "")
            package = obj.get("package", "")
            
            if not package or not package.startswith(("Z", "Y", "$TMP")):
                finding = {
                    "object": object_name,
                    "type": object_type,
                    "issue": f"Package '{package}' may not be included in transport",
                    "severity": "WARNING"
                }
                findings.append(finding)
                logger.warning(f"Dependency check warning: {object_name} in package {package}")
            else:
                finding = {
                    "object": object_name,
                    "type": object_type,
                    "issue": f"Package '{package}' is included",
                    "severity": "INFO"
                }
                findings.append(finding)
        
        self.validation_results["dependencies"] = findings
        return findings
    
    def generate_report(self) -> Dict:
        self.check_naming_conventions()
        self.check_dependencies()
        
        error_count = sum(1 for f in self.validation_results["naming_conventions"] if f["severity"] == "ERROR")
        warning_count = sum(1 for f in self.validation_results["naming_conventions"] if f["severity"] == "WARNING")
        warning_count += sum(1 for f in self.validation_results["dependencies"] if f["severity"] == "WARNING")
        
        report = {
            "is_valid": self.validation_results["overall_valid"],
            "total_objects": len(self.transport_objects),
            "error_count": error_count,
            "warning_count": warning_count,
            "naming_conventions": self.validation_results["naming_conventions"],
            "dependencies": self.validation_results["dependencies"],
            "summary": f"Validation complete: {error_count} errors, {warning_count} warnings"
        }
        
        logger.info(f"Validation report generated: {report['summary']}")
        return report
