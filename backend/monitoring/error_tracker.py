#!/usr/bin/env python3
import re
import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class ErrorTracker:
    def __init__(self, log_dir='/home/*/Documents/HireWise/backend/logs'):
        self.log_dir = Path(log_dir).expanduser()
        self.error_patterns = [
            r'ERROR.*',
            r'CRITICAL.*',
            r'Exception.*',
            r'Traceback.*'
        ]
    
    def scan_logs(self, hours_back=1):
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        errors = []
        
        for log_file in self.log_dir.glob('*.log'):
            try:
                with open(log_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in self.error_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                errors.append({
                                    'file': log_file.name,
                                    'line': line_num,
                                    'content': line.strip(),
                                    'timestamp': datetime.now().isoformat()
                                })
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        
        return errors
    
    def generate_report(self, errors):
        if not errors:
            return "No errors found in the specified time period."
        
        report = f"HireWise Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 60 + "\n\n"
        report += f"Total errors found: {len(errors)}\n\n"
        
        # Group by file
        by_file = {}
        for error in errors:
            file_name = error['file']
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(error)
        
        for file_name, file_errors in by_file.items():
            report += f"File: {file_name} ({len(file_errors)} errors)\n"
            report += "-" * 40 + "\n"
            for error in file_errors[:5]:  # Show first 5 errors per file
                report += f"Line {error['line']}: {error['content']}\n"
            if len(file_errors) > 5:
                report += f"... and {len(file_errors) - 5} more errors\n"
            report += "\n"
        
        return report
    
    def send_alert(self, report, email_config=None):
        if not email_config:
            print("Email configuration not provided. Printing report:")
            print(report)
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = email_config['to']
            msg['Subject'] = "HireWise Error Alert"
            
            msg.attach(MIMEText(report, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_host'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            print("Error alert sent successfully")
        except Exception as e:
            print(f"Failed to send alert: {e}")
    
    def run_check(self, hours_back=1, email_config=None):
        errors = self.scan_logs(hours_back)
        report = self.generate_report(errors)
        
        if errors:
            self.send_alert(report, email_config)
        
        return len(errors)

if __name__ == '__main__':
    import sys
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    tracker = ErrorTracker()
    error_count = tracker.run_check(hours)
    
    print(f"Error tracking completed. Found {error_count} errors in the last {hours} hour(s).")