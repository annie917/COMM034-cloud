#!/usr/bin/python2.7

from google.appengine.ext import ndb
from data_proc import calc_mean


class Results(ndb.Model):

    # Models results entity
    method = ndb.StringProperty()
    var95 = ndb.StringProperty()
    var99 = ndb.StringProperty()


class Input(ndb.Model):

    # Models input parameters entity
    # Stored then retrieved by EC2
    average = ndb.FloatProperty()
    sd = ndb.FloatProperty()
    recent = ndb.FloatProperty()
    samples = ndb.FloatProperty()


class Parameters(ndb.Model):

    # Models user input parameters
    name = ndb.StringProperty()
    investment = ndb.FloatProperty()
    data_points = ndb.IntegerProperty()
    samples = ndb.IntegerProperty()
    resources = ndb.IntegerProperty()
    resource_type = ndb.StringProperty()


def gds_write_params(avg, sd, rec_price, mc_samples):

    # Write the input parameters to Google Cloud Datastore
    # These will be read by EC2 instances

    key = ndb.Key("Input", "Params")

    input_obj = Input(key=key, average=avg, sd=sd, recent=rec_price, samples=mc_samples)

    input_obj.put()

    return


def gds_write_user_params(company, investment, points, samples, resources, res_type):

    # Write the user input parameters to Google Cloud Datastore
    # These will be read back for display on another page

    key = ndb.Key("Parameters", "Values")

    input_obj = Parameters(key=key, name=company, investment=investment, data_points=points, samples=samples,
                           resources=resources, resource_type=res_type)

    input_obj.put()

    return


def gds_write_res(method, key_name, var95, var99):

    # Write results to Google Cloud Datastore, with key name that
    # identifies this instance

    key = ndb.Key("Results", key_name)

    res_obj = Results(key=key, method=method, var95=str(var95), var99=str(var99))

    res_obj.put()

    return


def gds_read_user_params():

    # Read the user entered parameters for display with results
    kind = 'Parameters'
    name = 'Values'
    key = ndb.Key(kind, name)

    result = key.get()

    return result


def gds_read_results(res_type, investment):

    # Read all VaR values from datastore, multiply by investment and format for outputting

    res_mc_95 = []
    res_mc_99 = []

    kind = 'Results'
    name = 'hist'
    key = ndb.Key(kind, name)
    results_hist = key.get()
    results_hist.var95 = "${:.2f}".format(float(results_hist.var95) * investment*-1.0)
    results_hist.var99 = "${:.2f}".format(float(results_hist.var99) * investment*-1.0)

    name = 'cov'
    key = ndb.Key(kind, name)
    results_cov = key.get()
    results_cov.var95 = "${:.2f}".format(float(results_cov.var95) * investment*-1.0)
    results_cov.var99 = "${:.2f}".format(float(results_cov.var99) * investment*-1.0)

    if res_type == 'EC2':

        query = Results.query(Results.method == 'EC2')

    else:

        query = Results.query(Results.method == 'lambda')

    for res in query:
        res_mc_95.append(float(res.var95))
        res_mc_99.append(float(res.var99))

    # Average the scalable results and store in a Results object for consistency with others
    if query.count() > 0:
        results_mc = Results(method=res_type, var95="${:.2f}".format(calc_mean(res_mc_95)*investment*-1.0),
                                              var99="${:.2f}".format(calc_mean(res_mc_99)*investment*-1.0))

    else:
        results_mc = None

    return results_hist, results_cov, results_mc, query.count()


def gds_empty():

    # Collect together keys for all entities to be removed

    keys = []

    kind = 'Input'
    name = 'Params'
    key = ndb.Key(kind, name)
    keys.append(key)

    kind = 'Parameters'
    name = 'Values'
    key = ndb.Key(kind, name)
    keys.append(key)

    kind = 'Results'
    name = 'hist'
    key = ndb.Key(kind, name)
    keys.append(key)

    name = 'cov'
    key = ndb.Key(kind, name)
    keys.append(key)

    # Delete multiple entities at once
    ndb.delete_multi(keys)

    # Delete MC results by query, to allow for gaps in key numbers

    query = Results.query(Results.method == 'lambda')

    for res in query:
        res.key.delete()

    query = Results.query(Results.method == 'EC2')

    for res in query:
        res.key.delete()

    return


def gds_check_results():

    # Check that the historical and covariance results are back before trying to display them

    flag = False

    if Results.query(Results.method == 'hist').count() == 1:
        if Results.query(Results.method == 'cov').count() == 1:
            flag = True

    return flag
