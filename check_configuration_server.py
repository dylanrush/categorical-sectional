# Examples:
# curl localhost:8080/settings
# curl -X PUT -d '{"night_category_proportion": 0.1}' http://localhost:8080/settings

from configuration import configuration_server

host = configuration_server.WeatherMapServer()
host.run()
