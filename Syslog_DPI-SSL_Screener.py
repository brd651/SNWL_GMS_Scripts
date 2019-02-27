import csv
import re
import sqlite3
import time
import os

#start total processing timer
t0 = time.time()

addheaders = "count,serial,message"

#Create and open Database
conn = sqlite3.connect("sites.db")
c = conn.cursor()

#take user imput for directory which includes the \Data folder
text = input("Where is your Data?(Full file path with \Data folder)")
os.chdir(text + "/")

#Getting length of array or total files in directory
numfi = len(os.listdir("./"))

#setting i for use
i=1
for files in os.listdir("./"):
    print("Processing " + str(i) + " of " + str(numfi) + " files")
    #Start of per file timer
    ti0 = time.time()

    #opening file to add headers for easier reading also checking if they exist to not duplicate if they exist
    with open(files, "r+") as fb:
        content2 = fb.readline()
        if content2 == addheaders:
            continue
        else:
            with open(files, "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write(addheaders.rstrip('\r\n') + '\n' + content)
    #creating lists for use later
    message = []
    count = []

    #creating temporary files
    headers = "URL,counts\n"
    try:
        b = open('../Temp/temp.csv')
        b.close()
    except IOError:
        createfile = open("../Temp/temp.csv", "w")
        createfile.write(headers)
        createfile.close()

    headers2 = "Untrusted_URL,counts,untrusted\n"
    try:
        b = open('../Temp/fail.csv')
        b.close()
    except IOError:
        createfile = open("../Temp/fail.csv", "w")
        createfile.write(headers2)
        createfile.close()

    #Getting rid of all the useless data and parsing what is needed(needs refactoring, slow currently)
    print("Cleaning up files")
    with open(files, "r+") as g:
        reader = csv.DictReader(g, delimiter=',')
        for row in reader:
            try:
                a2 = re.search(r'server:(.*)connection', row['message']).group(1).replace(" ", "")
                row['message'] = a2
                urls = open("../Temp/temp.csv", "a")
                urls.write(str(row['message']) + "," + str(row['count'] + "\n"))
                urls.close()
            except AttributeError:
                continue

    with open(files, "r+") as g:
        reader = csv.DictReader(g, delimiter=',')
        for row in reader:
            try:
                a3 = re.search(r'sni:(.*)$', row['message']).group(1).replace(" ", "")
                row['message'] = a3
                row['untrusted'] = 1
                urls = open("../Temp/fail.csv", "a")
                urls.write(str(row['message']) + "," + str(row['count']) + "," + str(row['untrusted']) + "\n")
                urls.close()
            except AttributeError:
                continue

    with open(files, "r+") as g:
        reader = csv.DictReader(g, delimiter=',')
        for row in reader:
            try:
                a4 = re.search(r'Hello(.*)blocked', row['message']).group(1).replace(" ", "")
                row['message'] = a4
                row['untrusted'] = 1
                urls = open("../Temp/fail.csv", "a")
                urls.write(str(row['message']) + "," + str(row['count']) + "," + str(row['untrusted']) + "\n")
                urls.close()
            except AttributeError:
                continue

    #putting data into the 2 different tables to see the difference between common failure and cert failure
    print("Inserting into Database")
    c.execute("CREATE TABLE if not exists dpifail(URL TEXT,counts INTEGERS);")
    with open("../Temp/temp.csv", "r") as dump:
        read = csv.DictReader(dump)
        to_db = [(i['URL'], i['counts']) for i in read]
    for x in to_db:
        c.execute('select count() from dpifail where URL =?', (x[0],))
        c2 = c.fetchone()
        if c2 == (0,):
            c.execute('INSERT INTO dpifail(URL, counts) VALUES (?,?);', x)
        else:
            c.execute('UPDATE dpifail set counts = counts + 1 where URL =?', (x[0],))

    #creates table for the untrusted cert failures and puts in the domains of failures
    c.execute("CREATE TABLE if not exists certfail(Untrusted_URL VARCHAR,counts INTEGERS,untrusted INTEGERS);")
    with open("../Temp/fail.csv", "r") as dump2:
        read2 = csv.DictReader(dump2)
        to_db2 = [(i['Untrusted_URL'], i['counts'], i['untrusted']) for i in read2]
    for y in to_db2:
        c.execute('select count() from certfail where Untrusted_URL =?', (y[0],))
        c3 = c.fetchone()
        if c3 == (0,):
            c.execute("INSERT INTO certfail(Untrusted_URL, counts, untrusted) VALUES (?,?,?);", y)
        else:
            c.execute("UPDATE certfail set counts = counts + 1 where Untrusted_URL =?", (y[0],))

    conn.commit()

    #Cleaning up temp files
    try:
        os.remove("../Temp/temp.csv")
    except OSError:
        pass

    try:
        os.remove("../Temp/fail.csv")
    except OSError:
        pass

    #moving files to old data folder to make sure they are not processed again
    print("Moving " + files + " to Old_Data")
    os.rename("./" + files, "../Old_Data/" + files)
    #ending the file timer
    ti1 = time.time()
    #setting the per file time list
    times = []
    #getting the total time for file process
    totali = ti1 - ti0
    #adding time to times list
    times.append(totali)
    print(str(totali) + " seconds\n")
    #incrementing i because end of loop
    i += 1

#final commit to make sure the database is saved and close the connection
conn.commit()
conn.close()
#Ending full time process
t1 = time.time()
#getting the total time script ran
total = t1 - t0
#averaging the per file times to get the Mean time
avg = (sum(times)/len(times))
print("Average time to process file " + str(avg))
print("Completed Processing all files in " + str(total))
