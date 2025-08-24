#!/usr/bin/env python3

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import os

class InventoryAuditor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tolerance = 0.01  # Tolerance for rounding errors (1 cent/unit)
        self.audit_results_file = os.path.join(data_dir, "audit_results.csv")
        
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all three data files."""
        consumption_file = os.path.join(self.data_dir, "daily_consumption.csv")
        stock_file = os.path.join(self.data_dir, "daily_stock_levels.csv")
        deliveries_file = os.path.join(self.data_dir, "deliveries.csv")
        
        consumption_df = pd.read_csv(consumption_file)
        stock_df = pd.read_csv(stock_file)
        deliveries_df = pd.read_csv(deliveries_file)
        
        # Convert dates to datetime
        consumption_df['Date'] = pd.to_datetime(consumption_df['Date'])
        stock_df['Date'] = pd.to_datetime(stock_df['Date'])
        deliveries_df['Date'] = pd.to_datetime(deliveries_df['Date'])
        
        return consumption_df, stock_df, deliveries_df
    
    def audit_stock_consistency(self) -> Dict[str, List[Dict]]:
        """
        Audit inventory data for consistency.
        Formula: Previous_Stock - Consumption + Delivery_Amount = Current_Stock
        """
        consumption_df, stock_df, deliveries_df = self.load_data()
        
        issues = {
            'calculation_errors': [],
            'missing_stock_records': [],
            'negative_values': [],
            'missing_deliveries': [],
            'data_validation_errors': []
        }
        
        # First validate data constraints
        for idx, row in consumption_df.iterrows():
            date = row['Date'].strftime('%Y-%m-%d')
            item = row['Item_Name']
            consumption = row['Consumption']
            delivery = row['Delivery_Amount']
            previous_stock = row['Previous_Stock']
            stock_before = row['Stock_Before_Delivery']
            
            # Check for negative values (not allowed)
            if consumption < 0:
                issues['data_validation_errors'].append({
                    'date': date,
                    'item': item,
                    'field': 'Consumption',
                    'value': consumption,
                    'issue': 'Consumption cannot be negative'
                })
            
            if delivery < 0:
                issues['data_validation_errors'].append({
                    'date': date,
                    'item': item,
                    'field': 'Delivery_Amount',
                    'value': delivery,
                    'issue': 'Delivery amount cannot be negative'
                })
            
            if stock_before < 0:
                issues['data_validation_errors'].append({
                    'date': date,
                    'item': item,
                    'field': 'Stock_Before_Delivery',
                    'value': stock_before,
                    'issue': 'Stock before delivery cannot be negative'
                })
            
            if previous_stock < 0:
                issues['data_validation_errors'].append({
                    'date': date,
                    'item': item,
                    'field': 'Previous_Stock',
                    'value': previous_stock,
                    'issue': 'Previous stock cannot be negative'
                })

        # Group by item for sequential analysis
        for item in consumption_df['Item_Name'].unique():
            item_consumption = consumption_df[consumption_df['Item_Name'] == item].sort_values('Date')
            item_stock = stock_df[stock_df['Item_Name'] == item].sort_values('Date')
            item_deliveries = deliveries_df[deliveries_df['Item_Name'] == item].sort_values('Date')
            
            # Check each consumption record
            for idx, row in item_consumption.iterrows():
                date = row['Date']
                consumption = row['Consumption']
                stock_before = row['Stock_Before_Delivery']
                delivery_in_consumption = row['Delivery_Amount']
                previous_stock = row['Previous_Stock']
                
                # Find corresponding stock level
                stock_record = item_stock[item_stock['Date'] == date]
                if stock_record.empty:
                    issues['missing_stock_records'].append({
                        'date': date.strftime('%Y-%m-%d'),
                        'item': item,
                        'issue': 'No corresponding stock record found'
                    })
                    continue
                
                current_stock = stock_record.iloc[0]['Current_Stock']
                
                # Check if there's a delivery recorded in deliveries.csv for this date/item
                delivery_record = item_deliveries[item_deliveries['Date'] == date]
                actual_delivery = delivery_record['Delivery_Amount'].sum() if not delivery_record.empty else 0
                
                # If there's a delivery in deliveries.csv but not in consumption data
                if actual_delivery > 0 and delivery_in_consumption == 0:
                    issues['missing_deliveries'].append({
                        'date': date.strftime('%Y-%m-%d'),
                        'item': item,
                        'delivery_in_file': actual_delivery,
                        'delivery_in_consumption': delivery_in_consumption,
                        'issue': f'Delivery of {actual_delivery} recorded in deliveries.csv but missing from consumption data'
                    })
                    # Use the actual delivery for calculation
                    delivery = actual_delivery
                else:
                    delivery = delivery_in_consumption
                
                # Calculate expected stock: previous_stock - consumption + delivery
                expected_stock = previous_stock - consumption + delivery
                
                # Check for calculation errors (with tolerance for rounding)
                if abs(expected_stock - current_stock) > self.tolerance:
                    issues['calculation_errors'].append({
                        'date': date.strftime('%Y-%m-%d'),
                        'item': item,
                        'previous_stock': previous_stock,
                        'consumption': consumption,
                        'delivery': delivery,
                        'expected_stock': round(expected_stock, 2),
                        'actual_stock': current_stock,
                        'difference': round(current_stock - expected_stock, 2),
                        'calculation': f"{previous_stock} - {consumption} + {delivery} = {expected_stock}",
                        'note': 'Used delivery from deliveries.csv' if actual_delivery > 0 and delivery_in_consumption == 0 else ''
                    })
                
                # Check for negative stock values in stock file
                if current_stock < 0:
                    issues['negative_values'].append({
                        'date': date.strftime('%Y-%m-%d'),
                        'item': item,
                        'current_stock': current_stock,
                        'issue': 'Negative stock value in stock file'
                    })
        
        return issues
    
    def generate_audit_report(self, issues: Dict[str, List[Dict]]) -> str:
        """Generate a formatted audit report."""
        report = []
        report.append("=" * 60)
        report.append("INVENTORY AUDIT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        
        if total_issues == 0:
            report.append("\n✓ NO ISSUES FOUND - All inventory data is consistent!")
        else:
            report.append(f"\n⚠️  FOUND {total_issues} ISSUE(S):\n")
            
            # Data validation errors (highest priority)
            if issues['data_validation_errors']:
                report.append(f"DATA VALIDATION ERRORS ({len(issues['data_validation_errors'])}):")
                report.append("-" * 40)
                for error in issues['data_validation_errors']:
                    report.append(f"Date: {error['date']}")
                    report.append(f"Item: {error['item']}")
                    report.append(f"Field: {error['field']}")
                    report.append(f"Value: {error['value']}")
                    report.append(f"Issue: {error['issue']}")
                    report.append("")
            
            # Missing deliveries
            if issues['missing_deliveries']:
                report.append(f"MISSING DELIVERIES IN CONSUMPTION DATA ({len(issues['missing_deliveries'])}):")
                report.append("-" * 40)
                for missing in issues['missing_deliveries']:
                    report.append(f"Date: {missing['date']}")
                    report.append(f"Item: {missing['item']}")
                    report.append(f"Delivery in deliveries.csv: {missing['delivery_in_file']}")
                    report.append(f"Delivery in consumption.csv: {missing['delivery_in_consumption']}")
                    report.append(f"Issue: {missing['issue']}")
                    report.append("")
            
            # Calculation errors
            if issues['calculation_errors']:
                report.append(f"CALCULATION ERRORS ({len(issues['calculation_errors'])}):")
                report.append("-" * 40)
                for error in issues['calculation_errors']:
                    report.append(f"Date: {error['date']}")
                    report.append(f"Item: {error['item']}")
                    report.append(f"Formula: {error['calculation']}")
                    report.append(f"Expected: {error['expected_stock']}")
                    report.append(f"Actual: {error['actual_stock']}")
                    report.append(f"Difference: {error['difference']}")
                    if error.get('note'):
                        report.append(f"Note: {error['note']}")
                    report.append("")
            
            # Missing stock records
            if issues['missing_stock_records']:
                report.append(f"MISSING STOCK RECORDS ({len(issues['missing_stock_records'])}):")
                report.append("-" * 40)
                for missing in issues['missing_stock_records']:
                    report.append(f"Date: {missing['date']}")
                    report.append(f"Item: {missing['item']}")
                    report.append(f"Issue: {missing['issue']}")
                    report.append("")
            
            # Negative values
            if issues['negative_values']:
                report.append(f"NEGATIVE STOCK VALUES ({len(issues['negative_values'])}):")
                report.append("-" * 40)
                for negative in issues['negative_values']:
                    report.append(f"Date: {negative['date']}")
                    report.append(f"Item: {negative['item']}")
                    report.append(f"Current Stock: {negative['current_stock']}")
                    report.append(f"Issue: {negative['issue']}")
                    report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)
    
    def save_audit_results_to_csv(self, issues: Dict[str, List[Dict]]) -> None:
        """Save audit results to CSV for web app consumption."""
        audit_records = []
        
        # Process each issue type and create records
        for issue_type, issue_list in issues.items():
            for issue in issue_list:
                record = {
                    'Issue_Type': issue_type.replace('_', ' ').title(),
                    'Date': issue.get('date', ''),
                    'Item_Name': issue.get('item', ''),
                    'Severity': self._get_issue_severity(issue_type),
                    'Description': self._get_issue_description(issue_type, issue),
                    'Expected_Value': issue.get('expected_stock', ''),
                    'Actual_Value': issue.get('actual_stock', ''),
                    'Difference': issue.get('difference', ''),
                    'Field': issue.get('field', ''),
                    'Value': issue.get('value', ''),
                    'Note': issue.get('note', ''),
                    'Audit_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                audit_records.append(record)
        
        # If no issues, create a summary record
        if not audit_records:
            audit_records.append({
                'Issue_Type': 'No Issues',
                'Date': '',
                'Item_Name': 'All Items',
                'Severity': 'Success',
                'Description': 'All inventory data is consistent and passes validation',
                'Expected_Value': '',
                'Actual_Value': '',
                'Difference': '',
                'Field': '',
                'Value': '',
                'Note': '',
                'Audit_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Save to CSV
        audit_df = pd.DataFrame(audit_records)
        audit_df.to_csv(self.audit_results_file, index=False)
        
    def _get_issue_severity(self, issue_type: str) -> str:
        """Get severity level for issue type."""
        severity_map = {
            'data_validation_errors': 'Critical',
            'missing_deliveries': 'High',
            'calculation_errors': 'Medium',
            'missing_stock_records': 'High',
            'negative_values': 'Critical'
        }
        return severity_map.get(issue_type, 'Low')
    
    def _get_issue_description(self, issue_type: str, issue: Dict) -> str:
        """Generate human-readable description for issue."""
        if issue_type == 'calculation_errors':
            return f"Stock calculation mismatch: Expected {issue.get('expected_stock')} but found {issue.get('actual_stock')}"
        elif issue_type == 'data_validation_errors':
            return f"{issue.get('field')} has invalid value: {issue.get('issue')}"
        elif issue_type == 'missing_deliveries':
            return f"Delivery of {issue.get('delivery_in_file')} not reflected in consumption data"
        elif issue_type == 'missing_stock_records':
            return f"No stock record found for consumption entry"
        elif issue_type == 'negative_values':
            return f"Negative stock value detected: {issue.get('issue')}"
        else:
            return str(issue.get('issue', 'Unknown issue'))

    def run_audit(self) -> str:
        """Run complete audit and return report."""
        try:
            issues = self.audit_stock_consistency()
            
            # Save results to CSV for web app
            self.save_audit_results_to_csv(issues)
            
            # Generate text report
            report = self.generate_audit_report(issues)
            return report
        except Exception as e:
            return f"ERROR: Failed to run audit - {str(e)}"

def main():
    """Main function to run the audit."""
    auditor = InventoryAuditor()
    report = auditor.run_audit()
    print(report)
    
    # Also save report to file
    with open('audit_report.txt', 'w') as f:
        f.write(report)
    print(f"\nAudit report saved to: audit_report.txt")

if __name__ == "__main__":
    main()