"""
Module to run a RESTful server to set and get the configuration.
"""


import datetime
import json
import os
import re
import shutil
import socket
import sys
import urllib
from http.server import BaseHTTPRequestHandler

from configuration import configuration
from data_sources import weather
from visualizers.visualizers import VISUALIZERS

VIEW_NAME_KEY = 'name'
MEDIA_TYPE_KEY = 'media_type'
MEDIA_TYPE_VALUE = 'application/json'

# Based on https://gist.github.com/tliron/8e9757180506f25e46d9

# EXAMPLES
# Invoke-WebRequest -Uri "http://localhost:8080/settings" -Method GET -ContentType "application/json"
# Invoke-WebRequest -Uri "http://localhost:8080/settings" -Method PUT -ContentType "application/json" -Body '{"night_category_proportion": 0.1}'
# curl localhost:8080/settings
# curl -X PUT -d '{"night_category_proportion": 0.1}' http://localhost:8080/settings

ERROR_JSON = {'success': False}


def get_visualizer_response() -> dict:
    return {
        configuration.VISUALIZER_INDEX_KEY: configuration.get_visualizer_index(VISUALIZERS),
        "visualizer_name": VISUALIZERS[configuration.get_visualizer_index(VISUALIZERS)].get_name(),
        "visualizer_count": len(VISUALIZERS)
    }


def __set_visualizer_index__(
    increment: int
) -> dict:
    configuration.update_configuration(
        {
            configuration.VISUALIZER_INDEX_KEY: configuration.get_visualizer_index() +
            increment
        })

    return get_visualizer_response()


def current_view(
    handler
) -> dict:
    return get_visualizer_response()


def next_view(
    handler
) -> dict:
    return __set_visualizer_index__(1)


def previous_view(
    handler
) -> dict:
    return __set_visualizer_index__(-1)


def get_settings(
    handler
) -> dict:
    """
    Handles a get-the-settings request.
    """
    if configuration.CONFIG is not None:
        result = configuration.CONFIG.copy()

        result.update(get_visualizer_response())

        return result
    else:
        return ERROR_JSON


def set_settings(
    handler
) -> dict:
    """
    Handles a set-the-settings request.
    """

    if configuration.CONFIG is not None:
        payload = handler.get_payload()
        print("settings/PUT:")
        print(payload)

        response = configuration.update_configuration(payload)
        response.update(get_visualizer_response())

        return response
    else:
        return ERROR_JSON


class ConfigurationHost(BaseHTTPRequestHandler):
    """
    Handles the HTTP response for status.
    """

    HERE = os.path.dirname(os.path.realpath(__file__))
    ROUTES = {
        r'^/settings': {'GET': get_settings, 'PUT': set_settings, MEDIA_TYPE_KEY: MEDIA_TYPE_VALUE},
        r'^/view/next': {'GET': next_view, MEDIA_TYPE_KEY: MEDIA_TYPE_VALUE},
        r'^/view/previous': {'GET': previous_view, MEDIA_TYPE_KEY: MEDIA_TYPE_VALUE},
        r'^/view': {'GET': current_view, MEDIA_TYPE_KEY: MEDIA_TYPE_VALUE}
    }

    def do_HEAD(
        self
    ):
        self.handle_method('HEAD')

    def do_GET(
        self
    ):
        self.handle_method('GET')

    def do_POST(
        self
    ):
        self.handle_method('POST')

    def do_PUT(
        self
    ):
        self.handle_method('PUT')

    def do_DELETE(
        self
    ):
        self.handle_method('DELETE')

    def get_payload(
        self
    ) -> dict:
        try:
            payload_len = int(self.headers.get('Content-Length'))
            payload = self.rfile.read(payload_len)

            if isinstance(payload, bytes):
                payload = payload.decode(encoding="utf-8")

            payload = json.loads(payload)
            return payload
        except Exception as ex:
            return {"get_payload:ERROR": str(ex)}

    def __handle_invalid_route__(
        self
    ):
        """
        Handles the response to a bad route.
        """
        self.send_response(404)
        self.end_headers()
        self.wfile.write('Route not found\n')

    def __handle_file_request__(
        self,
        route,
        method: str
    ):
        if method == 'GET':
            try:
                f = open(os.path.join(
                    ConfigurationHost.HERE, route['file']))
                try:
                    self.send_response(200)
                    if 'media_type' in route:
                        self.send_header(
                            'Content-type', route['media_type'])
                    self.end_headers()
                    shutil.copyfileobj(f, self.wfile)
                finally:
                    f.close()
            except Exception:
                self.send_response(404)
                self.end_headers()
                self.wfile.write('File not found\n')
        else:
            self.send_response(405)
            self.end_headers()
            self.wfile.write('Only GET is supported\n')

    def __finish_request__(
        self,
        route,
        method: str
    ):
        if method in route:
            content = route[method](self)
            if content is not None:
                self.send_response(200)
                if 'media_type' in route:
                    self.send_header(
                        'Content-type', route['media_type'])
                self.end_headers()
                if method != 'DELETE':
                    self.wfile.write(json.dumps(content).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write('Not found\n')
        else:
            self.send_response(405)
            self.end_headers()
            self.wfile.write(method + ' is not supported\n')

    def __handle_request__(
        self,
        route,
        method: str
    ):
        if method == 'HEAD':
            self.send_response(200)
            if 'media_type' in route:
                self.send_header('Content-type', route['media_type'])
            self.end_headers()
        else:
            if 'file' in route:
                self.__handle_file_request__(route, method)
            else:
                self.__finish_request__(route, method)

    def handle_method(
        self,
        method: str
    ):
        route = self.get_route()
        if route is None:
            self.__handle_invalid_route__()
        else:
            self.__handle_request__(route, method)

    def get_route(
        self
    ):
        for path, route in ConfigurationHost.ROUTES.items():
            if re.match(path, self.path):
                return route
        return None
