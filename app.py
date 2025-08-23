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
from scripts.sheets_sync import SheetsSync
from werkzeug.utils import secure_filename
from scripts.google_drive_integration import GoogleDriveIntegration
from scripts.sync_scheduler import get_scheduler
from scripts.usage_calculator import UsageCalculator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cafe-supply-manager-2025'
app.config['UPLOAD_FOLDER'] = 'google_sheets_data'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize forecasting engine, sheets sync, Google Drive, scheduler, and usage calculator
forecast_engine = ForecastingEngine()
sheets_sync = SheetsSync()
google_drive = GoogleDriveIntegration()
sync_scheduler = get_scheduler()
usage_calculator = UsageCalculator("data/sample_data")

def process_daily_inventory_upload(csv_file_path):
    """Process uploaded daily inventory CSV using master CSV as source of truth"""
    import csv
    import pandas as pd
    
    try:
        print(f"📄 Processing uploaded CSV file...")
        
        # Step 1: Load uploaded CSV and clean it
        uploaded_df = pd.read_csv(csv_file_path)
        
        # Skip instruction rows if any
        uploaded_df = uploaded_df[~uploaded_df['Date'].astype(str).str.contains('📝', na=False)]
        uploaded_df = uploaded_df[~uploaded_df['Date'].astype(str).str.contains('INSTRUCTIONS', na=False)]
        
        # Clean and validate uploaded data
        clean_uploaded_data = []
        processed_count = 0
        
        for _, row in uploaded_df.iterrows():
            try:
                date_str = str(row['Date']).strip()
                item_name = str(row['Item_Name']).strip()
                
                # Skip invalid rows
                if not date_str or not item_name or date_str == 'nan' or item_name == 'nan':
                    continue
                
                # Parse numeric values
                current_stock = float(row.get('Current_Stock', 0))
                waste_amount = float(row.get('Waste_Amount', 0))
                deliveries_received = float(row.get('Deliveries_Received', 0))
                notes = str(row.get('Notes', '')).strip()
                
                clean_uploaded_data.append({
                    'Date': date_str,
                    'Item_Name': item_name,
                    'Current_Stock': current_stock,
                    'Waste_Amount': waste_amount,
                    'Deliveries_Received': deliveries_received,
                    'Notes': notes
                })
                processed_count += 1
                
            except (ValueError, TypeError) as e:
                print(f"⚠️  Warning: Invalid data in row, skipping: {e}")
                continue
        
        if processed_count == 0:
            return {
                'success': False,
                'error': 'No valid data found in uploaded file'
            }
        
        print(f"✅ Cleaned {processed_count} valid entries from upload")
        
        # Step 2: Load master CSV file (create if doesn't exist)
        master_csv_path = 'data/daily_inventory_master.csv'
        
        try:
            master_df = pd.read_csv(master_csv_path)
        except FileNotFoundError:
            # Create master CSV with headers if it doesn't exist
            master_df = pd.DataFrame(columns=['Date', 'Item_Name', 'Current_Stock', 'Waste_Amount', 'Deliveries_Received', 'Notes'])
            print("📝 Created new master CSV file")
        
        # Step 3: Smart merge - remove conflicts and append new data
        uploaded_keys = {(row['Date'], row['Item_Name']) for row in clean_uploaded_data}
        
        # Remove existing entries that conflict with uploaded data
        master_df_filtered = master_df[~master_df.apply(lambda x: (x['Date'], x['Item_Name']) in uploaded_keys, axis=1)]
        
        conflicts_resolved = len(master_df) - len(master_df_filtered)
        
        # Append new data
        uploaded_df_clean = pd.DataFrame(clean_uploaded_data)
        master_df_updated = pd.concat([master_df_filtered, uploaded_df_clean], ignore_index=True)
        
        # Sort by date and item name for consistency
        master_df_updated = master_df_updated.sort_values(['Date', 'Item_Name']).reset_index(drop=True)
        
        # Step 4: Save updated master CSV
        master_df_updated.to_csv(master_csv_path, index=False)
        print(f"💾 Updated master CSV: {len(master_df_updated)} total entries ({conflicts_resolved} conflicts resolved)")
        
        # Step 5: Generate JSON files from master CSV
        json_result = generate_json_from_master_csv(master_csv_path)
        
        if not json_result['success']:
            return {
                'success': False,
                'error': f'Failed to generate JSON files: {json_result["error"]}'
            }
        
        # Step 6: Update templates to stay current
        update_csv_templates_from_master()
        
        # Step 7: Reload forecasting engine
        global forecast_engine
        forecast_engine = ForecastingEngine()
        
        print("🎉 Successfully completed full CSV-first workflow")
        
        return {
            'success': True,
            'message': 'Successfully processed daily inventory update',
            'details': {
                'processed_entries': processed_count,
                'conflicts_resolved': conflicts_resolved,
                'total_entries': len(master_df_updated),
                'items_updated': json_result['items_updated'],
                'master_csv_path': master_csv_path
            }
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Error in process_daily_inventory_upload: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }

