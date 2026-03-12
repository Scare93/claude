(* ============================================================================
   MotorCalculations

   Computes motor health and performance metrics from real-time sensor data.
   Assumes a centrifugal (variable-torque) load — torque proportional to speed².

   Rounding helper: R2(x) = DINT_TO_LREAL(TRUNC(x * 100.0 + 0.5)) / 100.0
   This pattern rounds an LREAL to 2 decimal places and is used throughout.
   ============================================================================ *)
PROGRAM MotorCalculations

(* --- Inputs: read from top-level template points --- *)
VAR
    PowerKW       AT %I(..PowerkW)        : LREAL;
    NameplateRPM  AT %I(..Nameplate rpm)   : LREAL;
    Frequency     AT %I(..Frequency)       : LREAL;
    RPM           AT %I(..RPM)             : LREAL;
    Torque        AT %I(..Torque)          : LREAL;
    Current       AT %I(..Current)         : LREAL;
    Pressure      AT %I(..Pressure)        : LREAL;
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
    UseAFI          : BOOL;    (* Alternate efficiency formula flag *)
    Poles           : LREAL;
    SynchronousSpeed: LREAL;
    RatedRPM        : LREAL;
    Slip            : LREAL;
    RatedSlip       : LREAL;
    ExpectedTorque  : LREAL;
    SpeedRatio      : LREAL;
END_VAR

(* ---- Main logic ---- *)

(* Motor is considered running above 10 kW *)
IsRunning := PowerKW > 10.0;

IF NOT IsRunning THEN
    RETURN;
END_IF;

(* --- Speed calculations --- *)

(* Pole count: nearest even integer from nameplate speed *)
Poles := DINT_TO_LREAL(TRUNC(7200.0 / NameplateRPM + 0.5));

(* Synchronous speed = (120 × line frequency) / poles *)
SynchronousSpeed := DINT_TO_LREAL(TRUNC((120.0 * Frequency / Poles) * 100.0 + 0.5)) / 100.0;

(* Rated RPM at nominal 60 Hz *)
RatedRPM := DINT_TO_LREAL(TRUNC((7200.0 / Poles) * 100.0 + 0.5)) / 100.0;

(* --- Slip calculations --- *)

Slip      := DINT_TO_LREAL(TRUNC((SynchronousSpeed - RPM) * 100.0 + 0.5)) / 100.0;
RatedSlip := DINT_TO_LREAL(TRUNC((RatedRPM - NameplateRPM) * 100.0 + 0.5)) / 100.0;

(* How far actual slip deviates from rated slip — indicates mechanical load changes *)
RatedSlipDeviation := DINT_TO_LREAL(TRUNC((Slip - RatedSlip) * 100.0 + 0.5)) / 100.0;

(* --- Torque & load analysis --- *)

(* Expected torque for centrifugal loads follows the affinity law: T ∝ speed² *)
SpeedRatio     := RPM / NameplateRPM;
ExpectedTorque := DINT_TO_LREAL(TRUNC((EXPT(SpeedRatio, 2) * 100.0) * 100.0 + 0.5)) / 100.0;

(* Actual Load Deviation: positive = overloaded, negative = underloaded *)
ALD := DINT_TO_LREAL(TRUNC((Torque - ExpectedTorque) * 100.0 + 0.5)) / 100.0;

(* --- Efficiency --- *)

IF UseAFI AND (PowerKW < 100.0) THEN
    (* AFI method: mechanical power out / electrical power in *)
    Efficiency := DINT_TO_LREAL(TRUNC(((Torque * RPM) / (PowerKW * 100.0)) * 100.0 + 0.5)) / 100.0;
ELSE
    (* Default method *)
    Efficiency := DINT_TO_LREAL(TRUNC(((PowerKW / Current) * Torque) * 100.0 + 0.5)) / 100.0;
END_IF;

(* --- Energy intensity --- *)

IF Pressure > 0.0 THEN
    EnergyPerPSI := DINT_TO_LREAL(TRUNC((PowerKW / Pressure) * 100.0 + 0.5)) / 100.0;
END_IF;

END_PROGRAM
