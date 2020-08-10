import datetime
import requests
import mysql.connector
import os
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split # train model and use it to predict and compare against label
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import pandas as pd
from flask import Flask, render_template, request

host = os.environ.get('MYSQL_HOST')
database = os.environ.get('MYSQL_DATABASE')
password = os.environ.get('MYSQL_PASSWORD')
user = os.environ.get('MYSQL_USER')
print(database)
print(password)
print(user)
print(host)
connection = mysql.connector.connect(host=host, user=user, password=password, database=database)


cursor = connection.cursor()

app = Flask(__name__)
completedApps = [] # list of all company applications

class Application:
    def __init__(self, company_name, role_applied, jobID, season, date_submitted, status):
        self.company = company_name
        self.role = role_applied
        self.jobID = jobID
        self.season = season
        self.date = date_submitted
        self.status = status

    def get_name(self):
        return str(self.company)

    def get_role(self):
        return str(self.role)

    def get_id(self):
        return str(self.jobID)

    def get_season(self):
        return str(self.season)

    def get_date(self):
        # print(self.date)
        return str(self.date)

    def get_status(self):
        return str(self.status)

@app.route('/', methods=['GET', 'POST'])
def renderHome():
    return render_template('home.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def viewapps():  # GET request
    # return 'Hello World'
    completedApps.clear()
    if request.method == 'GET':
        cursor.execute("SELECT * FROM applications")
        for data in cursor.fetchall():  # data from database
            print(str(data[0]) + str(data[1]) + str(data[2]) + str(data[3]) + str(data[4]) + str(data[5]))
            app1 = Application(data[0], data[1], data[2], data[3], data[4], data[5])
            completedApps.append(app1)
    if request.method == 'POST':
        comp = request.form['companyName']
        role = request.form['position']
        id = request.form['jobid']
        season = request.form['season']
        date = request.form['submissionDate']
        # p1 = Person(firstname, lastname, bday, country)
        # names.append(p1)

        mutation = ('''INSERT INTO applications (companyName, position, jobID, season, submissionDate) VALUES (%s, %s, %s, %s, %s) ''')
        # query = ('''SELECT * FROM person;''')
        data_company = (comp, role, id, season, date)
        cursor.execute(mutation, data_company)
        # cursor.execute(query)
        connection.commit()
    time = datetime.datetime.now().strftime('%m/%d/%Y')
    numApps = len(completedApps)
    return render_template('dashboard.html', apps=completedApps, currTime=time, numApps=numApps)


@app.route('/addform', methods=['GET'])
def addCompletedApps():
    return render_template('addform.html')


@app.route('/companyView?fullname={fullname}', methods=['GET'])
def viewinfo():  # GET request
    # return 'Hello World'
    resp = requests.get('https://restcountries.eu/rest/v2/name/{name}')


@app.route('/companyView', methods=['GET'])  # GET requests will be blocked
def viewcompany():
    # first API: company domain and logo
    company_url = "https://company.clearbit.com/v1/domains/find?name="
    company_payload = {}
    company_headers = {
        'Authorization': 'Bearer sk_b640f0b21ee2bc300a164ce9c80eb039'
    }

    # second API: job board aggregation
    api_key = "&api_key=e4124c40495d16d7b530ab785224474ee7f1ab10b3ea27135ba1614834b3ad5a"
    page = "&page=1"
    url_jobs = "https://www.themuse.com/api/public/jobs?company="
    jobs_payload = {}
    jobs_headers = {
        'Cookie': '__cfduid=dc196f321486fdfd61272b17a78a6b4321589046784'
    }

    for x in completedApps:
        print(x.get_name().lower().strip())
        if x.get_name().lower() == request.args.get('companyname').lower():
            company = x
            print("got here")
            break
    resp_clearbit_api = requests.request("GET", company_url + company.get_name(), headers=company_headers, data=company_payload)
    resp_muse_api = requests.request("GET", url_jobs + company.get_name() + page + api_key, headers=jobs_headers, data=jobs_payload)
    print("RESPONSE OF FIRST API IS: " + str(resp_clearbit_api.status_code))
    print("RESPONSE OF SECOND API IS: " + str(resp_muse_api.status_code))
    if (resp_clearbit_api.status_code == 404):
        name = "unknown company name"
        domain = "localhost:5000/dashboard"
        logo = ""
    else:
        jsonresp = resp_clearbit_api.json()
        name = jsonresp['name']
        domain = jsonresp['domain']
        logo = jsonresp['logo']
    if (resp_muse_api.status_code == 404):
        print("")
    else:
        jsonresp_muse = resp_muse_api.json()
        print(jsonresp_muse)
        job_name = ""
        job_description = ""
        job_link = ""
        if len(jsonresp_muse['results']) > 0:
            # if(len(jsonresp_muse['results']) < 5):
            #     for x in jsonresp_muse['results']:
            #         print(jsonresp_muse['results'][0])
            #         job_name = jsonresp_muse['results'][0]['name'] + ", "
            #         print("job name: " + job_name) + ", "
            #         job_description = jsonresp_muse['results'][0]['contents']
            #         print("job desc: " + job_description) + ", "
            #         job_link = "Apply Now: " + jsonresp_muse['results'][0]['refs']['landing_page']
            #         print("job link: " + job_link)
            # else:
            #     for x in range (5):
            print(jsonresp_muse['results'][0])
            job_name += jsonresp_muse['results'][0]['name']
            print("job name: " + job_name)
            job_description += jsonresp_muse['results'][0]['contents']
            print("job desc: " + job_description)
            job_link += "Apply Now: " + jsonresp_muse['results'][0]['refs']['landing_page']
            print("job link: " + job_link)
            return render_template('viewapps.html', companyname=name, companydomain=domain, companylogo=logo,
                                   jobname=job_name,
                                   jobdesc=job_description, joblink=job_link)
        else:
            return render_template('viewapps.html', companyname=name, companydomain=domain, companylogo=logo,
                                   jobname="No jobs found.")


@app.route('/profile', methods=['GET'])
def goToProf():
    return render_template('profile.html')


@app.route('/profile', methods=['POST'])
def predictSalary():  # GET request
    # Importing the dataset
    dataset = pd.read_csv('salary_data.csv')
    x = dataset.iloc[:, :-1].values  # years of experience
    y = dataset.iloc[:, 1].values  # salary
    # x = dataset[['Salary']]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)
    regressor = LinearRegression()
    regressor.fit(x_train, y_train)
    # Visualizing the Training set results
    plt.scatter(x_train, y_train, color='red')
    plt.plot(x_train, regressor.predict(x_train), color='blue')
    plt.title('Salary VS Experience (Training set)')
    plt.xlabel('Year of Experience')
    plt.ylabel('Salary')
    # plt.show()
    fig_train, ax = plt.subplots()
    # s.plot.bar()
    fig_train.savefig('train_plot.png')

    # Visualizing the Test set results
    plt.scatter(x_test, y_test, color='red')
    plt.plot(x_train, regressor.predict(x_train), color='blue')
    plt.title('Salary VS Experience (Test set)')
    plt.xlabel('Year of Experience')
    plt.ylabel('Salary')
    # plt.show()
    fig_test, ax = plt.subplots()
    # s.plot.bar()
    fig_test.savefig('test_plot.png')
    print(x)
    sal = ""
    if request.method == 'POST':
        user_input = request.form['yoe']
        print(user_input)
        y_pred = regressor.predict(np.array([int(user_input)]).reshape(1, 1))
        print(y_pred.reshape(1, 1))
    return render_template('profile.html', salary=y_pred)


@app.route('/postendpoint', methods=['POST'])  # POST request
def post():  # client sends data to server so server must take that info and store it/use it for ML/etc
    resp = Response(status=200)
    print(request.data)  # data is what we specified for POST request
    return resp

if __name__ == '__main__':
    app.run(debug=True)

