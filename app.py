from flask import Flask, render_template, request
import sqlite3;
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():

    # Initiate database
    filename = "december.db"
    con = sqlite3.connect(filename)
    cur = con.cursor()

    if request.method == 'POST':
        # Gather form info
        day = request.form.get('day')
        transactionType = request.form.get('type')
        amount = request.form.get('amount')
        notes = request.form.get('notes')
        debit = request.form.get('debit')

        # Gather data to remove elements
        removePurchase = request.form.get('removePurchase')
        removeTransfer = request.form.get('removeTransfer')
        removeDebit = request.form.get('removeDebit')

        # Remove elements if requested
        if(removePurchase != None):
            cur.execute("DELETE FROM purchases WHERE id = ?", (removePurchase,))
        if(removeTransfer != None):
            cur.execute("DELETE FROM transfer WHERE id = ?", (removeTransfer,))
        if(removeDebit != None):
            cur.execute("DELETE FROM debit WHERE id = ?", (removeDebit,))

        # Add elements if requested
        if(debit != None):
            cur.execute("INSERT INTO debit(amount) VALUES (?)", (debit,))
        elif(transactionType == "spent"):
            cur.execute("INSERT INTO purchases(day, amount, notes) VALUES (?,?,?)", [ day, amount, notes])
        elif(transactionType == "gained"):
            cur.execute("INSERT INTO payback(day, amount, notes) VALUES (?,?,?)", [ day, amount, notes]) 
        elif(transactionType == "transfer"):
            cur.execute("INSERT INTO transfer(day, amount) VALUES (?,?)", [ day, amount])

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

# AVERAGES
    # Gather days entered
    cur.execute("SELECT COUNT(*) FROM purchases")
    days = round(cur.fetchone()[0])
    if(days==0): days=1
    if(days>30): days=30

    # Math averages
    dailyAverage = round(totalSpent/days, 2)
    futureAverage = round(totalLeft/(31-days), 2)
    leftWith = limit - round(dailyAverage*31)

# TRANSFERRED
    # Gather sum transferred
    cur.execute("SELECT SUM(amount) FROM transfer")
    try:
        totalTransferred = round(cur.fetchone()[0], 2)
    except:
        totalTransferred = 0

    # Math transferred
    hardTotalSpent = round(forHard + totalTransferred, 2)
    hardTotalLeft = round(limit - hardTotalSpent, 2)
 
# DEBIT
    cur.execute("SELECT SUM(amount) FROM debit")
    try:
        totalDebit = cur.fetchone()[0]
    except:
        totalDebit = 0


# Gather actual table rows from database
    cur.execute("SELECT * FROM purchases")
    purchaseRows = cur.fetchall()

    cur.execute("SELECT * FROM transfer")
    transferRows = cur.fetchall()

    cur.execute("SELECT * FROM debit")
    debitRows = cur.fetchall()[::-1]

# Close database
    con.close()

# Return variables
    return render_template('index.html', 
    filename = filename,
    totalSpent = totalSpent, 
    amtTrans = totalTransferred, 
    debit = totalDebit, 
    totalLeft = totalLeft, 
    hts = hardTotalSpent, 
    htl = hardTotalLeft, 
    average = dailyAverage, 
    fAverage = futureAverage, 
    leftWith=  leftWith, 
    purchases = purchaseRows, 
    transfer = transferRows, 
    debitList = debitRows)




if __name__ == '__main__':
    app.run(debug=True)