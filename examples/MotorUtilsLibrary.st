(* ============================================================================
   MotorUtils - ST Library

   Reusable function blocks for motor calculations.
   Create this as a Structured Text Library in ClearSCADA, then reference
   it from any program that needs these blocks.
   ============================================================================ *)

(* Round2: Rounds an LREAL value to 2 decimal places *)
FUNCTION_BLOCK Round2
VAR_INPUT
    Value : LREAL;
END_VAR
VAR_OUTPUT
    Result : LREAL;
END_VAR
    Result := DINT_TO_LREAL(TRUNC(Value * 100.0 + 0.5)) / 100.0;
END_FUNCTION_BLOCK
