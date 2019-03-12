import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import gatt_server as egs
import advertisement as ea
import common

from common import BLUEZ_SERVICE_NAME, LE_ADVERTISING_MANAGER_IFACE, GATT_MANAGER_IFACE, GATT_CHRC_IFACE

MIDI_SERVICE_UUID = '03b80e5a-ede8-4b33-a751-6ce34ec4c700'
MIDI_CHARACTERISTIC_UUID = '7772e5db-3868-4112-a1a9-f2669d106bf3'
LOCAL_NAME = 'Andrea MIDI'

mainloop = None


class MIDICharacteristic(egs.Characteristic):
    def __init__(self, bus, index, service):
        flags = ['notify', 'read', 'write', 'write-without-response']
        super().__init__(bus, index, MIDI_CHARACTERISTIC_UUID, flags, service)
        self.add_descriptor(egs.CharacteristicClientDescriptionDescriptor(bus, 0, self))

    def StartNotify(self):
        print('MIDICharacteristic.StartNotify')

    def StopNotify(self):
        print('MIDICharacteristic.StopNotify')

    def ReadValue(self, options):
        print('MIDICharacteristic.ReadValue')
        return 0

    def WriteValue(self, value, options):
        print('MIDICharacteristic.WriteValue')


class MIDIService(egs.Service):
    def __init__(self, bus, index):
        super().__init__(bus, index, MIDI_SERVICE_UUID, True)
        self.add_characteristic(MIDICharacteristic(bus, 0, self))


class MIDIApplication(egs.Application):
    def __init__(self, bus):
        super().__init__(bus)
        self.add_service(MIDIService(bus, 0))


class MIDIAdvertisement(ea.Advertisement):
    def __init__(self, bus, index):
        super().__init__(bus, index, 'peripheral')
        self.add_service_uuid(MIDI_SERVICE_UUID)
        self.add_local_name(LOCAL_NAME)


def register_ad_cb():
    print('Advertisement registered')


def register_ad_error_cb(error):
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()


def register_app_cb():
    print('GATT application registered')


def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = common.find_adapter(bus)
    if not adapter:
        print('BLE adapter not found')
        return

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    app = MIDIApplication(bus)
    adv = MIDIAdvertisement(bus, 0)

    mainloop = GLib.MainLoop()

    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv.Release()

    ad_manager.UnregisterAdvertisement(adv)
    print('Advertisement unregistered')
    dbus.service.Object.remove_from_connection(adv)


if __name__ == '__main__':
    main()
