from __future__ import annotations
from typing import TYPE_CHECKING

import requests

IMAGE_PVS = [
    "device1/image",
    "device2/image",
]

WORK_QUEUE_NUM_WORKERS = 12
IMAGE_BACKEND_ENDPOINT_URL = "http://localhost:5000"

from p4p.client.thread import Context as P4PContext
from p4p.rpc import WorkQueue

if TYPE_CHECKING:
    from p4p import Value as P4PValue

def send_to_image_backend(value: P4PValue):
    requests.post(IMAGE_BACKEND_ENDPOINT_URL, data={'device_name': value.device_name, 'shot_id': value.shot_id},
                  files={'image_data': value.image_data},
                 )

def main():
    # Subscribe to the image PVs
    work_queue = WorkQueue(WORK_QUEUE_NUM_WORKERS)
    p4p_context = P4PContext('pva', queue=work_queue)

    for image_pv in IMAGE_PVS:
        p4p_context.monitor(image_pv, send_to_image_backend)


if __name__ == '__main__':
    main()

