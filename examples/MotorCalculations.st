PROGRAM MotorCalculations
(* Inputs - read from top-level template points *)
VAR
    PowerkW AT %I(..PowerkW) : LREAL;
    Nameplaterpm AT %I(..Nameplate rpm) : LREAL;
    Frequency AT %I(..Frequency) : LREAL;
    RPM AT %I(..RPM) : LREAL;
    Torque AT %I(..Torque) : LREAL;
    Current AT %I(..Current) : LREAL;
    Pressure AT %I(..Pressure) : LREAL;
END_VAR
(* Outputs - read/write to variables folder *)
VAR
    isrunning AT %M(..variables.is running) : BOOL;
    RatedSlipdeviation AT %M(..variables.Rated Slip deviation) : LREAL;
    ALD AT %M(..variables.ALD) : LREAL;
    Efficiency AT %M(..variables.Efficiency) : LREAL;
    Energyperpsi AT %M(..variables.Energy per psi) : LREAL;
END_VAR
(* Internal variables *)
VAR
    AFI : BOOL;
    Poles : LREAL;
    Synchronousspeed : LREAL;
    RatedRPM : LREAL;
    Slip : LREAL;
    RatedSlip : LREAL;
    ExpectedTorque : LREAL;
    temp : LREAL;
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
