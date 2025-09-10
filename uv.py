from machine import Pin, ADC
from time import sleep

pot1 = ADC(26)
pot2 = ADC(27)

uv_sensitivity = 0.13

while True:
    pot_value1 = pot1.read_u16()*3.3/4096
    print("ADC/Voltage value : {:.6f} V".format(pot_value1))
    uv_intensity = pot_value1/uv_sensitivity
    print("UV Intensity: {:.6f} mW/cm²".format(uv_intensity))
    uv_ind = pot_value1/0.1
    print("UV Index : {:.6f}".format(uv_ind))
    photocurrent = pot_value1/4.3
    print("Photocurrent: {:.6f} A".format(photocurrent))
    irrad = photocurrent*9
    print("Irradiance : {:.6f} mW/cm²".format(irrad))
    print("------------------------------")
    
    pot_value2 = pot2.read_u16()*3.3/4096
    print("ADC/Voltage value : {:.6f} V".format(pot_value2))
    uv_intensity = pot_value2/uv_sensitivity
    print("UV Intensity: {:.6f} mW/cm²".format(uv_intensity))
    uv_ind = pot_value2/0.1
    print("UV Index : {:.6f}".format(uv_ind))
    photocurrent = pot_value2/4.3
    print("Photocurrent: {:.6f} A".format(photocurrent))
    irrad = photocurrent*9
    print("Irradiance : {:.6f} mW/cm²".format(irrad))
    print("------------------------------")
    print("------------------------------------------------------------------------------------------")
    sleep(0.5)