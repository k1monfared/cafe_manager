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

@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    """Handle CSV file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        file_type = request.form.get('file_type')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file_type:
            return jsonify({'success': False, 'error': 'File type not specified'})
        
        # Read CSV content
        content = file.read().decode('utf-8')
        
        # Save to appropriate file
        if file_type == 'stock_levels':
            current_engine = app.config.get('engine', engine)
            file_path = current_engine.stock_file
        elif file_type == 'deliveries':
            file_path = current_engine.delivery_file
        elif file_type == 'item_info':
            file_path = current_engine.item_info_file
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'})
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Recalculate everything if it's stock or delivery data
        if file_type in ['stock_levels', 'deliveries']:
            current_engine.calculate_daily_consumption()
            current_engine.calculate_forecast()
            current_engine.generate_recommendations()
        
        return jsonify({'success': True, 'message': f'Successfully uploaded {file_type} data'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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