def generate_json_from_master_csv(master_csv_path):
    """Generate all JSON files from the master CSV file"""
    import pandas as pd
    
    try:
        # Load master CSV
        master_df = pd.read_csv(master_csv_path)
        
        # Load inventory items to get item mapping
        items_path = 'data/sample_data/inventory_items.json'
        with open(items_path, 'r') as f:
            inventory_items = json.load(f)
        
        # Create name to item_id mapping
        name_to_id = {}
        id_to_item = {}
        for item in inventory_items:
            name_to_id[item['name']] = item['item_id']
            id_to_item[item['item_id']] = item
        
        # Generate inventory snapshots
        snapshots = []
        unknown_items = set()
        
        for _, row in master_df.iterrows():
            item_name = row['Item_Name']
            item_id = name_to_id.get(item_name)
            
            if not item_id:
                unknown_items.add(item_name)
                continue
            
            snapshot = {
                "date": row['Date'],
                "item_id": item_id,
                "stock_level": float(row['Current_Stock']),
                "waste_amount": float(row['Waste_Amount']),
                "deliveries_received": float(row['Deliveries_Received']),
                "notes": str(row['Notes'])
            }
            snapshots.append(snapshot)
        
        if unknown_items:
            print(f"⚠️  Warning: Unknown items in CSV: {', '.join(unknown_items)}")
        
        # Save inventory snapshots
        snapshots_path = 'data/sample_data/inventory_snapshots.json'
        with open(snapshots_path, 'w') as f:
            json.dump(snapshots, f, indent=2)
        
        # Update inventory items with latest stock levels
        latest_stocks = {}
        for snapshot in snapshots:
            key = snapshot['item_id']
            if key not in latest_stocks or snapshot['date'] > latest_stocks[key]['date']:
                latest_stocks[key] = snapshot
        
        items_updated = 0
        for item in inventory_items:
            if item['item_id'] in latest_stocks:
                old_stock = item['current_stock']
                item['current_stock'] = latest_stocks[item['item_id']]['stock_level']
                if old_stock != item['current_stock']:
                    items_updated += 1
                    print(f"📦 Updated {item['name']}: {old_stock} → {item['current_stock']}")
        
        # Save updated inventory items
        with open(items_path, 'w') as f:
            json.dump(inventory_items, f, indent=2)
        
        # Generate daily usage from snapshots (if usage calculator available)
        try:
            usage_calculator.load_data()
            calculated_usage = usage_calculator.calculate_usage_from_snapshots()
            usage_data = usage_calculator.export_calculated_usage_to_daily_usage_format()
            
            usage_path = 'data/sample_data/daily_usage.json'
            with open(usage_path, 'w') as f:
                json.dump(usage_data, f, indent=2)
            
            print("📊 Generated daily usage patterns")
        except Exception as e:
            print(f"⚠️  Usage calculation failed: {e}")
        
        print(f"✅ Generated JSON files from master CSV ({len(snapshots)} snapshots, {items_updated} items updated)")
        
        return {
            'success': True,
            'snapshots_count': len(snapshots),
            'items_updated': items_updated,
            'unknown_items': list(unknown_items)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def update_csv_templates_from_master():
    """Update CSV templates using data from master CSV"""
    try:
        # Copy master CSV to templates
        master_csv_path = 'data/daily_inventory_master.csv'
        
        template_paths = [
            'templates/csv_templates/daily_inventory_template.csv',
            'google_sheets_templates/daily_inventory_template.csv'
        ]
        
        import shutil
        for template_path in template_paths:
            shutil.copy2(master_csv_path, template_path)
            print(f"📋 Updated template: {template_path}")
        
        # Also update current inventory template with latest stock levels
        items_path = 'data/sample_data/inventory_items.json'
        with open(items_path, 'r') as f:
            inventory_items = json.load(f)
        
        # Update current inventory templates
        current_template_paths = [
            'templates/csv_templates/current_inventory_template.csv',
            'google_sheets_templates/current_inventory_template.csv'
        ]
        
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        
        for template_path in current_template_paths:
            try:
                import pandas as pd
                
                # Read existing template to preserve headers and instructions
                try:
                    template_df = pd.read_csv(template_path)
                    # Keep instruction row
                    instruction_rows = template_df[template_df['Item_Name'].astype(str).str.contains('📝', na=False)]
                except:
                    instruction_rows = pd.DataFrame()
                
                # Create updated data rows
                data_rows = []
                for item in inventory_items:
                    if item['item_id'] != 'ITEM001':  # Skip instruction item
                        data_rows.append({
                            'Item_Name': item['name'],
                            'Category': item['category'],
                            'Unit': item['unit'],
                            'Current_Stock': item['current_stock'],
                            'Min_Threshold': item['min_threshold'],
                            'Max_Capacity': item['max_capacity'],
                            'Cost_Per_Unit': item['cost_per_unit'],
                            'Supplier': 'Various',  # Simplified
                            'Lead_Time_Days': item['lead_time_days'],
                            'Shelf_Life_Days': item['shelf_life_days'],
                            'Storage_Requirements': item['storage_requirements'],
                            'Last_Updated': today
                        })
                
                # Combine instruction and data
                updated_df = pd.concat([instruction_rows, pd.DataFrame(data_rows)], ignore_index=True)
                updated_df.to_csv(template_path, index=False)
                
            except Exception as e:
                print(f"⚠️  Warning: Could not update {template_path}: {e}")
        
        print("✅ Templates synchronized with master data")
        
    except Exception as e:
        print(f"⚠️  Warning: Template update failed: {e}")

def update_csv_templates_from_json(date, inventory_snapshot):
    """Update CSV templates with latest data from daily inventory snapshots"""
    import csv
    
    # Update daily_inventory_template.csv with the new snapshot data
    daily_template_path = 'templates/csv_templates/daily_inventory_template.csv'
    
    try:
        # Read existing daily inventory template
        rows = []
        with open(daily_template_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Keep header and instruction rows
            for row in reader:
                if '📝 INSTRUCTIONS' in row.get('Date', ''):
                    rows.append(row)
                elif row.get('Date') != date:  # Keep other dates
                    rows.append(row)
        
        # Add the new snapshot data
        with open('data/sample_data/inventory_items.json', 'r') as f:
            items = json.load(f)
        
        items_dict = {item['item_id']: item for item in items}
        
        for snapshot in inventory_snapshot:
            item_id = snapshot['item_id']
            if item_id in items_dict and item_id != 'ITEM001':  # Skip template row
                item = items_dict[item_id]
                rows.append({
                    'Date': date,
                    'Item_Name': item['name'],
                    'Current_Stock': str(snapshot['stock_level']),
                    'Waste_Amount': str(snapshot.get('waste_amount', 0)),
                    'Deliveries_Received': str(snapshot.get('deliveries_received', 0)),
                    'Notes': snapshot.get('notes', '')
                })
        
        # Write updated daily inventory template
        with open(daily_template_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
    except Exception as e:
        print(f"Error updating daily inventory template: {e}")
    
    # Update current_inventory_template.csv with latest stock levels
    current_template_path = 'templates/csv_templates/current_inventory_template.csv'
    
    try:
        # Read existing current inventory template
        rows = []
        with open(current_template_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                if '📝 INSTRUCTIONS' in row.get('Item_Name', ''):
                    rows.append(row)  # Keep instruction row
                else:
                    # Update stock levels with latest data
                    item_name = row.get('Item_Name', '')
                    updated = False
                    
                    with open('data/sample_data/inventory_items.json', 'r') as f:
                        items = json.load(f)
                    
                    for item in items:
                        if item['name'] == item_name and item['item_id'] != 'ITEM001':
                            row['Current_Stock'] = str(item['current_stock'])
                            row['Last_Updated'] = date
                            updated = True
                            break
                    
                    rows.append(row)
        
        # Write updated current inventory template
        with open(current_template_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
    except Exception as e:
        print(f"Error updating current inventory template: {e}")
    
    # Also update Google Sheets templates folder
    try:
        import shutil
        
        # Copy updated templates to Google Sheets templates folder
        shutil.copy(daily_template_path, 'google_sheets_templates/daily_inventory_template.csv')
        shutil.copy(current_template_path, 'google_sheets_templates/current_inventory_template.csv')
        
        print("Synchronized Google Sheets templates")
        
    except Exception as e:
        print(f"Error updating Google Sheets templates: {e}")

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

@app.route('/api/upload_daily_inventory', methods=['POST'])
def upload_daily_inventory():
    """Upload and automatically process daily inventory CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Save uploaded file temporarily
        temp_filename = f"temp_daily_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        temp_file_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_file_path)
        
        # Process the upload: merge, calculate, and update everything automatically
        result = process_daily_inventory_upload(temp_file_path)
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    """Legacy upload endpoint - redirects to daily inventory for compatibility"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file_type = request.form.get('file_type', 'daily_inventory')
        
        # For daily inventory or usage, use the new automated flow
        if file_type in ['usage', 'daily_inventory']:
            return upload_daily_inventory()
        
        # For other file types, use original logic
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Map file types to expected filenames
        filename_map = {
            'inventory': 'current_inventory.csv',
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

@app.route('/api/download_template/<template_type>')
def download_template(template_type):
    """Download CSV templates"""
    if template_type == 'master_csv':
        # Special case: download the master CSV file
        master_csv_path = 'data/daily_inventory_master.csv'
        if not os.path.exists(master_csv_path):
            return jsonify({'error': 'Master CSV file not found'}), 404
        return send_file(master_csv_path, as_attachment=True, download_name='daily_inventory_master.csv')
    
    template_map = {
        'current_inventory': 'current_inventory_template.csv',
        'daily_inventory': 'daily_inventory_template.csv',
        'order_history': 'order_history_template.csv',
        'suppliers': 'suppliers_template.csv'
    }
    
    if template_type not in template_map:
        return jsonify({'error': 'Invalid template type'}), 400
    
    filename = template_map[template_type]
    file_path = os.path.join('templates', 'csv_templates', filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Template file not found'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/api/regenerate_json', methods=['POST'])
def regenerate_json():
    """Regenerate all JSON files from master CSV"""
    try:
        master_csv_path = 'data/daily_inventory_master.csv'
        if not os.path.exists(master_csv_path):
            return jsonify({
                'success': False,
                'error': 'Master CSV file not found'
            })
        
        result = generate_json_from_master_csv(master_csv_path)
        
        if result['success']:
            # Reload forecasting engine
            global forecast_engine
            forecast_engine = ForecastingEngine()
            
            return jsonify({
                'success': True,
                'message': 'Successfully regenerated JSON files from master CSV',
                'details': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to regenerate JSON: {str(e)}'
        })

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

# New Daily Inventory Routes
@app.route('/daily-inventory')
def daily_inventory_page():
    """Daily inventory entry page"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Get last inventory date
    try:
        with open('data/sample_data/inventory_snapshots.json', 'r') as f:
            snapshots = json.load(f)
        last_date = max([s['date'] for s in snapshots]) if snapshots else None
    except:
        last_date = None
    
    return render_template('daily_inventory.html', today_date=today, last_inventory_date=last_date)

@app.route('/api/inventory_snapshot/<date>')
def get_inventory_snapshot(date):
    """Get inventory snapshot for a specific date"""
    try:
        usage_calculator.load_data()
        snapshots = [s for s in usage_calculator.inventory_snapshots if s.get('date') == date]
        
        return jsonify({
            'success': True,
            'snapshot': snapshots
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_inventory_snapshot', methods=['POST'])
def save_inventory_snapshot():
    """Save daily inventory snapshot and calculate usage"""
    try:
        print("=== Save Inventory Snapshot Called ===")
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'})
        
        date = data.get('date')
        inventory = data.get('inventory', [])
        deliveries = data.get('deliveries', [])
        
        print(f"Date: {date}, Inventory items: {len(inventory)}, Deliveries: {len(deliveries)}")
        
        if not date:
            return jsonify({'success': False, 'error': 'Date is required'})
        
        if not inventory:
            return jsonify({'success': False, 'error': 'Inventory data is required'})
        
        # Save inventory snapshot
        usage_calculator.load_data()
        print("UsageCalculator loaded successfully")
        
        success = usage_calculator.add_inventory_snapshot(date, inventory)
        print(f"Inventory snapshot save result: {success}")
        
        if not success:
            return jsonify({'success': False, 'error': 'Failed to save inventory snapshot'})
        
        # Process any deliveries by creating order records
        if deliveries:
            print(f"Processing {len(deliveries)} deliveries")
            # Load existing order history
            try:
                with open('data/sample_data/order_history.json', 'r') as f:
                    order_history = json.load(f)
            except:
                order_history = []
            
            # Create delivery orders
            for delivery in deliveries:
                order_id = f"DEL-{date}-{len(order_history) + 1:03d}"
                order_record = {
                    "order_id": order_id,
                    "order_date": date,
                    "supplier_id": delivery['supplier_id'],
                    "delivery_date": date,
                    "total_cost": 0.0,  # Would need item pricing
                    "status": "delivered",
                    "line_items": [{
                        "item_id": delivery['item_id'],
                        "quantity_ordered": delivery['quantity'],
                        "quantity_received": delivery['quantity'],
                        "unit_cost": 0.0,  # Would need pricing
                        "line_total": 0.0
                    }]
                }
                order_history.append(order_record)
            
            # Save updated order history
            with open('data/sample_data/order_history.json', 'w') as f:
                json.dump(order_history, f, indent=2)
            print(f"Saved {len(deliveries)} deliveries to order history")
        
        # Calculate usage from snapshots and update daily_usage.json
        print("Calculating usage from snapshots...")
        records_updated = usage_calculator.update_daily_usage_file()
        print(f"Updated {records_updated} usage records")
        
        # Update inventory_items.json current_stock with latest snapshot data
        try:
            print("Synchronizing inventory_items.json with latest snapshot...")
            with open('data/sample_data/inventory_items.json', 'r') as f:
                inventory_items = json.load(f)
            
            # Update current_stock from the latest inventory snapshot
            for item_data in inventory:
                for item in inventory_items:
                    if item['item_id'] == item_data['item_id']:
                        old_stock = item['current_stock']
                        item['current_stock'] = item_data['stock_level']
                        print(f"Updated {item['name']} current_stock: {old_stock} → {item_data['stock_level']}")
                        break
            
            # Save updated inventory_items.json
            with open('data/sample_data/inventory_items.json', 'w') as f:
                json.dump(inventory_items, f, indent=2)
            
            print("Successfully synchronized inventory_items.json with latest snapshot")
            
        except Exception as e:
            print(f"Warning: Could not update inventory_items.json: {e}")
        
        # Update CSV templates to keep them synchronized
        try:
            print("Synchronizing CSV templates...")
            update_csv_templates_from_json(date, inventory)
            print("Successfully updated CSV templates")
        except Exception as e:
            print(f"Warning: Could not update CSV templates: {e}")
        
        # Refresh forecasting engine with new data
        try:
            global forecast_engine
            forecast_engine = ForecastingEngine()
            print("Forecasting engine refreshed")
        except Exception as e:
            print(f"Warning: Could not refresh forecasting engine: {e}")
            # Don't fail the whole operation if forecasting engine fails
        
        return jsonify({
            'success': True,
            'usage_records_updated': records_updated,
            'deliveries_processed': len(deliveries)
        })
        
    except Exception as e:
        print(f"Error in save_inventory_snapshot: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/inventory_items')
def api_inventory_items():
    """Get inventory items for the daily inventory form"""
    try:
        with open('data/sample_data/inventory_items.json', 'r') as f:
            items = json.load(f)
        return jsonify(items)
    except Exception as e:
        return jsonify({'error': str(e)})

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