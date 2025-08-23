#!/usr/bin/env python3
"""
Cafe Supply Manager - Web Application
Simple, user-friendly interface for managing cafe inventory and orders
"""

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, flash
import os
import json
from datetime import datetime, timedelta
from src.forecasting_engine import ForecastingEngine, OrderRecommendation
from sheets_sync import SheetsSync
from werkzeug.utils import secure_filename
from google_drive_integration import GoogleDriveIntegration
from sync_scheduler import get_scheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cafe-supply-manager-2025'
app.config['UPLOAD_FOLDER'] = 'google_sheets_data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize forecasting engine, sheets sync, Google Drive, and scheduler
forecast_engine = ForecastingEngine()
sheets_sync = SheetsSync()
google_drive = GoogleDriveIntegration()
sync_scheduler = get_scheduler()

@app.route('/')
def dashboard():
    """Main dashboard showing current status"""
    return render_template('dashboard.html')

@app.route('/api/dashboard_data')
def dashboard_data():
    """Get dashboard data as JSON"""
    try:
        # Generate recommendations
        recommendations = forecast_engine.generate_order_recommendations()
        alerts = forecast_engine.get_inventory_alerts()
        
        # Group recommendations by urgency
        urgency_counts = {"critical": 0, "warning": 0, "normal": 0, "stock_up": 0}
        total_cost = 0
        
        for rec in recommendations:
            urgency_counts[rec.urgency_level] += 1
            total_cost += rec.estimated_cost
        
        # Recent orders
        recent_orders = sorted(forecast_engine.order_history, 
                             key=lambda x: x['order_date'], reverse=True)[:5]
        
        # Inventory summary
        total_items = len(forecast_engine.inventory_items)
        low_stock_items = len([item for item in forecast_engine.inventory_items.values() 
                             if item['current_stock'] <= item['min_threshold']])
        
        return jsonify({
            'success': True,
            'urgency_counts': urgency_counts,
            'total_estimated_cost': total_cost,
            'alerts': alerts,
            'recent_orders': recent_orders,
            'inventory_summary': {
                'total_items': total_items,
                'low_stock_items': low_stock_items
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/recommendations')
def recommendations():
    """Order recommendations page"""
    return render_template('recommendations.html')

@app.route('/api/recommendations')
def api_recommendations():
    """Get order recommendations as JSON"""
    try:
        recommendations = forecast_engine.generate_order_recommendations()
        
        # Convert to JSON-serializable format
        rec_data = []
        for rec in recommendations:
            rec_data.append({
                'item_id': rec.item_id,
                'item_name': rec.item_name,
                'current_stock': rec.current_stock,
                'projected_usage': rec.projected_usage,
                'days_until_reorder': rec.days_until_reorder,
                'recommended_quantity': rec.recommended_quantity,
                'urgency_level': rec.urgency_level,
                'reasoning': rec.reasoning,
                'supplier': rec.supplier,
                'estimated_cost': rec.estimated_cost
            })
        
        return jsonify({'success': True, 'recommendations': rec_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/inventory')
def inventory():
    """Current inventory page"""
    return render_template('inventory.html')

@app.route('/api/inventory')
def api_inventory():
    """Get current inventory as JSON"""
    try:
        # Add usage predictions to inventory data
        inventory_with_predictions = []
        for item_id, item in forecast_engine.inventory_items.items():
            predicted_7day = forecast_engine.predict_usage(item_id, 7)
            predicted_14day = forecast_engine.predict_usage(item_id, 14)
            
            # Calculate days until empty
            if predicted_7day > 0:
                daily_usage = predicted_7day / 7
                days_until_empty = item['current_stock'] / daily_usage
            else:
                days_until_empty = 999
            
            item_data = item.copy()
            item_data['predicted_7day_usage'] = predicted_7day
            item_data['predicted_14day_usage'] = predicted_14day
            item_data['days_until_empty'] = min(days_until_empty, 999)
            item_data['supplier_name'] = forecast_engine.suppliers.get(
                item['supplier_id'], {}).get('name', 'Unknown')
            
            inventory_with_predictions.append(item_data)
        
        return jsonify({'success': True, 'inventory': inventory_with_predictions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/usage-analysis')
def usage_analysis():
    """Usage analysis page"""
    return render_template('usage_analysis.html')

@app.route('/api/usage_patterns')
def api_usage_patterns():
    """Get usage patterns analysis"""
    try:
        patterns = forecast_engine.analyze_usage_patterns()
        
        # Convert patterns to JSON-serializable format
        pattern_data = {}
        for item_id, pattern in patterns.items():
            item_name = forecast_engine.inventory_items.get(item_id, {}).get('name', item_id)
            pattern_data[item_id] = {
                'item_name': item_name,
                'daily_averages': pattern.daily_averages,
                'trend_factor': pattern.trend_factor,
                'volatility': pattern.volatility
            }
        
        return jsonify({'success': True, 'patterns': pattern_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/suppliers')
def suppliers():
    """Suppliers management page"""
    return render_template('suppliers.html')

@app.route('/api/suppliers')
def api_suppliers():
    """Get suppliers data"""
    try:
        return jsonify({'success': True, 'suppliers': list(forecast_engine.suppliers.values())})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export_recommendations')
def export_recommendations():
    """Export recommendations to CSV"""
    try:
        recommendations = forecast_engine.generate_order_recommendations()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'order_recommendations_{timestamp}.csv'
        
        forecast_engine.export_recommendations_csv(recommendations, filename)
        
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/help')
def help_page():
    """Help and instructions page"""
    return render_template('help.html')

@app.route('/sheets')
def sheets_sync_page():
    """Google Sheets sync page"""
    return render_template('sheets_sync.html')

@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    """Upload CSV file from Google Sheets"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        file_type = request.form.get('file_type')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file_type:
            return jsonify({'success': False, 'error': 'File type not specified'})
        
        # Map file types to expected filenames
        filename_map = {
            'inventory': 'current_inventory.csv',
            'usage': 'daily_usage.csv',
            'orders': 'order_history.csv',
            'suppliers': 'suppliers.csv'
        }
        
        if file_type not in filename_map:
            return jsonify({'success': False, 'error': 'Invalid file type'})
        
        # Save file with the expected name
        filename = filename_map[file_type]
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {filename}',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sync_sheets', methods=['POST'])
def sync_sheets():
    """Sync all uploaded CSV files to JSON format"""
    try:
        # Perform the sync
        results = sheets_sync.sync_from_sheets()
        
        # Reload the forecasting engine with new data
        global forecast_engine
        forecast_engine = ForecastingEngine()
        
        successful_files = [f for f, success in results.items() if success]
        failed_files = [f for f, success in results.items() if not success]
        
        return jsonify({
            'success': len(successful_files) > 0,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'message': f'Synced {len(successful_files)} files successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sheets_status')
def sheets_status():
    """Check status of uploaded CSV files"""
    try:
        file_status = {}
        expected_files = {
            'current_inventory.csv': 'Inventory Items',
            'daily_usage.csv': 'Daily Usage Records',
            'order_history.csv': 'Order History',
            'suppliers.csv': 'Supplier Information'
        }
        
        for filename, description in expected_files.items():
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                stat = os.stat(file_path)
                file_status[filename] = {
                    'exists': True,
                    'description': description,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                file_status[filename] = {
                    'exists': False,
                    'description': description,
                    'size': 0,
                    'modified': None
                }
        
        return jsonify({'success': True, 'files': file_status})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/google_drive_auth', methods=['POST'])
def google_drive_auth():
    """Set up Google Drive authentication"""
    try:
        success, message = google_drive.setup_credentials()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/google_drive_status')
def google_drive_status():
    """Check Google Drive connection status"""
    try:
        success, message = google_drive.test_connection()
        return jsonify({
            'success': success,
            'message': message,
            'authenticated': success
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': str(e),
            'authenticated': False
        })

@app.route('/api/list_google_sheets')
def list_google_sheets():
    """List all Google Sheets in user's drive"""
    try:
        success, sheets = google_drive.list_spreadsheets()
        return jsonify({
            'success': success,
            'sheets': sheets if success else [],
            'message': 'Failed to list sheets' if not success else ''
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/connect_google_sheet', methods=['POST'])
def connect_google_sheet():
    """Connect a Google Sheet by URL or ID"""
    try:
        data = request.get_json()
        sheet_url = data.get('sheet_url', '').strip()
        file_type = data.get('file_type', '').strip()
        
        if not sheet_url or not file_type:
            return jsonify({'success': False, 'error': 'Sheet URL and file type are required'})
        
        # Extract file ID from URL
        file_id = google_drive.extract_file_id_from_url(sheet_url)
        if not file_id:
            return jsonify({'success': False, 'error': 'Invalid Google Sheets URL'})
        
        # Get sheet info
        info_success, sheet_info = google_drive.get_sheet_info(file_id)
        if not info_success:
            return jsonify({'success': False, 'error': 'Could not access sheet. Check permissions.'})
        
        # Download and save the sheet
        download_success, csv_content, filename = google_drive.download_sheet_as_csv(file_id)
        if not download_success:
            return jsonify({'success': False, 'error': csv_content})  # Error message is in csv_content
        
        # Save to appropriate file
        save_success, save_message = google_drive.save_csv_content(csv_content, file_type)
        if not save_success:
            return jsonify({'success': False, 'error': save_message})
        
        return jsonify({
            'success': True,
            'message': f'Successfully connected and downloaded {sheet_info["name"]}',
            'sheet_info': sheet_info,
            'file_type': file_type
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sync_google_drive_links', methods=['POST'])
def sync_google_drive_links():
    """Sync multiple Google Sheets by their URLs"""
    try:
        data = request.get_json()
        drive_links = data.get('drive_links', {})
        
        if not drive_links:
            return jsonify({'success': False, 'error': 'No drive links provided'})
        
        # Download all sheets
        download_results = google_drive.sync_from_drive_links(drive_links)
        
        # Sync to JSON format
        sync_results = sheets_sync.sync_from_sheets()
        
        # Reload forecasting engine
        global forecast_engine
        forecast_engine = ForecastingEngine()
        
        # Combine results
        successful_downloads = [k for k, v in download_results.items() if v]
        successful_syncs = [k for k, v in sync_results.items() if v]
        
        return jsonify({
            'success': len(successful_downloads) > 0,
            'download_results': download_results,
            'sync_results': sync_results,
            'successful_files': successful_syncs,
            'message': f'Successfully synced {len(successful_syncs)} files from Google Drive'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/drive')
def google_drive_page():
    """Google Drive integration page"""
    return render_template('google_drive.html')

@app.route('/api/auto_sync_status')
def auto_sync_status():
    """Get auto-sync status"""
    try:
        status = sync_scheduler.get_sync_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/enable_auto_sync', methods=['POST'])
def enable_auto_sync():
    """Enable automatic syncing"""
    try:
        data = request.get_json()
        file_urls = data.get('file_urls', {})
        interval_hours = data.get('interval_hours', 24)
        
        if not file_urls:
            return jsonify({'success': False, 'error': 'No file URLs provided'})
        
        # Set up auto-sync
        sync_scheduler.set_auto_sync_files(file_urls)
        sync_scheduler.enable_auto_sync(interval_hours)
        
        return jsonify({
            'success': True,
            'message': f'Auto-sync enabled (every {interval_hours} hours)',
            'files_configured': len(file_urls)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disable_auto_sync', methods=['POST'])
def disable_auto_sync():
    """Disable automatic syncing"""
    try:
        sync_scheduler.disable_auto_sync()
        return jsonify({
            'success': True,
            'message': 'Auto-sync disabled'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🚀 Starting Cafe Supply Manager")
    print("📊 Dashboard: http://localhost:5001")
    print("📋 Recommendations: http://localhost:5001/recommendations")
    print("📦 Inventory: http://localhost:5001/inventory")
    print("📈 Usage Analysis: http://localhost:5001/usage-analysis")
    print("🏢 Suppliers: http://localhost:5001/suppliers")
    print("❓ Help: http://localhost:5001/help")
    print()
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5001)