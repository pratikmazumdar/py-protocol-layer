import time
import uuid
from datetime import datetime, timedelta

from main.config import get_config_by_name
from main.logger.custom_logging import log_error
from main.models import get_mongo_collection
from main.models.catalog import SearchType
from main.repository import mongo
from main.request_models.schema import Domain
from main.service.common import dump_request_payload, update_dumped_request_with_response
from main.service.search import gateway_search
from main.utils.parallel_processing_utils import io_bound_parallel_computation


def make_http_requests_for_search_by_city(search_type: SearchType, domains=None, cities=None, mode="start"):
    search_payload_list = []
    domain_list = [e.value for e in Domain] if domains is None else domains
    end_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    start_time = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    if search_type == SearchType.FULL:
        city_list = ['std:06274', 'std:0451', 'std:0120', 'std:0512', 'std:05842', 'std:0522', 'std:06243', 'std:04286',
                     'std:05547', 'std:0474', 'std:0121', 'std:04266', 'std:04142', 'std:0551', 'std:0124', 'std:0591',
                     'std:0364', 'std:04254', 'std:079', 'std:0129', 'std:06152', 'std:08922', 'std:04362', 'std:05263',
                     'std:0261', 'std:0487', 'std:08252', 'std:01342', 'std:0832217', 'std:0581', 'std:07486', 'std:0132',
                     'std:0484', 'std:0416', 'std:05248', 'std:0191', 'std:04546', 'std:0260', 'std:0427', 'std:08262',
                     'std:0194', 'std:0435', 'std:08258', 'std:01334', 'std:04652', 'std:04147', 'std:0421', 'std:08572',
                     'std:044', 'std:0731', 'std:02836', 'std:0641', 'std:06224', 'std:0462', 'std:02762', 'std:06244',
                     'std:04364', 'std:04259', 'std:03592', 'std:022', 'std:06255', 'std:0571', 'std:0281', 'std:07162',
                     'std:0532', 'std:08232', 'std:02792', 'std:06276', 'std:02838', 'std:04146', 'std:08373', 'std:0154',
                     'std:04175', 'std:04324', 'std:04632', 'std:0477', 'std:02766', 'std:05921', 'std:06345',
                     'std:02632', 'std:06324', 'std:0471', 'std:04174', 'std:05362', 'std:0479', 'std:0824', 'std:0131',
                     'std:0621', 'std:0265', 'std:020', 'std:04567', 'std:080', 'std:01382', 'std:06272', 'std:040',
                     'std:0497', 'std:0452', 'std:033', 'std:0755', 'std:0821', 'std:05872', 'std:05692', 'std:0422',
                     'std:04116', 'std:05852', 'std:04563', 'std:0612', 'std:0172', 'std:06452', 'std:0268', 'std:04575',
                     'std:0820', 'std:04112', 'std:02692', 'std:0135', 'std:01461', 'std:0832', 'std:06466', 'std:02752',
                     'std:0431', 'std:0424', 'std:04344', 'std:08676', 'std:0278', 'std:0542', 'std:0562', 'std:0671',
                     'std:05862', 'std:0288', 'std:02637', 'std:0141', 'std:01421', 'std:011', 'std:05271', 'std:05542',
                     'std:05282', 'std:08288'] if cities is None else cities
        message = {
            "intent": {
                "fulfillment":
                    {
                        "type": "Delivery"
                    },
                "payment":
                    {
                        "@ondc/org/buyer_app_finder_fee_type": "percent",
                        "@ondc/org/buyer_app_finder_fee_amount": "3"
                    }
            }
        }
    else:
        city_list = ["*"] if cities is None else cities
        if mode == "start_and_stop":
            message = {
                "intent":
                    {
                        "payment":
                            {
                                "@ondc/org/buyer_app_finder_fee_type":"percent",
                                "@ondc/org/buyer_app_finder_fee_amount":"3"
                            },
                        "tags":
                            [
                                {
                                    "code":"catalog_inc",
                                    "list":
                                        [
                                            {
                                                "code":"start_time",
                                                "value":start_time
                                            },
                                            {
                                                "code":"end_time",
                                                "value":end_time
                                            }
                                        ]
                                }
                            ]
                    }
            }
        else:
            message = {
                "intent": {
                    "payment":
                        {
                            "@ondc/org/buyer_app_finder_fee_type":"percent",
                            "@ondc/org/buyer_app_finder_fee_amount":"3"
                        },
                    "tags":
                        [
                            {
                                "code":"catalog_inc",
                                "list":
                                    [
                                        {
                                            "code":"mode",
                                            "value":mode
                                        }
                                    ]
                            }
                        ]
                }
            }

    for d in domain_list:
        for c in city_list:
            if search_type == SearchType.INC and mode == "stop":
                transaction_id = get_transaction_id_of_last_start(d, c)
                if transaction_id is None:
                    log_error(f"Transaction-id not found for start for {d}")
                    continue
            else:
                transaction_id = str(uuid.uuid4())
            search_payload = {
                "context": {
                    "domain": d,
                    "action": "search",
                    "country": "IND",
                    "city": c,
                    "core_version": "1.2.0",
                    "bap_id": get_config_by_name("BAP_ID"),
                    "bap_uri": get_config_by_name("BAP_URL"),
                    "transaction_id": transaction_id,
                    "message_id": str(uuid.uuid4()),
                    "timestamp": end_time,
                    "ttl": "PT30S"
                },
                "message": message
            }
            search_payload_list.append(search_payload)

    for x in search_payload_list:
        dump_request_and_make_gateway_search(search_type, x)
        time.sleep(1)


def get_transaction_id_of_last_start(domain, city):
    search_collection = get_mongo_collection('request_dump')
    query_object = {"action": "search", "request.context.domain": domain, "request.context.city": city,
                    "request.message.intent.tags.list.value": "start"}
    catalog = mongo.collection_find_one_with_sort(search_collection, query_object, "created_at")
    return catalog['request']['context']['transaction_id'] if catalog else None


def dump_request_and_make_gateway_search(search_type, search_payload):
    headers = {'X-ONDC-Search-Response': search_type.value}
    entry_object_id = dump_request_payload("search", search_payload)
    resp = gateway_search(search_payload, headers)
    update_dumped_request_with_response(entry_object_id, resp)


def make_full_catalog_search_requests(domains=None, cities=None):
    make_http_requests_for_search_by_city(SearchType.FULL, domains=domains, cities=cities)


def make_incremental_catalog_search_requests(domains=None, cities=None, mode="start"):
    make_http_requests_for_search_by_city(SearchType.INC, domains, cities, mode)


def make_search_operation_along_with_incremental():
    make_incremental_catalog_search_requests(mode="stop")
    make_incremental_catalog_search_requests(mode="start")


if __name__ == '__main__':
    make_search_operation_along_with_incremental()
