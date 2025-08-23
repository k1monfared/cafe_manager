# Cafe Supply Management - Data Structure Design

## Core Data Entities

### 1. Inventory Items
- **item_id**: Unique identifier
- **name**: Item name (e.g., "Colombian Medium Roast Beans")
- **category**: Type of item (beans, dairy, supplies, food, equipment)
- **subcategory**: More specific grouping (arabica_beans, whole_milk, paper_cups)
- **unit**: Unit of measurement (lbs, gallons, boxes, pieces)
- **current_stock**: Current quantity on hand
- **min_threshold**: Minimum stock level before reordering
- **max_capacity**: Maximum storage capacity
- **cost_per_unit**: Current cost per unit
- **supplier_id**: Reference to supplier
- **lead_time_days**: Days from order to delivery
- **shelf_life_days**: How long item stays fresh
- **storage_requirements**: Temperature, humidity, etc.

### 2. Suppliers
- **supplier_id**: Unique identifier
- **name**: Supplier name
- **contact_info**: Phone, email, address
- **lead_time_days**: Typical delivery time
- **minimum_order**: Minimum order requirements
- **payment_terms**: Net 30, etc.
- **reliability_rating**: 1-5 scale

### 3. Usage Records
- **date**: Date of usage
- **item_id**: Reference to inventory item
- **quantity_used**: Amount consumed
- **waste_amount**: Amount wasted/spilled
- **notes**: Special circumstances
- **sales_volume**: Number of drinks/items sold that day

### 4. Order History
- **order_id**: Unique identifier
- **order_date**: When order was placed
- **supplier_id**: Who we ordered from
- **delivery_date**: When order arrived
- **total_cost**: Total order value
- **status**: pending, delivered, partial, cancelled

### 5. Order Line Items
- **order_id**: Reference to order
- **item_id**: What was ordered
- **quantity_ordered**: How much ordered
- **quantity_received**: How much actually delivered
- **unit_cost**: Cost per unit for this order
- **line_total**: Total cost for this line item

### 6. Forecasting Patterns
- **item_id**: Reference to inventory item
- **day_of_week**: Monday = 1, Sunday = 7
- **average_usage**: Typical daily usage for this day
- **seasonal_multiplier**: Adjustment for time of year
- **trend_factor**: Growth/decline trend
- **last_updated**: When pattern was calculated

## Key Relationships

1. **Ordering Frequency Analysis**
   - Calculate days between orders for each item
   - Track consistency of ordering patterns
   - Identify seasonal variations

2. **Usage Prediction**
   - Daily usage * days until next planned order
   - Adjust for day-of-week patterns
   - Account for seasonal trends
   - Buffer for uncertainty

3. **Stock Level Monitoring**
   - Current stock - predicted usage = projected stock
   - Alert when projected stock < minimum threshold
   - Consider lead time in calculations

## Google Sheets Templates Structure

### Sheet 1: "Current_Inventory"
| Item_Name | Category | Unit | Current_Stock | Min_Threshold | Cost_Per_Unit | Supplier | Last_Updated |

### Sheet 2: "Daily_Usage"
| Date | Item_Name | Quantity_Used | Waste | Sales_Count | Notes |

### Sheet 3: "Order_History"
| Order_Date | Supplier | Item_Name | Quantity | Unit_Cost | Total_Cost | Delivery_Date |

### Sheet 4: "Suppliers"
| Supplier_Name | Contact_Phone | Contact_Email | Lead_Time_Days | Min_Order_Value | Notes |

## Data Validation Rules

1. Quantities must be positive numbers
2. Dates must be in valid format
3. Cost values must be positive
4. Stock levels cannot go negative without warning
5. Usage patterns should flag unusual spikes