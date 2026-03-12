"""
Motor Performance Calculations

Converted from PLC function block diagram (FBD) to Python.
Calculates key motor parameters: poles, synchronous speed, slip,
expected torque, efficiency, and more.
"""

import math


def round2decimals(value: float) -> float:
    return round(value, 2)


def motor_calculations(
    PowerkW: float,
    Nameplaterpm: float,
    Frequency: float,
    RPM: float,
    Torque: float,
    Current: float,
    Pressure: float,
) -> dict:
    """
    Run all motor calculations when the motor is running (PowerkW > 10).

    Args:
        PowerkW:       Measured power in kilowatts
        Nameplaterpm:  Nameplate rated RPM of the motor
        Frequency:     Supply frequency (Hz)
        RPM:           Measured shaft RPM
        Torque:        Measured torque
        Current:       Measured current
        Pressure:      Measured pressure

    Returns:
        Dictionary of calculated motor parameters, or None if motor is not running.
    """

    # --- isrunning: PowerkW > 10 ---
    isrunning = PowerkW > 10
    if not isrunning:
        return None

    # --- Poles: TRUNC(7200 / Nameplaterpm + 0.5) converted to real ---
    Poles = float(math.trunc(7200 / Nameplaterpm + 0.5))

    # --- Synchronous speed: (120 * Frequency) / Poles ---
    Synchronousspeed = round2decimals((120 * Frequency) / Poles)

    # --- Rated RPM: 7200 / Poles ---
    RatedRPM = round2decimals(7200 / Poles)

    # --- Slip: Synchronousspeed - RPM ---
    Slip = round2decimals(Synchronousspeed - RPM)

    # --- Rated Slip: RatedRPM - Nameplaterpm ---
    RatedSlip = round2decimals(RatedRPM - Nameplaterpm)

    # --- Rated Slip Deviation: Slip - RatedSlip ---
    RatedSlipdeviation = round2decimals(Slip - RatedSlip)

    # --- Expected Torque: (RPM / Nameplaterpm) ^ 2 * 100 ---
    ExpectedTorque = round2decimals((RPM / Nameplaterpm) ** 2 * 100)

    # --- ALD (Actual Load Deviation): (ExpectedTorque - Torque) * -1.0 ---
    ALD = round2decimals(ExpectedTorque - Torque) * -1.0

    # --- Efficiency ---
    if PowerkW < 100:
        # Alternate formula: (Torque * RPM) / (PowerkW * 100)
        Efficiency = round2decimals((Torque * RPM) / (PowerkW * 100))
    else:
        # Standard formula: (PowerkW / Current) * Torque
        Efficiency = round2decimals((PowerkW / Current) * Torque)

    # --- Energy per PSI: PowerkW / Pressure ---
    Energyperpsi = round2decimals(PowerkW / Pressure)

    return {
        "Poles": Poles,
        "Synchronousspeed": Synchronousspeed,
        "RatedRPM": RatedRPM,
        "Slip": Slip,
        "RatedSlip": RatedSlip,
        "RatedSlipdeviation": RatedSlipdeviation,
        "ExpectedTorque": ExpectedTorque,
        "ALD": ALD,
        "Efficiency": Efficiency,
        "Energyperpsi": Energyperpsi,
    }


# --- Example usage ---
if __name__ == "__main__":
    results = motor_calculations(
        PowerkW=75,
        Nameplaterpm=1770,
        Frequency=60,
        RPM=1750,
        Torque=85,
        Current=95,
        Pressure=50,
    )

    if results:
        print("Motor Calculations")
        print("-" * 35)
        for key, value in results.items():
            print(f"  {key:.<25} {value}")
    else:
        print("Motor is not running (PowerkW <= 10)")
