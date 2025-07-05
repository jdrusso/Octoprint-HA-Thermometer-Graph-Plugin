# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import requests
import threading
import time

class HAThermometerGraphPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SimpleApiPlugin
):

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def __init__(self):
        self._temperature = None
        self._stop_event = threading.Event()
        self._thread = None

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            ha_url="http://homeassistant.local:8123",
            ha_token="",
            sensor_entity_id="sensor.your_thermometer",
            sensor_label="HA_Sensor",
            ignore_ssl_verify=False
        )

    ##~~ StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info("Starting HA Thermometer Graph background thread")
        self._thread = threading.Thread(target=self._background_worker)
        self._thread.daemon = True
        self._thread.start()

    def _background_worker(self):
        while not self._stop_event.is_set():
            try:
                url = "{}/api/states/{}".format(
                    self._settings.get(["ha_url"]).rstrip("/"),
                    self._settings.get(["sensor_entity_id"])
                )
                headers = {
                    "Authorization": "Bearer {}".format(self._settings.get(["ha_token"])),
                    "Content-Type": "application/json",
                }
                verify_ssl = not self._settings.get_boolean(["ignore_ssl_verify"])
                response = requests.get(url, headers=headers, timeout=5, verify=verify_ssl)
                if response.ok:
                    data = response.json()
                    self._temperature = float(data["state"])
            except Exception as e:
                self._logger.error("Failed to fetch temperature: {}".format(e))
            time.sleep(30)  # Fetch every 30 seconds

    ##~~ SimpleApiPlugin mixin

    def get_api_commands(self):
        return dict(get_temp=[])

    def on_api_command(self, command, data):
        if command == "get_temp":
            return dict(temperature=self._temperature)

    ##~~ AssetPlugin mixin

    def get_assets(self):
        return dict(
            js=["js/ha_thermometer_graph.js"],
            css=[],
            less=[]
        )

    ##~~ HookPlugin mixin

    def get_hooks(self):
        return {
            "octoprint.comm.protocol.temperatures.received": self.ha_temperature_hook
        }

    def ha_temperature_hook(self, comm_instance, parsed_temps, *args, **kwargs):
        # Inject HA temperature as a virtual tool using the configured label
        if self._temperature is not None:
            sensor_label = self._settings.get(["sensor_label"]) or "HA_Sensor"
            parsed_temps[sensor_label] = (self._temperature, None)
        return parsed_temps

__plugin_name__ = "HA Thermometer Graph"
__plugin_pythoncompat__ = ">=3.7,<4"
def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = HAThermometerGraphPlugin()
