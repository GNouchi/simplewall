from flask import Flask, render_template, redirect, request, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
import re, random, math
app = Flask(__name__)
bcrypt = Bcrypt(app)
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
app.secret_key = "8D4C1B7696C8959CD062D99DDA9C0CCCBD6A18E6DE24A65A7CBAC890A43DAFDE"
mysql = connectToMySQL('wall')
# bcrypt.generate_password_hash(password_string)
# bcrypt.check_password_hash(hashed_password, password_string)

@app.route('/')
def index():    
# **********LOGIN PAGE***************
    # print (session)
    if 'session_id' in session: 
        return redirect ('/wall')
    return render_template("login.html" )    

# **************REGISTER*****************
@app.route("/register", methods= ["POST"])
def createuser():
    if 'session_id' in session: 
        return redirect ('/wall')  

    for key in request.form:
        # Flash in errors for any blank fields
        if request.form[key] =="":
            x = key + " was blank"
            flash(x, 'error')
        # Match password inputs 
    if request.form['password'] != request.form['confirm_password']:
        flash('Your passwords do not match', 'error')
    print("**** FORM FILLED = ",'_flashes' not in session,  "****")

# Redirect any error flashes 
    if '_flashes' in session:
        for x in range(len(session['_flashes'])):
            if session['_flashes'][x][0] == 'error':
                print("Found error: ", session['_flashes'][x][1])
        return redirect ('/')


# ******* QUERY AVAILABLE HERE (Info submitted) **********
    print("*********CHECKING EMAIL AVAILABILITY***************")
    query = "select id, name, email from user where email= %(email)s;"
    data1 = {
        'email' : request.form['email'] 
        }
    lookup = mysql.query_db(query, data1)
# ************ If Email exists redirect home *************
    if lookup!=():
        flash("Sorry that email appears to be taken!", 'error')
        return redirect('/') 

# ******** ENSURES USER DOES NOT EXIST **********
    if lookup ==():
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        session['session_id'] = random.randint(1,1000000000)
        usertoadd = "INSERT INTO USER (name, pwd_enc, email, session_id, create_d, update_d) VALUES (%(user_name)s,%(pwd_enc)s,%(email)s,%(session_id)s, NOW(),NOW());"
        data2 = {
            'email' : request.form['email'],
            'user_name' : request.form['user_name'],
            'pwd_enc' : pw_hash,
            'session_id' : session['session_id']
            }
        adduser = mysql.query_db(usertoadd, data2)
# rerun lookup query 
        lookup = mysql.query_db(query, data2)
        session['user_id'] = lookup[0]['id'] 
        session['user_name'] =lookup[0]['name'] 
        return redirect ('/wall')
    else:
        flash("An unexpected error has occured, please contact an admin", 'error')
        print("SQL INSERT ERROR")
        return ("/")

# *********************LOGIN*********************
@app.route('/login',methods = ['POST'])
def logginmcbobbin():
    for key in request.form:
# Check form is filled
        if request.form[key] =="":
            x = key + " is blank"
            flash(x, 'error')
    print("**** good login entered = ",'_flashes' not in session,  "****")

# Redirect any error flashes 
    if '_flashes' in session:
        print("hello2")
        for x in range(len(session['_flashes'])):
            if session['_flashes'][x][0] == 'error':
                print("Found error: ", session['_flashes'][x][1])

#LOGIN******* QUERY AVAILABLE HERE (Info submitted) **********
    print("LOGIN********* CHECKING ACCOUNT EXISTS ***************")
    query = "SELECT id, name, email , pwd_enc FROM USER WHERE email= %(email)s;"
    data = {
        'email' : request.form['email'] 
        }
    lookup = mysql.query_db(query, data)
     
# LOGIN******* If Email DOES NOT EXIST redirect home *************
    if lookup==():
        flash("Your login info does not match anything in our system!", 'error')
        return redirect('/') 

# LOGIN********COMPARE PASSWORD HASHES**********
    if lookup !=():
        print(lookup)
        # IF PW MATCHES, GEN AND REPLACE SESSION_ID
        if bcrypt.check_password_hash(lookup[0]['pwd_enc'], request.form['password']):
            session['user_id'] = lookup[0]['id'] 
            session['user_name'] =lookup[0]['name'] 
            session['session_id'] = random.randint(1,1000000000)
            updatesession = "UPDATE USER SET session_id = %(session_id)s, update_d= NOW() WHERE ID = %(id)s;"
            data = {
                'session_id' : session['session_id'],
                'id' : lookup[0]['id']
            }
            sessionupdate = mysql.query_db(updatesession, data)
            print("LOGIN SUCCESS!")
            return redirect ('/wall')
        else:
            flash("Your login info does not match anything in our system!", 'error')
            print("LOGIN FAIL")
            return redirect ("/")
    else:
        flash("An unexpected error has occured, please contact an admin", 'error')
    return redirect ('/')

