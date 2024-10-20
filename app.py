from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import datetime
import calendar
import plotly.graph_objs as go
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB Setup
client = MongoClient('mongodb://localhost:27017/')
db = client['expense_tracker_1']
expenses_collection = db['expenses']
settings_collection = db['settings']

# Retrieve or initialize the monthly budget
def get_monthly_budget():
    settings = settings_collection.find_one({'type': 'budget'})
    if settings:
        return settings['amount']
    else:
        # Default budget if not set
        return 1000

def update_monthly_budget(amount):
    settings_collection.update_one({'type': 'budget'}, {'$set': {'amount': amount}}, upsert=True)

# Route for home page
@app.route('/')
def index():
    expenses = list(expenses_collection.find())
    total_expenses = sum(exp['amount'] for exp in expenses)
    categories = get_expense_by_category(expenses)
    
    monthly_budget = get_monthly_budget()
    budget_left = monthly_budget - total_expenses
    
    # Chart data (spending by category)
    labels = list(categories.keys())
    values = list(categories.values())
    
    pie_chart = create_pie_chart(labels, values)

    return render_template('index.html', expenses=expenses, total_expenses=total_expenses,
                           monthly_budget=monthly_budget, budget_left=budget_left,
                           pie_chart=pie_chart)

# Add expense route
@app.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    amount = float(request.form.get('amount'))
    description = request.form.get('description')
    date = datetime.datetime.now().strftime("%Y-%m-%d")

    expense = {
        'category': category,
        'amount': amount,
        'description': description,
        'date': date
    }

    expenses_collection.insert_one(expense)
    return redirect(url_for('index'))

# Delete expense route
@app.route('/delete_expense/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    expenses_collection.delete_one({'_id': ObjectId(expense_id)})
    return redirect(url_for('index'))

# Update budget route
@app.route('/update_budget', methods=['POST'])
def update_budget():
    new_budget = float(request.form.get('budget'))
    update_monthly_budget(new_budget)
    return redirect(url_for('index'))

# Utility function to categorize expenses
def get_expense_by_category(expenses):
    category_totals = {}
    for exp in expenses:
        category = exp['category']
        category_totals[category] = category_totals.get(category, 0) + exp['amount']
    return category_totals

# Create pie chart using Plotly
def create_pie_chart(labels, values):
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    return fig.to_html(full_html=False)

if __name__ == '__main__':
    app.run(debug=True)
