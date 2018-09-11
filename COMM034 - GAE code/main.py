#!/usr/bin/python2.7

import webapp2
import jinja2
import os
import ndb_functions
from main_proc import main_processing
from aws_functions import terminate_ec2
from data_proc import get_return_ser

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


def render_template(handler, temp_name, values={}):

    template = jinja_environment.get_template(temp_name)
    handler.response.out.write(template.render(values))

    return


def get_file_names():

    # Get names of files in /data directory and pass back for display
    companies = []

    for datafile in os.listdir("./data"):

        if datafile[-4:] == ".csv":
            companies.append(datafile[:-4])

    return companies


def prepare_chart(company, points):

    # Re-read .csv to get chart data, as seems faster then putting then retrieving
    # from Datastore

    data_file = open("./data/" + company + ".csv", "r")

    # Skip header line
    data_file.readline()

    # Store most recent price as needed for Monte Carlo simulation
    line = data_file.readline()
    today_price = float(line.split(',')[6])
    today_date = line.split(',')[0]

    # Get the returns series then close the file

    ret_ser, sorted_returns, time_series, last_date = get_return_ser(data_file, today_price, points)

    data_file.close()

    return time_series, sorted_returns, last_date, today_date


class MainPage(webapp2.RequestHandler):

    def get(self):

        # Make sure datastore is empty
        ndb_functions.gds_empty()

        # Render input page, with list of companies for drop down list
        companies = get_file_names()
        values = {'companies': companies}
        render_template(self, "index.html", values)


class ResultsPage(webapp2.RequestHandler):

    def get(self):

        ready = True

        params = ndb_functions.gds_read_user_params()

        if params is None or not ndb_functions.gds_check_results():
            ready = False

        if ready:

            times, returns, last_date, first_date = prepare_chart(params.name, params.data_points)

            res_hist, res_cov, res_mc, count = ndb_functions.gds_read_results(params.resource_type, params.investment)

            results = [res_hist, res_cov]
            dates = [last_date, first_date]

            resources = "No Monte Carlo Values returned."

            if count > 0:
                results.append(res_mc)
                resources = "Monte Carlo values calculated from " + str(count) + " resources."

            if count == params.resources:
                resources = "Monte Carlo values calculated from all resources."

            values = {'params': params, 'results': results, 'times': times, 'returns': returns,
                      'res_text': resources, 'ready': ready, 'dates': dates}

            render_template(self, "results.html", values)

            if params.resource_type == "EC2":
                if count == params.resources:
                    terminate_ec2()

        else:
            values = {'ready': ready}

            render_template(self, "results.html", values)


class CalculateHandler(webapp2.RequestHandler):

    def post(self):

        # Set up user input variables
        name = self.request.get('company')
        investment = self.request.get('investment')
        data_points = self.request.get('points')
        mc_samples = self.request.get('samples')
        mc_res = self.request.get('resources')
        res = self.request.get('resType')
        all_points = self.request.get('allPoints')

        if all_points == "Checked":
            data_points = 0

        ec2_flag = False

        if res == 'EC2':
            ec2_flag = True

        # Call main processing function
        main_processing(name, float(investment), int(data_points), int(mc_samples), int(mc_res), ec2_flag)


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/results.html', ResultsPage),
    ('/calculate', CalculateHandler),
    ], debug=True)