# ********************************
# *********** WALL ***************
# ********************************

@app.route('/wall', methods=['GET'])
def rt():
    print(session)
    if 'session_id' not in session or 'user_id' not in session or 'user_name' not in session: 
        session.clear()
        print('session cleared and redirect to home')
        return redirect ('/')

    print("LOGIN********* CHECKING EMAIL EXISTS ***************")
    query1 = "SELECT id, name, session_id from user  where id=%(id)s and session_id=%(session_id)s;"
    data1 = {
        'id' : session['user_id'], 
        'session_id' : session['session_id'] 
        }
    verify = mysql.query_db(query1, data1)

# WALL ********* If Email DOES NOT EXIST redirect home *************
    if verify==():
        session.clear()
        flash("Something broke!", 'error')
        return redirect('/')

# WALL ********* IF SESSIONS DO NOT MATCH THEN CLEAR AND REDIRECT *************
    # if session['session_id']!= verify[0]['session_id']:
    #     session.clear()
    #     print('We have logged you out for security reasons', 'error')
    #     return redirect('/')


# -------- HERE WE KNOW THE CORRECT USER IS LOGGED IN -------#


# WALL------------ QUERY FOR ALL OTHER USERS HERE ------------
    query2 = "SELECT id, name from user where id !=%(id)s and session_id != %(session_id)s;"
    data2 = {
        'id' : session['user_id'], 
        'session_id' : session['session_id'] 
        }
    lookup = mysql.query_db(query2, data2)

# WALL ------------QUERY FOR MESSAGES RECEIVED-----------
    query3 = "select m.id message_id, u2.name from_name,u1.name, TIME_TO_SEC(TIMEDIFF(now() , m.create_d)) as sec_diff, m.message from messages m left join user u1 on u1.id = m.to_user left join user u2 on u2.id = m.from_user where m.to_user =  %(id)s order by m.create_d desc;"
# use the logged session data to run SQL 
    messagehist= mysql.query_db(query3, data1)
    msg_age =0

    # print("------------Show mesage history---------------")
    # print(x)
    # print("----------------------------------------")

    for x in messagehist:
        print( x['sec_diff'])
        if x['sec_diff'] == None:
            flash('timedifference not logged')
            msg_age = "unknown"
        elif x['sec_diff']/(60*60*24) >= 1:
            msg_age=(str(math.floor(x['sec_diff']/(60*60*24))) + " day(s) ago:")
        elif x['sec_diff']/(60*60) >=1:
            msg_age =(str(math.floor(x['sec_diff']/(60*60))) + " hour(s) ago:")
        elif x['sec_diff']/(60) > 1:
            msg_age =(str(math.floor(x['sec_diff']/(60))) + " minute(s) ago:")
        elif x['sec_diff'] :
            msg_age =(str(x['sec_diff']) + " seconds ago:")
    if len(messagehist) == 0 or messagehist==():
        num_msg = "0 Messages"
    elif len(messagehist) == 1:
        num_msg = "1 Message"
    else: 
        num_msg = (str(len(messagehist)) + " Messages")

#------------------------ RENDER PAGE ------------------------
    if 'session_id' in session: 
        user_name = session['user_name']
        session_id = session['session_id']
        return render_template ('wall.html', user_name=user_name,session_id=session_id,lookup=lookup, messagehist=messagehist, num_msg=num_msg, msg_age=msg_age)
    else:
        session.clear()
        print('session cleared and redirect to home')
        return redirect ('/')

# ---------------SENDING MESSAGES----------------

@app.route ('/sendmessage', methods =['POST'])
def chat():
    insertmessage = "INSERT INTO messages (from_user, to_user, message, create_d) VALUES (%(from_user)s,%(to_user)s,%(text)s,now() )"
    data1 = {
        'from_user' : session['user_id'],
        'to_user' : request.form['id'],
        'text': request.form['text']
        }
    sendmsg = mysql.query_db(insertmessage, data1)
    return redirect('/wall')

@app.route('/deletemessage', methods = ['POST'])
def rm():
    rmquery = "DELETE FROM messages WHERE id = %(msg_id)s;"
    rmdata = {
        'msg_id': request.form['msg_id']
    }
    del_msg = mysql.query_db(rmquery, rmdata)
    return redirect('wall')

@app.route('/logout',methods =['GET','POST'] )
def loggout():
    session.clear()
    return redirect('/')


if __name__ == "__main__":
    app.run(debug = True)