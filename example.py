import logging
from autotermheater import AutotermHeater

heater_log_path = '/home/pi/AutotermHeaterController/appdata/logs/PlanarHeater.log'

heater = AutotermHeater(serial_num='A50285BI', log_path=heater_log_path, log_level=logging.INFO)

print('Connection with heater successfully initialized.')

while True:
    request = input('Enter your request: ')

    if request == 'ast':
        heater.asks_for_status()

    elif request == 'ase':
        heater.asks_for_settings()
    elif 'rct' in request:
        heater.report_controller_temperature(int(request.split(' ')[1]))
    elif request == 'ct':
        print(heater.get_controller_temperature())
    elif request == 'ht':
        print(heater.get_heater_temperature())
    elif request == 'et':
        print(heater.get_external_temperature())
    elif request == 'bv':
        print(heater.get_battery_voltage())
    elif request == 'ft':
        print(heater.get_flame_temperature())
    elif request == 'hs':
        print(heater.get_heater_status())
    elif request == 'hst':
        print(heater.get_heater_status_text())

    elif request == 'hmd':
        print(heater.get_heater_mode())
    elif request == 'hsp':
        print(heater.get_heater_setpoint())
    elif request == 'hvt':
        print(heater.get_heater_ventilation())
    elif request == 'hpl':
        print(heater.get_heater_power_level())

    elif 'sht' in request:
        heater.set_heater_timer(int(request.split(' ')[1]))
    elif request == 'ght':
        print(heater.get_heater_timer())
    elif 'vent_on' in request:
        if len(request.split(' ')) == 3:
            heater.turn_on_ventilation(int(request.split(' ')[1]), timer=int(request.split(' ')[2]))
        elif len(request.split(' ')) == 2:
            heater.turn_on_ventilation(int(request.split(' ')[1]))
        else:
            print('ERROR')
    elif 'heat_on' in request:
        if len(request.split(' ')) == 3:
            heater.turn_on_heater(mode=4, power=int(request.split(' ')[1]), timer=int(request.split(' ')[2]))
        elif len(request.split(' ')) == 2:
            heater.turn_on_heater(mode=4, power=int(request.split(' ')[1]))
        else:
            print('ERROR')
    elif 'heat_set' in request:
        heater.change_settings(mode=4, power=int(request.split(' ')[1]))
    elif 'heat_off' in request:
        heater.shutdown()

    elif request == 'diag on':
        heater.diagnostic_on()
    elif request == 'diag off':
        heater.diagnostic_off()
    elif request == 'dhs':
        print(heater.get_d_status())
    elif request == 'dc1':
        print(heater.get_d_counter1())
    elif request == 'dc2':
        print(heater.get_d_counter2())
    elif request == 'ddr':
        print(heater.get_d_defined_rev())
    elif request == 'dmr':
        print(heater.get_d_measured_rev())
    elif request == 'df1':
        print(heater.get_d_fuel_pump1())
    elif request == 'df2':
        print(heater.get_d_fuel_pump2())
    elif request == 'dct':
        print(heater.get_d_chamber_temperature())
    elif request == 'dft':
        print(heater.get_d_flame_temperature())
    elif request == 'det':
        print(heater.get_d_external_temperature())
    elif request == 'dht':
        print(heater.get_d_heater_temperature())
    elif request == 'dbv':
        print(heater.get_d_battery_voltage())
    else:
        print('Unknown request!')
