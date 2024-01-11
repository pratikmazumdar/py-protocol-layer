import threading

from flask_restx import Namespace, Resource, reqparse

from main.cron.search_by_city import make_full_catalog_search_requests, make_incremental_catalog_search_requests, \
    make_search_operation_along_with_incremental
from main.utils.decorators import token_required

authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-KEY'
    }
}

cron_namespace = Namespace('cron', description='Cron Job Namespace', authorizations=authorizations)


@cron_namespace.route("/cron/search/full-catalog")
class FullCatalogSearch(Resource):

    def create_parser_with_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("domains", type=str, action='append')
        parser.add_argument("cities", type=str, action='append')
        return parser.parse_args()

    def long_running_task(self, **kwargs):
        args = kwargs.get('post_data', {})
        make_full_catalog_search_requests(args['domains'], args['cities'])

    @cron_namespace.doc(security='apikey')
    @token_required
    def post(self):
        args = self.create_parser_with_args()
        # make_full_catalog_search_requests(args['domains'], args['cities'])
        # return {"status": "success"}, 200
        thread = threading.Thread(target=self.long_running_task, kwargs={'post_data': args})
        thread.start()
        return {"status": "success"}, 200


@cron_namespace.route("/cron/search/incremental")
class IncrementalCatalogSearch(Resource):

    def create_parser_with_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("domains", type=str, action='append')
        parser.add_argument("cities", type=str, action='append')
        return parser.parse_args()

    @cron_namespace.doc(security='apikey')
    @token_required
    def post(self):
        args = self.create_parser_with_args()
        make_incremental_catalog_search_requests(args['domains'], args['cities'], mode="start_and_stop")
        return {"status": "success"}, 200


@cron_namespace.route("/cron/search/incremental-start")
class IncrementalCatalogSearch(Resource):

    def create_parser_with_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("domains", type=str, action='append')
        parser.add_argument("cities", type=str, action='append')
        return parser.parse_args()

    @cron_namespace.doc(security='apikey')
    @token_required
    def post(self):
        args = self.create_parser_with_args()
        make_incremental_catalog_search_requests(args['domains'], args['cities'], mode="start")
        return {"status": "success"}, 200


@cron_namespace.route("/cron/search/incremental-stop")
class IncrementalCatalogSearch(Resource):

    def create_parser_with_args(self):
        parser = reqparse.RequestParser()
        parser.add_argument("domains", type=str, action='append')
        parser.add_argument("cities", type=str, action='append')
        return parser.parse_args()

    @cron_namespace.doc(security='apikey')
    @token_required
    def post(self):
        args = self.create_parser_with_args()
        make_incremental_catalog_search_requests(args['domains'], args['cities'], mode="stop")
        return {"status": "success"}, 200


@cron_namespace.route("/cron/search/full-and-incremental")
class IncrementalCatalogSearch(Resource):

    @cron_namespace.doc(security='apikey')
    @token_required
    def post(self):
        make_search_operation_along_with_incremental()
        return {"status": "success"}, 200
