#!/usr/bin/python2.7

import httplib
import json
import ndb_functions
from Queue import Queue
from threading import Thread

var95s = []
var99s = []


def call_lambda(q, mean, sd, rp):

    # Function called by each thread

    # Get next count from queue
    count = q.get()

    params = {"key1": str(count), "key2": str(mean), "key3": str(sd), "key4": str(rp)}

    # jsonify parameters
    json_input = json.dumps(params)

    # Call Lambda function, then get response
    conn = httplib.HTTPSConnection("n8ohsp32p5.execute-api.eu-west-2.amazonaws.com")

    conn.request("POST", "/deploy", json_input)

    response = conn.getresponse()

    data = response.read()

    # Un-jasonify
    results = json.loads(data)

    var95s.append(float(results[0]))
    var99s.append(float(results[1]))

    # Tell queue it's done
    q.task_done()

    return


def call_lambda_r(mean, sd, rp, samples_first, samples, resources):

    # Function sets up queue
    # Returns separate lists for var 95% and var99%

    # Make sure global lists are empty
    var95s[:] = []
    var99s[:] = []

    q = Queue(maxsize=0)

    # Start a thread for each resource

    for i in range(resources):

        worker = Thread(target=call_lambda, args=(q, mean, sd, rp))
        worker.setDaemon(True)
        worker.start()

    # Add the counts to the queue

    for i in range(resources):

        if i == 0:
            q.put(samples_first)
        else:
            q.put(samples)

    # Finish off threads

    q.join()

    # Write results to google datastore
    for i in range(resources):

        ndb_functions.gds_write_res("lambda", "lambda" + str(i), var95s[i], var99s[i])

    return

