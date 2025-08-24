#!/usr/bin/env python3
"""
Simplified Inventory Management Web Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import pandas as pd
from datetime import datetime, timedelta
from inventory_engine import InventoryEngine
import json
import os

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

@app.route('/stock_entry')
def stock_entry():
    """Stock entry form"""
    try:
        current_engine = app.config.get('engine', engine)
        item_info_df = current_engine.load_item_info()
        items = item_info_df['Item_Name'].tolist() if not item_info_df.empty else []
        
        return render_template('stock_entry.html', items=items)
    except Exception as e:
        flash(f'Error loading stock entry: {str(e)}', 'error')
        return render_template('stock_entry.html', items=[])

@app.route('/api/add_stock', methods=['POST'])
def add_stock():
    """Add stock entry via API"""
    try:
        data = request.json
        date = data.get('date')
        item_name = data.get('item_name')
        current_stock = float(data.get('current_stock', 0))
        
        if not date or not item_name:
            return jsonify({'success': False, 'error': 'Date and item name are required'})
        
        current_engine = app.config.get('engine', engine)
        success = current_engine.add_stock_entry(date, item_name, current_stock)
        
        if success:
            return jsonify({'success': True, 'message': f'Added stock entry for {item_name}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to add stock entry'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
        
        # Load forecast results
        forecast_data = []
        try:
            forecast_df = pd.read_csv(current_engine.forecast_file)
            if not forecast_df.empty:
                for _, row in forecast_df.iterrows():
                    # Parse chart data - handle NaN values and convert to string
                    chart_dates_raw = str(row['Chart_Dates']) if pd.notna(row['Chart_Dates']) else ''
                    chart_consumption_raw = str(row['Chart_Consumption']) if pd.notna(row['Chart_Consumption']) else ''
                    
                    chart_dates = chart_dates_raw.split('|') if chart_dates_raw else []
                    chart_consumption = [float(x) for x in chart_consumption_raw.split('|')] if chart_consumption_raw else []
                    
                    forecast_data.append({
                        'item_name': row['Item_Name'],
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
                        'chart_consumption': chart_consumption
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
        
        return render_template('analytics.html', 
                             forecast_data=forecast_data,
                             recommendations=recommendations_data)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('analytics.html', forecast_data=[], recommendations=[])

@app.route('/upload')
def upload_page():
    """CSV upload page"""
    return render_template('upload.html')

@app.route('/audit')
def audit_page():
    """Comprehensive audit page showing 14-day history, consumption rates, and forecasts"""
    try:
        # Use test engine if in testing mode
        current_engine = app.config.get('engine', engine)
        
        # Load all data
        stock_df = current_engine.load_stock_data()
        item_info_df = current_engine.load_item_info()
        
        # Load consumption data (calculated by engine)
        consumption_df = pd.DataFrame()
        try:
            consumption_df = pd.read_csv(current_engine.consumption_file)
        except FileNotFoundError:
            pass
        
        audit_data = []
        
        if not stock_df.empty and not item_info_df.empty:
            from datetime import datetime, timedelta
            
            for item_name in item_info_df['Item_Name']:
                item_stock_data = stock_df[stock_df['Item_Name'] == item_name].copy()
                item_consumption_data = consumption_df[consumption_df['Item_Name'] == item_name].copy() if not consumption_df.empty else pd.DataFrame()
                item_info = item_info_df[item_info_df['Item_Name'] == item_name].iloc[0]
                
                if not item_stock_data.empty:
                    # Convert dates and sort
                    item_stock_data['Date'] = pd.to_datetime(item_stock_data['Date'])
                    item_stock_data = item_stock_data.sort_values('Date')
                    
                    # Get last 14 days or all available data
                    recent_data = item_stock_data.tail(14)
                    
                    # Get consumption data for the same period
                    consumption_values = []
                    if not item_consumption_data.empty:
                        item_consumption_data['Date'] = pd.to_datetime(item_consumption_data['Date'])
                        consumption_values = item_consumption_data['Consumption'].tolist()[-13:]  # Last 13 days (14 stock points = 13 consumption days)
                    
                    # Calculate average consumption rate
                    avg_consumption = sum(consumption_values) / len(consumption_values) if consumption_values else 0
                    
                    # Prepare chart data
                    dates = [d.strftime('%Y-%m-%d') for d in recent_data['Date']]
                    stock_levels = recent_data['Current_Stock'].tolist()
                    
                    audit_data.append({
                        'item_name': item_name,
                        'unit': item_info['Unit'],
                        'current_stock': recent_data.iloc[-1]['Current_Stock'] if not recent_data.empty else 0,
                        'min_threshold': item_info['Min_Threshold'],
                        'max_capacity': item_info['Max_Capacity'],
                        'avg_consumption': avg_consumption,
                        'data_points': len(recent_data),
                        'dates': dates,
                        'stock_levels': stock_levels,
                        'consumption_data': consumption_values,
                        'date_range': f"{dates[0]} to {dates[-1]}" if dates else "No data"
                    })
        
        # Load forecast data for comparison
        forecast_data = []
        try:
            forecast_df = pd.read_csv(current_engine.forecast_file)
            if not forecast_df.empty:
                forecast_data = forecast_df.to_dict('records')
        except FileNotFoundError:
            pass
        
        return render_template('audit.html', 
                             audit_data=audit_data,
                             forecast_data=forecast_data)
    except Exception as e:
        flash(f'Error loading audit data: {str(e)}', 'error')
        return render_template('audit.html', audit_data=[], forecast_data=[])

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
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Recalculate everything if it's stock or delivery data
        if file_type in ['stock_levels', 'deliveries']:
            current_engine.calculate_daily_consumption()
            current_engine.calculate_forecast()
            current_engine.generate_recommendations()
        
        flash(f'Successfully uploaded {file_type.replace("_", " ")} data and recalculated forecasts!', 'success')
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)