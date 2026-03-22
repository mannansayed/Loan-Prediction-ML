from flask import Flask, render_template, session, request, url_for, flash, redirect
import pickle
import pandas as pd
import numpy as np 
from supabase_config import supabase
from hashlib import sha256

app = Flask(__name__)
app.secret_key = "bank_loan_prediction"



# Load model and scaler
model = pickle.load(open("loan_logistic_model.pkl", "rb"))
scaler = pickle.load(open("loan_scaler.pkl", "rb"))

# Feature columns used during training
columns = ['Gender','Married','Dependents','Education',
           'Applicant_Income','Coapplicant_Income','Loan_Amount',
           'Loan_Term','Credit_History','Age',
           'Employment_Status_Self-Employed',
           'Employment_Status_Unemployed',
           'Property_Area_Semiurban',
           'Property_Area_Urban']

def hash_password(password):
      return sha256(password.encode()).hexdigest()




@app.route('/')
def home():
    return render_template("index.html")



















@app.route('/login', methods=['GET','POST'])
def login():

    if request.method=='POST':

        email = request.form.get('email')
        password = request.form.get('password')

        response = supabase.table("users").select("*").eq("email",email).execute()

        if response.data:

            user = response.data[0]

            if hash_password(password) == user['password']:

                session['user_id'] = user['uid']
                session['username'] = user['name']
                session['email'] = user['email']

                flash("Login successful","success")

                return redirect(url_for("predict_page"))

            else:
                flash("Invalid Password","error")
                return redirect(url_for("login"))

        else:
            flash("Email not registered","error")
            return redirect(url_for("login"))

    return render_template('login.html')









@app.route('/register',methods=["GET","POST"])
def register():
    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        bankcode = request.form.get("bankcode")
        
        phoneno = request.form.get("phoneno")
        password = request.form.get("password")
        # check existing email
        existing = supabase.table("users").select("*").eq("email",email).execute()

        if existing.data:
            flash("Email already registered","error")
            return redirect(url_for("register"))
        
        hashed_password = hash_password(password)

        supabase.table("users").insert({
            "name":name,
            "email":email,
            "bankcode":bankcode,
            "phoneno":phoneno,
            "password":hashed_password
        }).execute()

        flash("Registration successful","success")
        return redirect(url_for("login"))
        
        
        
    
    
    return render_template("register.html")










@app.route('/predict_page')
def predict_page():
    return render_template("predict.html")


@app.route('/predict', methods=['POST'])
def predict():

    Gender = request.form['Gender']
    Married = request.form['Married']
    Dependents = int(request.form['Dependents'])
    Education = request.form['Education']
    Employment_Status = request.form['Employment_Status']
    Applicant_Income = float(request.form['Applicant_Income'])
    Coapplicant_Income = float(request.form['Coapplicant_Income'])
    Loan_Amount = float(request.form['Loan_Amount'])
    Loan_Term = float(request.form['Loan_Term'])
    Credit_History = int(request.form['Credit_History'])
    Property_Area = request.form['Property_Area']
    Age = int(request.form['Age'])

    # Encoding
    gender = 1 if Gender == "Male" else 0
    married = 1 if Married == "Yes" else 0
    education = 1 if Education == "Graduate" else 0

    emp_self = 1 if Employment_Status == "Self-Employed" else 0
    emp_unemp = 1 if Employment_Status == "Unemployed" else 0

    prop_semi = 1 if Property_Area == "Semiurban" else 0
    prop_urban = 1 if Property_Area == "Urban" else 0

    data = [[gender, married, Dependents, education,
             Applicant_Income, Coapplicant_Income,
             Loan_Amount, Loan_Term, Credit_History, Age,
             emp_self, emp_unemp, prop_semi, prop_urban]]

    df = pd.DataFrame(data, columns=columns)

    scaled = scaler.transform(df)

    prediction = model.predict(scaled)

    if prediction[0] == 1:
        result = "Loan Approved ✅"
    else:
        result = "Loan Rejected ❌"

    return render_template("predict.html", prediction_text=result)


if __name__ == "__main__":
    app.run(debug=True)