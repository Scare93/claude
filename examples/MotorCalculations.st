PROGRAM MotorCalculations
VAR
    (* Inputs *)
    PowerkW         : LREAL;
    Nameplaterpm    : LREAL;
    Frequency       : LREAL;
    RPM             : LREAL;
    Torque          : LREAL;
    Current         : LREAL;
    Pressure        : LREAL;
    AFI             : BOOL;
    (* Outputs *)
    isrunning           : BOOL;
    Poles               : LREAL;
    Synchronousspeed    : LREAL;
    RatedRPM            : LREAL;
    Slip                : LREAL;
    RatedSlip           : LREAL;
    RatedSlipdeviation  : LREAL;
    ExpectedTorque      : LREAL;
    ALD                 : LREAL;
    Efficiency          : LREAL;
    Energyperpsi        : LREAL;
    (* Internal *)
    temp                : LREAL;
END_VAR
(* Step 1: Running check *)
isrunning := PowerkW > 10;
IF isrunning THEN
    (* Step 2: Poles *)
    Poles := DINT_TO_LREAL(TRUNC(7200 / Nameplaterpm + 0.5));
    (* Step 3: Synchronous speed *)
    Synchronousspeed := DINT_TO_LREAL(TRUNC(((120 * Frequency) / Poles) * 100.0 + 0.5)) / 100.0;
    (* Step 4: Rated RPM *)
    RatedRPM := DINT_TO_LREAL(TRUNC((7200 / Poles) * 100.0 + 0.5)) / 100.0;
    (* Step 5: Slip *)
    Slip := DINT_TO_LREAL(TRUNC((Synchronousspeed - RPM) * 100.0 + 0.5)) / 100.0;
    (* Step 6: Rated Slip *)
    RatedSlip := DINT_TO_LREAL(TRUNC((RatedRPM - Nameplaterpm) * 100.0 + 0.5)) / 100.0;
    (* Step 7: Rated Slip Deviation *)
    RatedSlipdeviation := DINT_TO_LREAL(TRUNC((Slip - RatedSlip) * 100.0 + 0.5)) / 100.0;
    (* Step 8: Expected Torque *)
    temp := RPM / Nameplaterpm;
    ExpectedTorque := DINT_TO_LREAL(TRUNC((EXPT(temp, 2) * 100) * 100.0 + 0.5)) / 100.0;
    (* Step 9: ALD *)
    ALD := DINT_TO_LREAL(TRUNC((ExpectedTorque - Torque) * 100.0 + 0.5)) / 100.0 * -1.0;
    (* Step 10: Efficiency *)
    IF AFI AND (PowerkW < 100) THEN
        Efficiency := DINT_TO_LREAL(TRUNC(((Torque * RPM) / (PowerkW * 100)) * 100.0 + 0.5)) / 100.0;
    ELSE
        Efficiency := DINT_TO_LREAL(TRUNC(((PowerkW / Current) * Torque) * 100.0 + 0.5)) / 100.0;
    END_IF;
    (* Step 11: Energy per PSI *)
    IF Pressure > 0.0 THEN
        Energyperpsi := DINT_TO_LREAL(TRUNC((PowerkW / Pressure) * 100.0 + 0.5)) / 100.0;
    END_IF;
END_IF;
END_PROGRAM
