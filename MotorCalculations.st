(* ============================================================================
   MotorCalculations
   Computes motor health and performance metrics from real-time sensor data.
   Assumes a centrifugal (variable-torque) load — torque proportional to speed squared.
   Requires: STAFF WORK.Bryan's Folder.Logic.round2decimels (enable via Logic > Libraries)
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
    AFI           : BOOL;    (* Alternate efficiency formula flag *)
    Poles            : LREAL;
    SynchronousSpeed : LREAL;
    RatedRPM         : LREAL;
    Slip             : LREAL;
    RatedSlip        : LREAL;
    ExpectedTorque   : LREAL;
    SpeedRatio       : LREAL;
END_VAR
(* --- Library reference: STAFF WORK.Bryan's Folder.Logic.round2decimels --- *)
VAR
    R2 : round2decimels;
END_VAR
(* ---- Main logic ---- *)
(* Motor is considered running above 10 kW *)
IsRunning := PowerKW > 10.0;
IF IsRunning THEN
    (* --- Speed calculations --- *)
    (* Pole count: nearest even integer from nameplate speed *)
    Poles := DINT_TO_LREAL(TRUNC(7200.0 / NameplateRPM + 0.5));
    (* Synchronous speed = (120 x line frequency) / poles *)
    R2(VarIn := 120.0 * Frequency / Poles, OUT1 => SynchronousSpeed);
    (* Rated RPM at nominal 60 Hz *)
    R2(VarIn := 7200.0 / Poles, OUT1 => RatedRPM);
    (* --- Slip calculations --- *)
    R2(VarIn := SynchronousSpeed - RPM, OUT1 => Slip);
    R2(VarIn := RatedRPM - NameplateRPM, OUT1 => RatedSlip);
    (* Normalized slip deviation: (actual - expected) / expected *)
    IF RatedSlip <> 0.0 THEN
        R2(VarIn := (Slip - RatedSlip) / RatedSlip, OUT1 => RatedSlipDeviation);
    ELSE
        RatedSlipDeviation := 0.0;
    END_IF;
    (* --- Torque & load analysis --- *)
    (* Expected torque for centrifugal loads follows the affinity law: T proportional to speed squared *)
    SpeedRatio := RPM / NameplateRPM;
    R2(VarIn := EXPT(SpeedRatio, 2) * 100.0, OUT1 => ExpectedTorque);
    (* Normalized Actual Load Deviation: (actual - expected) / expected *)
    IF ExpectedTorque <> 0.0 THEN
        R2(VarIn := (Torque - ExpectedTorque) / ExpectedTorque, OUT1 => ALD);
    ELSE
        ALD := 0.0;
    END_IF;
    (* --- Efficiency --- *)
    IF AFI AND (PowerKW < 100.0) THEN
        (* AFI method: mechanical power out / electrical power in *)
        R2(VarIn := (Torque * RPM) / (PowerKW * 100.0), OUT1 => Efficiency);
    ELSE
        (* Default method *)
        R2(VarIn := (PowerKW / Current) * Torque, OUT1 => Efficiency);
    END_IF;
    (* --- Energy intensity --- *)
    IF Pressure > 0.0 THEN
        R2(VarIn := PowerKW / Pressure, OUT1 => EnergyPerPSI);
    END_IF;
END_IF;
END_PROGRAM
