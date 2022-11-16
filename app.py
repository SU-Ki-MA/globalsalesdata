from os import getenv
from flask import Flask, render_template, url_for, request, redirect, Markup, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import uuid
import json
import pymysql
# ml imports
import pickle
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split

load_dotenv()
mysql_user = getenv('MYSQL_USER')
mysql_pass = getenv('MYSQL_PASS')
deploy_url = getenv('DEPLOYMENT_URL')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + \
    mysql_user+':'+mysql_pass+'@localhost/globalsalesdata'
db = SQLAlchemy(app)
app.app_context().push()


class Tokens(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    session = db.Column(db.String(36))
    sts = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id


@app.errorhandler(404)
def page_not_found(e):
    return redirect('/generatetoken')


@app.route('/generatetoken', methods=['POST', 'GET'])
def gentoken(active=False, dashboard=False, report=False, story=False, deactivate=False, ml=False, generatetoken=True, activateaccount=False,
             toasts=[], toastdata=[]):
    if request.method == 'POST':
        newid = uuid.uuid4()
        newuser = Tokens(id=str(newid))
        try:
            db.session.add(newuser)
            db.session.commit()
            return {"token_id": str(newid)}
        except:
            return {"token_id": "Error : something when wrong"}
    else:
        return render_template('generatetoken.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)


@app.route('/activateacc', methods=['POST', 'GET'])
def activateacc(active=False, dashboard=False, report=False, story=False, deactivate=False, ml=False, generatetoken=False, activateaccount=True,
                toasts=[], toastdata=[]):
    if request.method == 'POST':
        tokenid = request.form['tokenid']
        toactivate = Tokens.query.get_or_404(tokenid)
        if toactivate.sts == False:
            toactivate.sts = True
            sesid = uuid.uuid4()
            toactivate.session = str(sesid)
            db.session.commit()
            toasts = ['success']
            toastdata = [Markup('Successfully activated your account')]
            active = True
            activateaccount = False
            dashboard = True
            res = make_response(render_template('dashboard.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate,
                                ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url))
            res.set_cookie('tokenid', tokenid)
            res.set_cookie('sessionid', str(sesid))
            return res
        else:
            toasts = ['warning']
            toastdata = [Markup('The Token has already been utilized <br> Please <a href="' +
                                deploy_url+'/generatetoken" class="link-text">generate new one</a>')]
            return render_template('activateacc.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)
    else:
        return render_template('activateacc.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)


@app.route('/dashboard')
def dashboard(active=False, dashboard=True, report=False, story=False, deactivate=False, ml=False, generatetoken=False, activateaccount=False,
              toasts=[], toastdata=[]):
    sesid = request.cookies.get('sessionid', '')
    if sesid != '':
        row = Tokens.query.filter_by(session=sesid).first()
        if row is None:
            return gentoken(toasts=['danger'], toastdata=[Markup('bad session')])
        else:
            active = True
            return render_template('dashboard.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)
    else:
        return gentoken(toasts=['warning'], toastdata=[Markup('no session available <br> please activate account or <a href="'+deploy_url+'/generatetoken" class="link-text">generate new token</a>')])


@app.route('/deactivate')
def deactivate(active=False, dashboard=False, report=False, story=False, deactivate=True, ml=False, generatetoken=False, activateaccount=False,
               toasts=[], toastdata=[]):
    sesid = request.cookies.get('sessionid', '')
    row = Tokens.query.filter_by(session=sesid).first()
    if row is None:
        return gentoken(toasts=['danger'], toastdata=[Markup('bad session')])
    else:
        db.session.delete(row)
        db.session.commit()
        deactivate = False
        geenratetoken = True
        toasts = ['success']
        toastdata = ['Successfully Deactivated your token.']
        res = make_response(render_template('generatetoken.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate,
                            ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url))
        res.set_cookie('tokenid', '')
        res.set_cookie('sessionid', '')
        return res


@app.route('/story')
def story(active=False, dashboard=False, report=False, story=True, deactivate=False, ml=False, generatetoken=False, activateaccount=False,
          toasts=[], toastdata=[]):
    sesid = request.cookies.get('sessionid', '')
    if sesid != '':
        row = Tokens.query.filter_by(session=sesid).first()
        if row is None:
            return gentoken(toasts=['danger'], toastdata=[Markup('bad session')])
        else:
            active = True
            return render_template('story.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)
    else:
        return gentoken(toasts=['warning'], toastdata=[Markup('no session available <br> please activate account or <a href="'+deploy_url+'/generatetoken" class="link-text">generate new token</a>')])


@app.route('/report')
def report(active=False, dashboard=False, report=True, story=False, deactivate=False, ml=False, generatetoken=False, activateaccount=False,
           toasts=[], toastdata=[]):
    sesid = request.cookies.get('sessionid', '')
    if sesid != '':
        row = Tokens.query.filter_by(session=sesid).first()
        if row is None:
            return gentoken(toasts=['danger'], toastdata=[Markup('bad session')])
        else:
            active = True
            return render_template('report.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)
    else:
        return gentoken(toasts=['warning'], toastdata=[Markup('no session available <br> please activate account or <a href="'+deploy_url+'/generatetoken" class="link-text">generate new token</a>')])


@app.route('/ml')
def ml(active=False, dashboard=False, report=False, story=False, deactivate=False, ml=True, generatetoken=False, activateaccount=False,
        toasts=[], toastdata=[]):
    sesid = request.cookies.get('sessionid', '')
    if sesid != '':
        row = Tokens.query.filter_by(session=sesid).first()
        if row is None:
            return gentoken(toasts=['danger'], toastdata=[Markup('bad session')])
        else:
            active = True

            return render_template('ml.html', active=active, dashboard=dashboard, report=report, story=story, deactivate=deactivate, ml=ml, generatetoken=generatetoken, activateaccount=activateaccount, toasts=toasts, toastdata=toastdata, deploy_url=deploy_url)
    else:
        return gentoken(toasts=['warning'], toastdata=[Markup('no session available <br> please activate account or <a href="'+deploy_url+'/generatetoken" class="link-text">generate new token</a>')])


# ml functions

@app.route('/mljson')
def mljson():
    with open("static/pkl/data.json", encoding="utf8") as f:
        final_out_data = json.load(f)
        return final_out_data

# ml evalution function


def findAccuracy(value):
    col_name = ['Ship Mode', 'Segment', 'City', 'State', 'Country', 'Market', 'Region',
                'Category', 'Sub-Category', 'Product Name', 'Sales', 'Quantity',
                'Discount', 'Profit', 'Shipping Cost', 'Item Value']
    final_data = {}
    for i in range(len(col_name)):
        final_data[col_name[i]] = [value[col_name[i]]]
    # data frame
    dataFrame = pd.DataFrame(final_data)

    file = "static/pkl/finalModel.pkl"
    fileObject2 = open(file, "rb")
    model = pickle.load(fileObject2, encoding='binary')
    return model.predict(dataFrame)[0]


@app.route('/ml-evaluate', methods=['POST'])
def mlEvaluate(): 
    return {"accuracy": int(findAccuracy(request.get_json(force=True)))}


if __name__ == "__main__":
    app.run(debug=True)
