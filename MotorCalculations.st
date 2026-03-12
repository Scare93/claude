(* ============================================================================
   MotorCalculations
   Computes normalized motor health and performance metrics from real-time
   sensor data. All deviation outputs are dimensionless percentages so they
   are comparable across motor sizes and operating points.

   Assumes a centrifugal (variable-torque) load — torque proportional to
   speed squared.  Torque input is percent of rated (%).

   Requires: STAFF WORK.Bryan's Folder.Logic.round2decimels
             (enable via Logic > Libraries)
   ============================================================================ *)
PROGRAM MotorCalculations

(* --- Inputs: read from top-level template points --- *)
VAR
    PowerKW       AT %I(..PowerkW)       : LREAL;
    NameplateRPM  AT %I(..Nameplate rpm)  : LREAL;
    Frequency     AT %I(..Frequency)      : LREAL;
    RPM           AT %I(..RPM)            : LREAL;
    Torque        AT %I(..Torque)         : LREAL;   (* percent of rated *)
    Current       AT %I(..Current)        : LREAL;
    Pressure      AT %I(..Pressure)       : LREAL;
END_VAR

(* --- Outputs: read/write to variables folder --- *)
VAR
    IsRunning          AT %M(.variables.is running)            : BOOL;
    RatedSlipDeviation AT %M(.variables.Rated Slip deviation)  : LREAL;  (* slip as % of synchronous speed *)
    ALD                AT %M(.variables.ALD)                   : LREAL;  (* % deviation from expected load *)
    EfficiencyIndex    AT %M(.variables.Efficiency Index)      : LREAL;  (* relative efficiency proxy — trend only, not absolute *)
    EnergyPerPSI       AT %M(.variables.Energy per psi)        : LREAL;
    SpecificSlip       AT %M(.variables.Specific Slip)         : LREAL;  (* slip per unit load — trend for bearing/rotor health *)
END_VAR

(* --- Internal working variables --- *)
VAR
    Poles            : LREAL;
    SynchronousSpeed : LREAL;
    Slip             : LREAL;
    ExpectedTorque   : LREAL;
    SpeedRatio       : LREAL;
    LoadFraction     : LREAL;
END_VAR

(* --- Library reference: STAFF WORK.Bryan's Folder.Logic.round2decimels --- *)
VAR
    R2 : round2decimels;
END_VAR

(* ==== Main logic ==== *)

(* Motor is considered running above 10 kW *)
IsRunning := PowerKW > 10.0;

IF IsRunning AND (NameplateRPM > 0.0) THEN

    (* --- Pole count: nearest EVEN integer from nameplate speed --- *)
    Poles := DINT_TO_LREAL(TRUNC(7200.0 / NameplateRPM + 0.5));
    (* Force even — round odd result to nearest even *)
    IF (TRUNC(Poles) MOD 2) <> 0 THEN
        Poles := Poles + 1.0;
    END_IF;

    IF Poles > 0.0 THEN

        (* --- Speed & slip calculations --- *)
        R2(VarIn := 120.0 * Frequency / Poles, OUT1 => SynchronousSpeed);
        R2(VarIn := SynchronousSpeed - RPM, OUT1 => Slip);

        (* --- Normalized slip (% of synchronous speed) --- *)
        (* Stable denominator, comparable across motor sizes *)
        IF SynchronousSpeed > 0.0 THEN
            R2(VarIn := (Slip / SynchronousSpeed) * 100.0, OUT1 => RatedSlipDeviation);
        END_IF;

        (* --- Torque & normalized load analysis --- *)
        SpeedRatio := RPM / NameplateRPM;
        R2(VarIn := EXPT(SpeedRatio, 2) * 100.0, OUT1 => ExpectedTorque);

        (* Normalized ALD (%): positive = overloaded, negative = underloaded *)
        IF ExpectedTorque > 0.0 THEN
            R2(VarIn := ((Torque - ExpectedTorque) / ExpectedTorque) * 100.0, OUT1 => ALD);
        END_IF;

        (* --- Efficiency Index (relative proxy, not absolute efficiency) --- *)
        (* Torque% * RPM is proportional to mechanical output.              *)
        (* Dividing by electrical input (PowerKW) gives a value proportional *)
        (* to true efficiency. Absolute value is meaningless — trend it.     *)
        (* A dropping trend at similar load = motor losing efficiency.       *)
        IF PowerKW > 0.0 THEN
            R2(VarIn := (Torque * RPM) / (PowerKW * NameplateRPM) * 100.0, OUT1 => EfficiencyIndex);
        END_IF;

        (* --- Energy intensity --- *)
        IF Pressure > 0.0 THEN
            R2(VarIn := PowerKW / Pressure, OUT1 => EnergyPerPSI);
        END_IF;

        (* --- Load-normalized health trending --- *)
        (* Only computed above 20% load to avoid noise at light loads *)
        IF Torque > 20.0 THEN
            LoadFraction := Torque / 100.0;
            R2(VarIn := Slip / LoadFraction, OUT1 => SpecificSlip);
        END_IF;

    END_IF;  (* Poles > 0 *)
END_IF;  (* IsRunning *)

END_PROGRAM
