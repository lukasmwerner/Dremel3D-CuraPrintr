import json

from cura.CuraApplication import CuraApplication

DREMEL3D_SETTINGS = "dremel3d/instances"


def _load_prefs():
    application = CuraApplication.getInstance()
    global_container_stack = application.getGlobalContainerStack()
    if not global_container_stack:
        return {}, None
    printer_id = global_container_stack.getId()
    p = application.getPreferences()
    s = json.loads(p.getValue(DREMEL3D_SETTINGS))
    return s, printer_id


def init_config():
    application = CuraApplication.getInstance()
    p = application.getPreferences()
    p.addPreference(DREMEL3D_SETTINGS, json.dumps({}))


def get_config():
    s, printer_id = _load_prefs()
    if printer_id in s:
        return s[printer_id]
    return {}


def save_config(url):
    s, printer_id = _load_prefs()
    s[printer_id] = {"url": url}
    application = CuraApplication.getInstance()
    p = application.getPreferences()
    p.setValue(DREMEL3D_SETTINGS, json.dumps(s))
    return s


def delete_config(printer_id=None):
    s, active_printer_id = _load_prefs()
    if not printer_id:
        printer_id = active_printer_id
    if printer_id in s:
        del s[printer_id]
        application = CuraApplication.getInstance()
        p = application.getPreferences()
        p.setValue(DREMEL3D_SETTINGS, json.dumps(s))
        return True
    return False
