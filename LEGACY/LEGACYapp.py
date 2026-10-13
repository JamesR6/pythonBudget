from flask import Flask, render_template, request
import sqlite3

from app import create_app
app = create_app()

@app.route('/', methods=['GET', 'POST'])
def dashboard():

    # Initiate database
    path = "./months/y26/august.db"
    
    con = sqlite3.connect(path)
    cur = con.cursor()

    # Get filename
    startIndex = path.rindex("/") + 1
    endIndex = path.rindex(".")
    yearStartIndex = path.rindex("/") - 2
    yearEndIndex = path.rindex("/")
    filename = path[startIndex:endIndex].upper() + " 20" + path[yearStartIndex:yearEndIndex]


    if request.method == 'POST':
        # Gather form info
        day = request.form.get('day')
        transactionType = request.form.get('type')
        amount = request.form.get('amount')
        notes = request.form.get('notes')
        cash = request.form.get('cash')

        # Gather data to remove elements
        removePurchase = request.form.get('removePurchase')
        removeFood = request.form.get('removeFood')
        removeCash = request.form.get('removeCash')

        # Remove elements if requested
        if(removePurchase != None):
            cur.execute("DELETE FROM purchases WHERE id = ?", (removePurchase,))
        if(removeFood != None):
            cur.execute("DELETE FROM transfer WHERE id = ?", (removeFood,))
        if(removeCash != None):
            cur.execute("DELETE FROM cash WHERE id = ?", (removeCash,))

        # Add elements if requested
        if(cash != None):
            cur.execute("INSERT INTO cash(amount) VALUES (?)", (cash,))
        elif(transactionType == "spent"):
            cur.execute("INSERT INTO purchases(day, amount, notes) VALUES (?,?,?)", [ day, amount, notes])
        elif(transactionType == "food"):
            cur.execute("INSERT INTO transfer(day, amount, notes) VALUES (?,?,?)", [ day, amount, notes])
            

        # Commit to database
        con.commit()



# Monthly limit
    limit = 1000

# PURCHASES
    # Gather sum spent
    cur.execute("SELECT SUM(amount) FROM purchases")
    try:
        totalSpent=round(cur.fetchone()[0], 2)
    except:
        totalSpent = 0

    # Math sum spent
    forHard = totalSpent
    totalLeft = round(limit - totalSpent, 2)



# FOOD
    # Gather sum FOOD
    cur.execute("SELECT SUM(amount) FROM transfer")
    try:
        totalFood = round(cur.fetchone()[0], 2)
    except:
        totalFood = 0

 
# CASH
    cur.execute("SELECT SUM(amount) FROM cash")
    try:
        totalCash = cur.fetchone()[0]
    except:
        totalCash = 0


# Gather actual table rows from database
    cur.execute("SELECT * FROM purchases")
    purchaseRows = cur.fetchall()

    cur.execute("SELECT * FROM transfer")
    foodRows = cur.fetchall()

    cur.execute("SELECT * FROM cash")
    cashRows = cur.fetchall()[::-1]

# Close database
    con.close()

# Return variables
    return render_template('index.html', 
    filename = filename,
    totalSpent = totalSpent, 
    totalFood = totalFood, 
    totalCash = totalCash, 
    totalLeft = totalLeft,
    purchaseRows = purchaseRows, 
    foodRows = foodRows, 
    cashRows = cashRows
    )




if __name__ == '__main__':
    app.run(debug=True)