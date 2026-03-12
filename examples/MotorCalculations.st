(* ============================================================================
   Round2: Rounds a LREAL value to 2 decimal places.
   Used throughout MotorCalculations to keep outputs display-friendly.
   ============================================================================ *)
FUNCTION Round2 : LREAL
VAR_INPUT
    Value : LREAL;
END_VAR
    Round2 := DINT_TO_LREAL(TRUNC(Value * 100.0 + 0.5)) / 100.0;
END_FUNCTION


(* ============================================================================
   MotorCalculations

   Computes motor health and performance metrics from real-time sensor data.
   Assumes a centrifugal (variable-torque) load — torque proportional to speed².
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
SynchronousSpeed := Round2(120.0 * Frequency / Poles);

(* Rated RPM at nominal 60 Hz *)
RatedRPM := Round2(7200.0 / Poles);

(* --- Slip calculations --- *)

Slip      := Round2(SynchronousSpeed - RPM);
RatedSlip := Round2(RatedRPM - NameplateRPM);

(* How far actual slip deviates from rated slip — indicates mechanical load changes *)
RatedSlipDeviation := Round2(Slip - RatedSlip);

(* --- Torque & load analysis --- *)

(* Expected torque for centrifugal loads follows the affinity law: T ∝ speed² *)
SpeedRatio     := RPM / NameplateRPM;
ExpectedTorque := Round2(EXPT(SpeedRatio, 2) * 100.0);   (* percentage of full-load torque *)

(* Actual Load Deviation: positive = overloaded, negative = underloaded *)
ALD := Round2((Torque - ExpectedTorque) * 1.0);

(* --- Efficiency --- *)

IF UseAFI AND (PowerKW < 100.0) THEN
    (* AFI method: mechanical power out / electrical power in *)
    Efficiency := Round2((Torque * RPM) / (PowerKW * 100.0));
ELSE
    (* Default method *)
    Efficiency := Round2((PowerKW / Current) * Torque);
END_IF;

(* --- Energy intensity --- *)

IF Pressure > 0.0 THEN
    EnergyPerPSI := Round2(PowerKW / Pressure);
END_IF;

END_PROGRAM
