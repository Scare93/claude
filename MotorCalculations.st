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
    RatedSlipDeviation AT %M(.variables.Rated Slip deviation)  : LREAL;  (* % deviation from rated slip *)
    ALD                AT %M(.variables.ALD)                   : LREAL;  (* % deviation from expected load *)
    Efficiency         AT %M(.variables.Efficiency)            : LREAL;
    EnergyPerPSI       AT %M(.variables.Energy per psi)        : LREAL;
    SpecificSlip       AT %M(.variables.Specific Slip)         : LREAL;  (* slip per unit load — trend for bearing/rotor health *)
    SpecificPower      AT %M(.variables.Specific Power)        : LREAL;  (* kW per unit load — trend for efficiency loss *)
    SpecificCurrent    AT %M(.variables.Specific Current)      : LREAL;  (* amps per unit load — trend for winding/PQ issues *)
END_VAR

(* --- Internal working variables --- *)
VAR
    Poles            : LREAL;
    SynchronousSpeed : LREAL;
    RatedRPM         : LREAL;
    Slip             : LREAL;
    RatedSlip        : LREAL;
    ExpectedTorque   : LREAL;
    SpeedRatio       : LREAL;
    LoadFraction     : LREAL;   (* Torque / 100.0 — unitless load fraction *)
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

        (* --- Speed calculations --- *)
        R2(VarIn := 120.0 * Frequency / Poles, OUT1 => SynchronousSpeed);
        R2(VarIn := 7200.0 / Poles, OUT1 => RatedRPM);

        (* --- Slip calculations --- *)
        R2(VarIn := SynchronousSpeed - RPM, OUT1 => Slip);
        R2(VarIn := RatedRPM - NameplateRPM, OUT1 => RatedSlip);

        (* --- Normalized slip deviation (%) --- *)
        (* (actual slip - rated slip) / rated slip * 100 *)
        IF RatedSlip > 0.0 THEN
            R2(VarIn := ((Slip - RatedSlip) / RatedSlip) * 100.0, OUT1 => RatedSlipDeviation);
        END_IF;

        (* --- Torque & normalized load analysis --- *)
        SpeedRatio := RPM / NameplateRPM;
        R2(VarIn := EXPT(SpeedRatio, 2) * 100.0, OUT1 => ExpectedTorque);

        (* Normalized ALD (%): positive = overloaded, negative = underloaded *)
        IF ExpectedTorque > 0.0 THEN
            R2(VarIn := ((Torque - ExpectedTorque) / ExpectedTorque) * 100.0, OUT1 => ALD);
        END_IF;

        (* --- Efficiency (approximation — torque is in % of rated, not Nm) --- *)
        IF (Current > 0.0) AND (PowerKW > 0.0) THEN
            R2(VarIn := (PowerKW / Current) * Torque, OUT1 => Efficiency);
        END_IF;

        (* --- Energy intensity --- *)
        IF Pressure > 0.0 THEN
            R2(VarIn := PowerKW / Pressure, OUT1 => EnergyPerPSI);
        END_IF;

        (* --- Load-normalized health trending metrics --- *)
        (* Only computed above 20% load to avoid noise at light loads *)
        IF Torque > 20.0 THEN
            LoadFraction := Torque / 100.0;
            R2(VarIn := Slip / LoadFraction,    OUT1 => SpecificSlip);
            R2(VarIn := PowerKW / LoadFraction,  OUT1 => SpecificPower);
            R2(VarIn := Current / LoadFraction,  OUT1 => SpecificCurrent);
        END_IF;

    END_IF;  (* Poles > 0 *)
END_IF;  (* IsRunning *)

END_PROGRAM
