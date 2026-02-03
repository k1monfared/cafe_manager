#!/usr/bin/env python3
"""
Simplified Inventory Management Web Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
import pandas as pd
from datetime import datetime, timedelta
from inventory_engine import InventoryEngine
import json
import os
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = 'simple-inventory-2025'

# Initialize inventory engine
engine = InventoryEngine()

@app.route('/')
def dashboard():
    """Main dashboard showing current status and alerts"""
    try:
        # Use test engine if in testing mode
        current_engine = app.config.get('engine', engine)
        
        # Get current status
        status = current_engine.get_current_status()
        
        # Load current stock levels
        stock_df = current_engine.load_stock_data()
        item_info_df = current_engine.load_item_info()
        
        current_stocks = []
        if not stock_df.empty and not item_info_df.empty:
            latest_stocks = stock_df.groupby('Item_Name').last()
            
            for item_name in latest_stocks.index:
                stock_info = latest_stocks.loc[item_name]
                item_info = item_info_df[item_info_df['Item_Name'] == item_name]
                
                if not item_info.empty:
                    item_data = item_info.iloc[0]
                    current_stock = stock_info['Current_Stock']
                    min_threshold = item_data['Min_Threshold']
                    
                    # Determine status
                    if current_stock <= min_threshold:
                        status_class = 'danger'
                        status_text = 'Below Threshold'
                    elif current_stock <= min_threshold * 1.5:
                        status_class = 'warning'
                        status_text = 'Getting Low'
                    else:
                        status_class = 'success'
                        status_text = 'Good'
                    
                    current_stocks.append({
                        'item_name': item_name,
                        'current_stock': current_stock,
                        'unit': item_data['Unit'],
                        'min_threshold': min_threshold,
                        'status_class': status_class,
                        'status_text': status_text,
                        'last_updated': stock_info['Date'].strftime('%Y-%m-%d') if hasattr(stock_info['Date'], 'strftime') else str(stock_info['Date'])
                    })
        
        # Load recommendations
        recommendations = []
        try:
            recommendations_df = pd.read_csv(current_engine.recommendations_file)
            if not recommendations_df.empty:
                recommendations = recommendations_df.to_dict('records')
        except FileNotFoundError:
            pass
        
        return render_template('simple_dashboard.html', 
                             status=status, 
                             current_stocks=current_stocks,
                             recommendations=recommendations)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('simple_dashboard.html', 
                             status={}, 
                             current_stocks=[],
                             recommendations=[])



@app.route('/api/add_delivery', methods=['POST'])
def add_delivery():
    """Add delivery entry via API"""
    try:
        data = request.json
        date = data.get('date')
        item_name = data.get('item_name')
        delivery_amount = float(data.get('delivery_amount', 0))
        notes = data.get('notes', '')
        
        if not date or not item_name:
            return jsonify({'success': False, 'error': 'Date and item name are required'})
        
        current_engine = app.config.get('engine', engine)
        success = current_engine.add_delivery_entry(date, item_name, delivery_amount, notes)
        
        if success:
            return jsonify({'success': True, 'message': f'Added delivery entry for {item_name}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to add delivery entry'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/analytics')
def analytics():
    """Analytics page with detailed explanations"""
    try:
        # Use test engine if in testing mode
        current_engine = app.config.get('engine', engine)
        
        # Load stock and delivery data for enhanced charts
        stock_df = current_engine.load_stock_data()
        delivery_df = current_engine.load_delivery_data()
        
        # Load forecast results
        forecast_data = []
        try:
            forecast_df = pd.read_csv(current_engine.forecast_file)
            if not forecast_df.empty:
                for _, row in forecast_df.iterrows():
                    item_name = row['Item_Name']
                    
                    # Parse chart data - handle NaN values and convert to string
                    chart_dates_raw = str(row['Chart_Dates']) if pd.notna(row['Chart_Dates']) else ''
                    chart_consumption_raw = str(row['Chart_Consumption']) if pd.notna(row['Chart_Consumption']) else ''
                    
                    chart_dates = chart_dates_raw.split('|') if chart_dates_raw else []
                    chart_consumption = [float(x) for x in chart_consumption_raw.split('|') if x.strip() and x.strip().lower() != 'nan'] if chart_consumption_raw else []
                    
                    # Get stock levels for the same dates
                    chart_stock_levels = []
                    delivery_markers = []
                    
                    if not stock_df.empty and chart_dates:
                        item_stock_data = stock_df[stock_df['Item_Name'] == item_name].copy()
                        if not item_stock_data.empty:
                            item_stock_data['Date'] = pd.to_datetime(item_stock_data['Date'])
                            item_stock_data = item_stock_data.sort_values('Date')
                            
                            # Get stock levels for chart dates
                            for date_str in chart_dates:
                                date_match = item_stock_data[item_stock_data['Date'] == pd.to_datetime(date_str)]
                                if not date_match.empty:
                                    chart_stock_levels.append(float(date_match.iloc[0]['Current_Stock']))
                                else:
                                    chart_stock_levels.append(None)
                    
                    # Get delivery information for this item
                    if not delivery_df.empty:
                        # Apply item name mapping for deliveries
                        item_mapping = {
                            'House Blend Coffee': 'Coffee Beans',
                            'Whole Milk': 'Milk',
                            '12oz Paper Cups': 'Paper Cups',
                            'Test Coffee': 'Coffee Beans',
                            'Test Milk': 'Milk',
                            'Vanilla Syrup': 'Sugar'
                        }
                        
                        # Find deliveries for this item (with name mapping)
                        item_deliveries = delivery_df[delivery_df['Item_Name'] == item_name].copy()
                        for delivery_name, stock_name in item_mapping.items():
                            if stock_name == item_name:
                                mapped_deliveries = delivery_df[delivery_df['Item_Name'] == delivery_name].copy()
                                item_deliveries = pd.concat([item_deliveries, mapped_deliveries], ignore_index=True)
                        
                        if not item_deliveries.empty:
                            item_deliveries['Date'] = pd.to_datetime(item_deliveries['Date'])
                            
                            # Create delivery markers for chart dates
                            for i, date_str in enumerate(chart_dates):
                                date_deliveries = item_deliveries[item_deliveries['Date'] == pd.to_datetime(date_str)]
                                if not date_deliveries.empty:
                                    total_delivery = date_deliveries['Delivery_Amount'].sum()
                                    delivery_markers.append({
                                        'x': i,
                                        'amount': float(total_delivery),
                                        'date': date_str
                                    })
                    
                    forecast_data.append({
                        'item_name': item_name,
                        'current_stock': row['Current_Stock'],
                        'unit': row['Unit'],
                        'min_threshold': row['Min_Threshold'],
                        'max_capacity': row['Max_Capacity'],
                        'avg_daily_consumption': row['Avg_Daily_Consumption'],
                        'days_remaining': row['Days_Remaining'],
                        'runout_date': row['Runout_Date'],
                        'confidence': row['Confidence'],
                        'data_points': row['Data_Points_Used'],
                        'chart_dates': chart_dates,
                        'chart_consumption': chart_consumption,
                        'chart_stock_levels': chart_stock_levels,
                        'delivery_markers': delivery_markers
                    })
        except FileNotFoundError:
            pass
        
        # Load recommendations
        recommendations_data = []
        try:
            recommendations_df = pd.read_csv(current_engine.recommendations_file)
            if not recommendations_df.empty:
                recommendations_data = recommendations_df.to_dict('records')
        except FileNotFoundError:
            pass
        
        # Load item info data
        item_info_data = {}
        try:
            item_info_df = current_engine.load_item_info()
            if not item_info_df.empty:
                # Create a dictionary mapping item names to their info
                for _, row in item_info_df.iterrows():
                    item_info_data[row['Item_Name']] = row.to_dict()
        except FileNotFoundError:
            pass
        
        return render_template('analytics.html', 
                             forecast_data=forecast_data,
                             recommendations=recommendations_data,
                             item_info=item_info_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('analytics.html', forecast_data=[], recommendations=[], item_info={})

@app.route('/upload')
def upload_page():
    """CSV upload page"""
    return render_template('upload.html')


@app.route('/audit_results')
def audit_results_page():
    """Data audit results page showing validation issues and recommendations"""
    try:
        current_engine = app.config.get('engine', engine)
        
        # Load audit results
        audit_results = []
        audit_summary = None
        all_clear = False
        issues_by_severity = {}
        item_status = []
        
        try:
            audit_df = pd.read_csv(current_engine.auditor.audit_results_file)
            if not audit_df.empty:
                audit_results = audit_df.to_dict('records')
                
                # Check if it's an "all clear" result
                if len(audit_results) == 1 and audit_results[0]['Severity'] == 'Success':
                    all_clear = True
                    # Get list of items that were checked
                    stock_df = current_engine.load_stock_data()
                    if not stock_df.empty:
                        item_status = stock_df['Item_Name'].unique().tolist()
                else:
                    # Group issues by severity
                    for result in audit_results:
                        severity = result['Severity']
                        if severity not in issues_by_severity:
                            issues_by_severity[severity] = []
                        issues_by_severity[severity].append(result)
                
                # Create audit summary
                total_issues = len(audit_results) if not all_clear else 0
                last_run = audit_results[0]['Audit_Date'] if audit_results else 'Never'
                
                if all_clear:
                    status = 'Success'
                elif any(r['Severity'] == 'Critical' for r in audit_results):
                    status = 'Critical'
                elif any(r['Severity'] == 'High' for r in audit_results):
                    status = 'Warning'
                else:
                    status = 'Info'
                
                audit_summary = {
                    'last_run': last_run,
                    'total_issues': total_issues,
                    'items_checked': len(set(r['Item_Name'] for r in audit_results if r['Item_Name'])) or len(item_status),
                    'status': status
                }
                
        except FileNotFoundError:
            all_clear = True  # No audit file means no audit has been run yet
            audit_summary = {
                'last_run': 'Never',
                'total_issues': 0,
                'items_checked': 0,
                'status': 'Info'
            }
        
        # Generate recommendations based on issues
        recommendations = []
        if issues_by_severity:
            if 'Critical' in issues_by_severity:
                recommendations.append({
                    'title': 'Address Critical Issues Immediately',
                    'description': 'Critical issues can cause data corruption. Please review and fix negative values or validation errors.'
                })
            if 'High' in issues_by_severity:
                recommendations.append({
                    'title': 'Review Missing Data',
                    'description': 'Some deliveries or stock records may be missing. Check your data entry processes.'
                })
            if 'Medium' in issues_by_severity:
                recommendations.append({
                    'title': 'Verify Calculations',
                    'description': 'Some stock calculations don\'t match expected values. Review your consumption tracking.'
                })
        
        return render_template('audit_results.html',
                             audit_results=audit_results,
                             audit_summary=audit_summary,
                             all_clear=all_clear,
                             issues_by_severity=issues_by_severity,
                             item_status=item_status,
                             recommendations=recommendations)
                             
    except Exception as e:
        flash(f'Error loading audit results: {str(e)}', 'error')
        return render_template('audit_results.html',
                             audit_results=[],
                             audit_summary=None,
                             all_clear=True,
                             issues_by_severity={},
                             item_status=[],
                             recommendations=[])

@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    """Handle CSV file uploads"""
    try:
        # Use test engine if in testing mode
        current_engine = app.config.get('engine', engine)
        
        if 'csv_file' not in request.files:
            flash('No file provided', 'error')
            return redirect('/upload')
        
        file = request.files['csv_file']
        file_type = request.form.get('file_type')
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect('/upload')
        
        if not file_type:
            flash('File type not specified', 'error')
            return redirect('/upload')
        
        # Validate file extension
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return redirect('/upload')
        
        # Read and validate CSV content
        content = file.read().decode('utf-8')
        
        # Basic validation - check if it has comma separators
        lines = content.strip().split('\n')
        if len(lines) < 2:
            flash('CSV file must have at least a header and one data row', 'error')
            return redirect('/upload')
        
        # Save to appropriate file
        if file_type == 'stock_levels':
            file_path = current_engine.stock_file
            # Validate stock levels format
            if 'Date,Item_Name,Current_Stock' not in lines[0]:
                flash('Stock levels CSV must have columns: Date,Item_Name,Current_Stock', 'error')
                return redirect('/upload')
        elif file_type == 'deliveries':
            file_path = current_engine.delivery_file
            # Validate deliveries format
            if 'Date,Item_Name,Delivery_Amount' not in lines[0]:
                flash('Deliveries CSV must have columns: Date,Item_Name,Delivery_Amount,Notes', 'error')
                return redirect('/upload')
        elif file_type == 'item_info':
            file_path = current_engine.item_info_file
            # Validate item info format
            if 'Item_Name,Unit' not in lines[0]:
                flash('Item info CSV must have columns starting with: Item_Name,Unit', 'error')
                return redirect('/upload')
        else:
            flash('Invalid file type', 'error')
            return redirect('/upload')
        
        # Backup existing file
        import shutil
        import os
        if os.path.exists(file_path):
            backup_path = file_path + '.backup'
            shutil.copy2(file_path, backup_path)
        
        # Save new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Recalculate everything if it's data that affects analytics
        if file_type in ['stock_levels', 'deliveries', 'item_info']:
            # Run all analytics calculations
            consumption_df = current_engine.calculate_daily_consumption()
            forecast_df = current_engine.calculate_forecast()
            recommendations_df = current_engine.generate_recommendations()
            
            # Provide detailed feedback on what was updated
            flash(f'✅ Successfully uploaded {file_type.replace("_", " ")} data!', 'success')
            flash(f'📊 Auto-updated analytics: {len(consumption_df)} consumption records, {len(forecast_df)} forecasts, {len(recommendations_df)} recommendations', 'success')
        else:
            flash(f'✅ Successfully uploaded {file_type.replace("_", " ")} data!', 'success')
        return redirect('/upload')
        
    except Exception as e:
        flash(f'Error uploading file: {str(e)}', 'error')
        return redirect('/upload')

@app.route('/api/recalculate', methods=['POST'])
def recalculate():
    """Manually trigger recalculation"""
    try:
        current_engine = app.config.get('engine', engine)
        current_engine.calculate_daily_consumption()
        forecast_df = current_engine.calculate_forecast()
        recommendations_df = current_engine.generate_recommendations()
        
        return jsonify({
            'success': True,
            'message': f'Recalculated: {len(forecast_df)} forecasts, {len(recommendations_df)} recommendations'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/run_audit', methods=['POST'])
def run_audit():
    """Manually trigger audit"""
    try:
        current_engine = app.config.get('engine', engine)
        audit_report = current_engine.auditor.run_audit()
        
        return jsonify({
            'success': True,
            'message': 'Audit completed successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download/audit_csv')
def download_audit_csv():
    """Download audit results as CSV"""
    try:
        current_engine = app.config.get('engine', engine)
        audit_file = current_engine.auditor.audit_results_file
        
        if os.path.exists(audit_file):
            return send_file(audit_file, as_attachment=True, 
                           download_name=f'audit_results_{datetime.now().strftime("%Y%m%d")}.csv')
        else:
            return jsonify({'error': 'Audit results file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def open_browser():
    """Open web browser after a short delay"""
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()

if __name__ == '__main__':
    print("🚀 Starting Cafe Manager...")
    print("📊 Inventory Analytics System")
    print("🔗 Opening web interface at http://localhost:5000")
    
    # Open browser automatically
    open_browser()
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)