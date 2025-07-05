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
            enabled=False,
            ha_url="http://homeassistant.local:8123",
            ha_token="",
            sensor_entity_id="sensor.your_thermometer",
            sensor_label="C",
            ignore_ssl_verify=False,
            poll_interval=5
        )

    ##~~ StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info("Starting HA Thermometer Graph background thread")
        self._thread = threading.Thread(target=self._background_worker)
        self._thread.daemon = True
        self._thread.start()

    def _background_worker(self):
        while not self._stop_event.is_set():
            interval = max(5, self._settings.get_int(["poll_interval"]))
            if not self._settings.get_boolean(["enabled"]):
                self._logger.debug("Plugin not enabled, skipping poll")
                time.sleep(interval)
                continue
            try:
                self._logger.info("Making request")
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
                    self._logger.debug(f"Got temperature {self._temperature}")
                else:
                    self._temperature = None
                    self._logger.error(f"Failed to fetch temperature: {response.text}, {response.status_code}")
            except Exception as e:
                self._temperature = None
                self._logger.error("Failed to fetch temperature: {}".format(e))
            self._logger.debug(f"After making request, {self._temperature=}")
            time.sleep(interval)

    ##~~ SimpleApiPlugin mixin

    def get_api_commands(self):
        return dict(get_temp=[])

    def on_api_command(self, command, data):
        if command == "get_temp":
            return dict(temperature=self._temperature)

    ##~~ AssetPlugin mixin

    def get_assets(self):
        return dict(
            js=[],
            css=[],
            less=[]
        )

    ##~~ Hook

    def get_hooks(self):
        return {
            "octoprint.comm.protocol.temperatures.received": self.ha_temperature_hook
        }

    def ha_temperature_hook(self, comm_instance, parsed_temps, *args, **kwargs):
        # Inject HA temperature as the chamber ("C")
        if self._temperature is not None:
            parsed_temps["C"] = (self._temperature, None)
            self._logger.debug(f"HA temperature {self._temperature} injected as chamber (C)")
        return parsed_temps

__plugin_name__ = "HA Thermometer Graph"
__plugin_pythoncompat__ = ">=3.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    global __plugin_hooks__
    __plugin_implementation__ = HAThermometerGraphPlugin()
    __plugin_hooks__ = __plugin_implementation__.get_hooks()
