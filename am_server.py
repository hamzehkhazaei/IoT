import pika

import infrastructure_management as im
from autonomic_manager import scale_kafka_service, init


def handle_arrival_request(ch, method, properties, body):
    req = str(body, encoding='utf8').split(",")
    region, change = req[0], int(req[1])

    if region.__contains__("CORE"):
        scale_kafka_service("core-agg", change)
    elif region.__contains__("EDGE-WT-1"):
        scale_kafka_service("wt-agg", change)
    elif region.__contains__("EDGE-CT-1"):
        scale_kafka_service("ct-agg", change)
    elif region.__contains__("EDGE-YK-1"):
        scale_kafka_service("yk-agg", change)
    else:
        print("Bad Request: " + str(body))


def start_am():
    init()
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=im.controller_ip))
    channel = connection.channel()
    channel.queue_declare(queue='qiot')
    print(' [*] Waiting for request. To exit press CTRL+C')

    channel.basic_consume(handle_arrival_request, queue='qiot', no_ack=True)
    channel.start_consuming()

start_am()
