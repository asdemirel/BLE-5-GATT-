import gatt
import threading
import time
import configparser
import os

class AnyDevice(gatt.Device):
    def __init__(self,s_uuid,c_uuid,mac_address,manager,managed=True):
        super().__init__(mac_address,manager,managed=True)
        self.my_characteristic = None
        self.write_succeed = True
        self.my_services_result = False
        self.s_uuid = s_uuid
        self.c_uuid = c_uuid

    def services_resolved(self):
        super().services_resolved()
        s_uuid = []
        c_uuid = []
        for service in self.services:
            s_uuid.append(service.uuid)
            for characteristic in service.characteristics:
                c_uuid.append(characteristic.uuid)    
        device_information_service = next(
            s for s in self.services
            if s.uuid == self.s_uuid)
        self.my_characteristic = next(
            c for c in device_information_service.characteristics
            if c.uuid == self.c_uuid)
        self.my_services_result = True

    def characteristic_write_value_succeeded(self,characteristic):
        self.write_succeed = True

    def characteristic_write_value_failed(self,characteristic,error):
        self.write_succeed = False
        print('Connection Crashed')

class bluetooth():
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.readfp(open(r'configs.ini'))

        self.mac_address = self.config.get('Defaults','mac_address')  # Config dosyasından çektiğimiz gerekli parametreler.
        self.s_uuid = self.config.get('Defaults','s_uuid')            
        self.c_uuid = self.config.get('Defaults','c_uuid')

        os.system('systemctl restart bluetooth')
        os.system('sudo rfkill block bluetooth')
        os.system('sudo rfkill unblock bluetooth')
        time.sleep(0.5)    
        
        self.manager = gatt.DeviceManager(adapter_name='hci0')
        self.manager.start_discovery()
        print('INITIALIZING...')
        time.sleep(0.5)                      
        self.manager.stop_discovery()
        threading.Thread(target=self.manager.run).start()
        self.device = None    
        self.value = None
        self.initialize_bluetooth()
        
    def connect_device(self):
        print("Connecting...")
        start = time.time()
        self.device  = AnyDevice(mac_address= self.mac_address , manager = self.manager , managed = True, s_uuid= self.s_uuid, c_uuid= self.c_uuid)
        if self.device.is_connected():
            self.device.disconnect()   # cihaz characteristiklerine ulaşmak için.
            self.device.connect()
        else:
            self.device.connect()
        while not self.device.my_services_result:
            if (time.time() - start) > 5:
                self.device.connection_crash = True
                print("Connection Failed")
                os.system('sudo rfkill unblock bluetooth')
                time.sleep(1)
                return self.connect_device()
            pass
        self.write_succeed = True
        print("Connected.")


    def edit_sending_value(self,value):
        return [ord(b) for b in value]
    
    def send_value(self,value):
        if self.device.write_succeed :
            self.device.write_succeed = None
            self.device.my_characteristic.write_value(self.edit_sending_value(value))
            while self.device.write_succeed == None:
                time.sleep(0.01)
                pass
            if self.device.write_succeed == False:
                self.connect_device()
                #return self.send_value(value) #son degeri tutmak istersek
        

    def initialize_bluetooth(self):
        self.connect_device()

if __name__ == "__main__":  
    blue = bluetooth()
    state = ["0","0","0","0"]
    while True:
        blue.send_value(state)
    
