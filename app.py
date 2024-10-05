from flask import Flask, render_template, request
import sqlite3;
app = Flask(__name__)


totalSpent=0

# --------------------------
@app.route('/', methods=['GET', 'POST'])
def hello():
    filename = "august.db"
    con = sqlite3.connect(filename)
    cur = con.cursor()
    if request.method == 'POST':
        day = request.form.get('day')
        typ = request.form.get('type')
        amt = request.form.get('amount')
        notes = request.form.get('notes')
        rpu = request.form.get('removePurchase')
        rpa = request.form.get('removePayback')
        rpt = request.form.get('removeTransfer')
        d = request.form.get('debit')
        rd = request.form.get('removeDebit')
        if(d!=None):
            cur.execute("INSERT INTO debit(amount) VALUES (?)", (d,))
        if(rpu!=None):
            cur.execute("DELETE FROM purchases WHERE id = ?", (rpu,))
        if(rpa!=None):
            cur.execute("DELETE FROM payback WHERE id = ?", (rpa,))
        if(rpt!=None):
            cur.execute("DELETE FROM transfer WHERE id = ?", (rpt,))
        if(rd!=None):
            cur.execute("DELETE FROM debit WHERE id = ?", (rd,))
        if(typ=="spent"):
            cur.execute("INSERT INTO purchases(day, amount, notes) VALUES (?,?,?)", [ day, amt, notes])
        elif(typ=="gained"):
            cur.execute("INSERT INTO payback(day, amount, notes) VALUES (?,?,?)", [ day, amt, notes])
        elif(typ=="transfer"):
            cur.execute("INSERT INTO transfer(day, amount) VALUES (?,?)", [ day, amt])
        con.commit()

    # maths
    limit = 1000

# PURCHASES AND PAYBACK
    cur.execute("SELECT SUM(amount) FROM purchases")
    try:
        totalSpent=round(cur.fetchone()[0], 2)
    except:
        totalSpent = 0
    cur.execute("SELECT SUM(amount) FROM payback")
    try:
        totalGained= round(cur.fetchone()[0], 2)
    except:
        totalGained = 0
    forHard = totalSpent
    totalSpent -= totalGained
    totalLeft = round(limit - totalSpent, 2)

# AVERAGES
    cur.execute("SELECT COUNT(*) FROM purchases")
    days = round(cur.fetchone()[0])
    if(days==0): days=1
    if(days>30): days=30
    average = round(totalSpent/days, 2)
    fAverage = round(totalLeft/(31-days), 2)
    leftWith = limit - round(average*31)

# TRANSFERRED
    cur.execute("SELECT SUM(amount) FROM transfer")
    try:
        amtTrans = round(cur.fetchone()[0], 2)
    except:
        amtTrans = 0
    hts = round(forHard + amtTrans, 2)
    htl = round(limit-hts, 2)
 
# DEBIT
    cur.execute("SELECT SUM(amount) FROM debit")
    try:
        debit = cur.fetchone()[0]
    except:
        debit = 0

    # end maths

    cur.execute("SELECT * FROM payback")
    payback = cur.fetchall()

    cur.execute("SELECT * FROM purchases")
    purchases = cur.fetchall()

    cur.execute("SELECT * FROM transfer")
    transfer = cur.fetchall()

    cur.execute("SELECT * FROM debit")
    debitList = cur.fetchall()[::-1]

    con.close()
    return render_template('index.html', purchases=purchases, payback=payback, totalSpent=totalSpent, totalLeft=totalLeft, totalGained=totalGained, average=average, fAverage=fAverage, leftWith=leftWith, debit=debit, debitList=debitList, transfer=transfer, hts=hts, amtTrans=amtTrans, htl=htl, filename = filename)




# -------------------------

if __name__ == '__main__':
    app.run(debug=True)