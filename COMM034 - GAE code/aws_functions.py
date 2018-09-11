#!/usr/bin/python2.7

import boto.ec2


def create_ec2_from_img(num_instances, first_samples):

    # Starts up required number of ec2 instances from own ami
    # Returns list of reservations

    for i in range(num_instances):

        userdata = get_user_data(i, first_samples)

        ec2_conn = boto.ec2.connect_to_region('eu-west-2',
                                              aws_access_key_id="AKIAJGBKPPL2RLLVYU5A",
                                              aws_secret_access_key="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")

        ec2_conn.run_instances(image_id='ami-a5dfc8c1',
                               key_name='euwest2',
                               security_groups=['ssh'],
                               instance_type='t2.micro',
                               user_data=userdata,
                               instance_profile_name='inst-profile')

    return


def terminate_ec2():

    # Terminates all ec2 instances in all reservations
    ec2_conn = boto.ec2.connect_to_region('eu-west-2', aws_access_key_id="AKIAJGBKPPL2RLLVYU5A",
                                          aws_secret_access_key="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")

    reservations = ec2_conn.get_all_reservations()

    for res in reservations:
        for inst in res.instances:
            ec2_conn.terminate_instances(inst.id)
    return


def get_user_data(inst_i, first_smp):

    # Set up user data for ec2 instances
    # Writes data.txt file to home directory with instance number and in the case of instance 0,
    # number of samples
    # Runs commands to copy required file from S3 bucket, and run python code
    # Writes message to status.txt when finished
    # Returns user data string

    userdata = "#!/bin/bash\n"
    userdata = userdata + "echo " + str(inst_i) + " >> /home/ubuntu/data.txt\n"

    if inst_i == 0:
        userdata = userdata + "echo " + str(first_smp) + " >> /home/ubuntu/data.txt\n"

    userdata = userdata + """sudo aws s3 cp s3://ama-cloud-cw/ami-creds /home/ubuntu/comm034x1.json --region eu-west-2
    sudo aws s3 cp s3://ama-cloud-cw/ami-python /home/ubuntu/ami.py --region eu-west-2
    sudo python /home/ubuntu/ami.py
    echo 'End of Script' >> /home/ubuntu/status.txt"""

    return userdata
