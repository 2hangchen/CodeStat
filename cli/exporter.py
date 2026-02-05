"""Export query results to CSV/JSON"""
import json
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from utils.time_utils import format_datetime

logger = logging.getLogger(__name__)


def export_to_json(data: Dict[str, Any], output_path: str) -> bool:
    """
    Export data as JSON format
    
    Args:
        data: Data to export
        output_path: Output file path
    
    Returns:
        Whether successful
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "export_time": format_datetime(datetime.now()),
            "data": data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Data exported to JSON: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to export to JSON: {e}")
        return False


def export_to_csv(metrics: Dict[str, Any], output_path: str) -> bool:
    """
    Export metrics data as CSV format
    
    Args:
        metrics: Metrics data
        output_path: Output file path
    
    Returns:
        Whether successful
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header row
            writer.writerow(["Metric Name", "Value"])
            
            # Write metrics data
            writer.writerow(["AI Generated Lines", metrics.get("ai_total_lines", 0)])
            writer.writerow(["Adopted Lines", metrics.get("adopted_lines", 0)])
            writer.writerow(["Code Adoption Rate (%)", metrics.get("adoption_rate", 0.0)])
            writer.writerow(["Code Generation Rate (%)", metrics.get("generation_rate", 0.0)])
            
            if "file_count" in metrics:
                writer.writerow(["Files Involved", metrics.get("file_count", 0)])
            
            if "session_count" in metrics:
                writer.writerow(["Sessions", metrics.get("session_count", 0)])
            
            # If there are diff lines details, write them
            diff_lines = metrics.get("diff_lines", [])
            if diff_lines:
                writer.writerow([])  # Empty row
                writer.writerow(["Diff Lines Details"])
                writer.writerow(["Diff Type", "Line Number", "Code Content"])
                for diff_line in diff_lines:
                    writer.writerow([
                        diff_line.get("diff_type", ""),
                        diff_line.get("line_number", ""),
                        diff_line.get("line_content", "")
                    ])
        
        logger.info(f"Data exported to CSV: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to export to CSV: {e}")
        return False


def export_metrics(metrics: Dict[str, Any], output_path: str, format: str = "json") -> bool:
    """
    Export metrics data
    
    Args:
        metrics: Metrics data
        output_path: Output file path
        format: Export format (json or csv)
    
    Returns:
        Whether successful
    """
    if format.lower() == "csv":
        return export_to_csv(metrics, output_path)
    else:
        return export_to_json(metrics, output_path)
