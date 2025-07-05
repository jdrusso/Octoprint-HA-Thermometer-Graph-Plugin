/*
 * View model for OctoPrint-HA-Thermometer-Graph
 *
 * Author: JD Russo
 * License: AGPL-3.0-or-later
 */
$(function() {
    function Ha_thermometer_graphViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];

        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Ha_thermometer_graphViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ /* "loginStateViewModel", "settingsViewModel" */ ],
        // Elements to bind to, e.g. #settings_plugin_ha_thermometer_graph, #tab_plugin_ha_thermometer_graph, ...
        elements: [ /* ... */ ]
    });
});
