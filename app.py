import logging.config
import pickle
import traceback
import xgboost
import pandas as pd
import numpy as np

from datetime import datetime
from flask import Flask,render_template, url_for, flash, redirect,request
import logging.config
from app import db, app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from src.model import User

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)



logging.config.fileConfig(app.config["LOGGING_CONFIG"])
logger = logging.getLogger("penny-lane")
logger.debug('Test log')


@app.route("/index")
@app.route("/")
def index():
    """Home page of our app 

    Returns: rendered index html template
    """
    return render_template('index.html', title='Index')


@app.route("/contact", methods=['POST','GET'])
def contact():
    """Contact page of our app 

    Returns: rendered contact html template
    """
    return render_template('contact.html', title='contact')


@app.route("/prediction")
def prediction():
    """User input page of our app, prepared for the final prediction 

    Returns: rendered user input html template
    """
    return render_template('prediction.html', title='Prediction')


def ValuePredictor(to_predict_list):
    """the function to make the prediciton based on the user input 

    to_predict_list: a list of user input 

    Returns: 
    Integer: a classifcation label (0 or 1) of whether the customer will buy the product or not
    """

    to_predict = np.array(to_predict_list).reshape(1,15)
    model_path = app.config['MODEL_PATH']
    loaded_model = pickle.load(open(model_path,"rb"))
    #loaded_model = pickle.load(open("models/bank-prediction.pkl","rb"))
    features_columns = ['age', 'job', 'marital', 'education', 'default', 'balance', 'housing','loan', 'contact', 'day', 'month', 'campaign', 'pdays', 'previous','poutcome']
    new_df = pd.DataFrame(to_predict, columns = features_columns)
    result = loaded_model.predict(new_df)
    prob = loaded_model.predict_proba(new_df)
    
    prob_class = [prob[0][1],result[0]]
    return prob_class


@app.route('/result',methods = ['POST'])
def result():
    """Prediction page of our app, return to the error page if any of input is not given 

    Returns: rendered prediction html template
    """
    try:
        if request.method == 'POST':
            to_predict_list = request.form.to_dict()
            to_predict_list=list(to_predict_list.values())
            to_predict_list = list(map(int, to_predict_list)) 
            result = ValuePredictor(to_predict_list)
         
            # tell the user about the prediction result 
            if int(result[1])==1:
                prediction='Woo-hoo, the customer will try the new product!'
            else:
                prediction='Opps, the customer decides to save some money.'

            prob = 'Predicted Purchase Probability: '+str(result[0])
            print(prob)
            print('********')

            # convert all user input to integer to be put into the user database as required
            Age = int(request.form['age'])
            Job = int(request.form['job'])
            Marital = int(request.form['marital'])
            Education = int(request.form['education'])
            Default = int(request.form['default'])
            Balance = int(request.form['balance'])
            Housing = int(request.form['housing'])
            Loan = int(request.form['loan'])
            Contact = int(request.form['contact'])
            Day = int(request.form['day'])
            Month = int(request.form['month'])
            Campaign = int(request.form['campaign'])
            Pdays = int(request.form['pdays'])
            Previous = int(request.form['previous'])
            Poutcome = int(request.form['poutcome'])





            # fill out the row for the user table 
            customer1 = User(age=Age, job =Job, marital=Marital, education=Education, 
                default=Default, balance=Balance, housing=Housing, loan=Loan, 
                contact=Contact, day=Day, month=Month, campaign=Campaign, pdays=Pdays, 
                previous=Previous, poutcome=Poutcome, y =int(result[1]))

            # add the new customer to the user database
            db.session.add(customer1)
            db.session.commit()


            return render_template("result.html",prediction=prediction, prob = prob)
    except:
        # if the user input is incomplete, then direct to the error page.
        logger.warning("At least one user input not been filled")
        return render_template("error.html")


@app.route("/error")
def error():
    """Error page when at least one user input has missing value. This can lead back to the prediction page"""
    return render_template('error.html', title='error')



if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], port=app.config["PORT"], host=app.config["HOST"])
