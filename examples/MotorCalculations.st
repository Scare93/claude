(* ============================================================================
   MotorCalculations

   Computes motor health and performance metrics from real-time sensor data.
   Assumes a centrifugal (variable-torque) load — torque proportional to speed squared.

   Requires: Round2 ST Library (enable via Logic > Libraries in Design mode)
   ============================================================================ *)
PROGRAM MotorCalculations

(* --- Inputs: read from top-level template points --- *)
VAR
    PowerKW       AT %I(..PowerkW)       : LREAL;
    NameplateRPM  AT %I(..Nameplate rpm)  : LREAL;
    Frequency     AT %I(..Frequency)      : LREAL;
    RPM           AT %I(..RPM)            : LREAL;
    Torque        AT %I(..Torque)         : LREAL;
    Current       AT %I(..Current)        : LREAL;
    Pressure      AT %I(..Pressure)       : LREAL;
END_VAR

(* --- Outputs: read/write to variables folder --- *)
VAR
    IsRunning          AT %M(.variables.is running)            : BOOL;
    RatedSlipDeviation AT %M(.variables.Rated Slip deviation)  : LREAL;
    ALD                AT %M(.variables.ALD)                   : LREAL;
    Efficiency         AT %M(.variables.Efficiency)            : LREAL;
    EnergyPerPSI       AT %M(.variables.Energy per psi)        : LREAL;
END_VAR

(* --- Internal working variables --- *)
VAR
    UseAFI           : BOOL;    (* Alternate efficiency formula flag *)
    Poles            : LREAL;
    SynchronousSpeed : LREAL;
    RatedRPM         : LREAL;
    Slip             : LREAL;
    RatedSlip        : LREAL;
    ExpectedTorque   : LREAL;
    SpeedRatio       : LREAL;
END_VAR

(* --- Library reference: Round2 ST Library --- *)
VAR
    R2 : Round2;
END_VAR

(* ---- Main logic ---- *)

(* Motor is considered running above 10 kW *)
IsRunning := PowerKW > 10.0;

IF IsRunning THEN

    (* --- Speed calculations --- *)

    (* Pole count: nearest even integer from nameplate speed *)
    Poles := DINT_TO_LREAL(TRUNC(7200.0 / NameplateRPM + 0.5));

    (* Synchronous speed = (120 x line frequency) / poles *)
    R2(Value := 120.0 * Frequency / Poles, Result => SynchronousSpeed);

    (* Rated RPM at nominal 60 Hz *)
    R2(Value := 7200.0 / Poles, Result => RatedRPM);

    (* --- Slip calculations --- *)

    R2(Value := SynchronousSpeed - RPM, Result => Slip);
    R2(Value := RatedRPM - NameplateRPM, Result => RatedSlip);

    (* How far actual slip deviates from rated slip — indicates mechanical load changes *)
    R2(Value := Slip - RatedSlip, Result => RatedSlipDeviation);

    (* --- Torque & load analysis --- *)

    (* Expected torque for centrifugal loads follows the affinity law: T proportional to speed squared *)
    SpeedRatio := RPM / NameplateRPM;
    R2(Value := EXPT(SpeedRatio, 2) * 100.0, Result => ExpectedTorque);

    (* Actual Load Deviation: positive = overloaded, negative = underloaded *)
    R2(Value := Torque - ExpectedTorque, Result => ALD);

    (* --- Efficiency --- *)

    IF UseAFI AND (PowerKW < 100.0) THEN
        (* AFI method: mechanical power out / electrical power in *)
        R2(Value := (Torque * RPM) / (PowerKW * 100.0), Result => Efficiency);
    ELSE
        (* Default method *)
        R2(Value := (PowerKW / Current) * Torque, Result => Efficiency);
    END_IF;

    (* --- Energy intensity --- *)

    IF Pressure > 0.0 THEN
        R2(Value := PowerKW / Pressure, Result => EnergyPerPSI);
    END_IF;

END_IF;

END_PROGRAM
