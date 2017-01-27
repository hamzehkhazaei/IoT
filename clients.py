import random
import time

import pika

import infrastructure_management as im

connection = pika.BlockingConnection(pika.ConnectionParameters(im.controller_ip))
channel = connection.channel()
channel.queue_declare(queue='qiot')

count = 0
regions = im.regions_name
mean_arr_time_aggs = 10

while True:
    ind = random.randint(0, len(regions) - 1)
    change = random.randint(0, 1)
    region = regions[ind]

    if change == 1:  # scale up
        req = str(region) + "," + "1"
    else:   # scale down
        req = str(region) + "," + "1"

    channel.basic_publish(exchange='', routing_key='qiot', body=req)
    print(" [" + str(count) + "] Sent request for: " + req)
    time.sleep(random.expovariate(1/mean_arr_time_aggs))
    # input()
    count += 1

# connection.close()
