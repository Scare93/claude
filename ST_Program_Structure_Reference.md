# ST Program Structure Reference

Before you begin to create your own ST programs, you need to be aware of the basic structure of an ST program.

## 1. The Start of the Program

ST programs begin with a `PROGRAM` keyword and a program name. This is followed by a `VAR` keyword and a list of variables.

## 2. The Variable Blocks

There are 2 types of VAR block—VAR blocks for internal variables and VAR blocks for direct and indirect variables. Variables of different types have to be defined in separate blocks.

### Internal Variables

For internal variables, the VAR block will begin with a `VAR` keyword. The variables are defined after the VAR keyword and use the format:

```
<name> : <type>;
```

### Direct and Indirect Variables

For direct and indirect variables, the VAR block will also begin with a `VAR` keyword. The variables are defined after the VAR keyword and use this format:

```
<name> <instruction> (<item>.<variable>) : <variable type>;
```

For example:

```
VAR
  Desc AT %I(.Valve.Position.CurrentStateDesc) : STRING;
END_VAR
```

Each VAR block is ended by an `END_VAR` keyword.

### Important: Separating Internal and Direct/Indirect Variables

**Internal variables and direct/indirect variables cannot be listed in the same VAR block.** You must create separate VAR lists for each type. The `END_VAR` keyword only has a semicolon at the end of the **final** VAR list.

Example:

```
VAR
  TimeCount : TIME;
END_VAR
VAR
  TimedStart AT %M(.Power.StartMotor.CurrentState) : BOOL;
END_VAR

IF TimeCount > T#60s THEN
  TimedStart := TRUE;
ELSE
  TimedStart := FALSE;
END_IF;
```

In this example, `TimeCount` is an internal variable (no `AT` binding) and `TimedStart` is a direct variable (with `AT %M` binding), so they must be in separate VAR blocks.

### Using the RETAIN Keyword

Normally, internal variables are not stored for use after the program or server has been reset. Similarly, they are not transferred to any standby servers.

However, you can use the `VAR RETAIN` keyword to store internal values so that:
- They are **not reset** to their initial values when the server or program is reset
- They are **transferred** to any standby servers

Format:

```
VAR RETAIN
  <name> : <type>;
END_VAR
```

Example:

```
VAR RETAIN
  TempConversion : INT;
END_VAR
```

Where `TempConversion` is the name of the internal variable and `INT` is the type of value that it represents (an integer).

### Direct Variables

Direct variables are values that are read from (or written to) items in the ClearSCADA database. You reference direct variables to allow programs to react to and apply changes to database values.

#### Using the VAR List to Access Direct Variables

Direct variables are defined in a VAR list after the `PROGRAM` keyword using this syntax:

```
VAR
  <Name of variable> AT <AccessType>(<path.to.item.field>) : <Type of variable>;
END_VAR
```

Example:

```
VAR
  Input AT %I(..TemperatureSensor.CurrentValueFormatted) : STRING;
END_VAR;
```

In this example, the variable is read-only (`%I`), read from the `CurrentValueFormatted` tag of the `TemperatureSensor` item. The two periods (`..`) indicate a relative reference in the hierarchy.

#### Access Types

| Characters | Access Type |
|------------|------------|
| `%I` | Read Only |
| `%Q` | Write Only |
| `%M` | Read and Write |

#### Specifying Fields

When referencing a database item, you can specify a field or let the program use the default field (e.g., `CurrentValue` for points). To specify a field, add the field name to the end of the item's path with a period separator:

```
Desc AT %I(.Valve.Position.CurrentStateDesc) : STRING;
```

This references the `CurrentStateDesc` field as a read-only string value.

**Direct variables must be separated from internal variables, constants, and function blocks in the VAR lists.**

#### Example: Reading a Point Value and Writing it to Another Point

```
PROGRAM ReadTempWriteTemp
VAR
  Input AT %I(TemperatureSensor1.CurrentValue) : REAL;
  Output AT %M(TemperatureSensor2.CurrentValue) : REAL;
END_VAR;
Output := Input;
END_PROGRAM
```

`%I` reads a value from the database and `%M` is used to write a value to the database (`%M` can both read and write).

#### Alternative Access Methods

The VAR list is the most common way to access direct variables. However, alternatives are more effective in certain situations:

- **`VAR NOCACHE`** — Use when your program must not use cached values. Required when values accumulate with each execution of the program.
- **Database Object Structures** — Use when your program references the same properties for a large number of database items of the same type. Reduces time and effort to create references.
- **SQL Queries** — Use when your program needs to access multiple database items that meet certain criteria but are not named explicitly in the program. SQL queries can be included within the ST program.
- **Vectors** — Use when your program needs to read/write values from/to an array.
- **Historic Values** — Use when you need to access historic values.

**Important: Parentheses in database item names** — If a database item's name includes parentheses `( )`, each opening parenthesis must be paired with a closing parenthesis. Unpaired parentheses (e.g., `"Analog Point (4"` or `"Analog Point (4))"`) will cause compile errors. Multiple sets of parentheses compile successfully, including nested (e.g., `"Analog Point (4)"` or `"Analog Point (4(x))"`).

### Rules for Using Variables

1. Define the type for any arguments.
2. Separate each argument type with a comma. For example, `STRING, BYTE, STRING;` means there are 3 arguments: the first is a string, the second is a byte, and the final argument is a string.
3. Use `VAR INPUT` definitions to allow the ST program to receive inputs from a user/another ST program. The `VAR INPUT` keyword needs to be included in the recipient program (so, if one ST program receives the inputs for its indirect variables from another program, the program that receives the inputs has to have `VAR INPUTS`).
4. Define the `VAR INPUTS` in the same order in which they are to be executed. To allow a program to use the values from another program, the arguments for the indirect variables' inputs have to be in the same order in both programs. For example, Program 1 defines a method that has outputs in this order: `STRING, BYTE`. These values are output to Program 2. In Program 2, the `VAR INPUT` definition has to define that the first argument is a `STRING` and the second argument is a `BYTE` as this is the order defined in Program 1.
5. Set the Interval to `0s` on the ST Program Form for the recipient ST program. Programs that use manually entered input values or input values from other programs cannot be executed on an interval basis. However, they can be executed by another program (the other program executes the recipient ST program at a regular interval), according to a schedule, and manually. If required, configure a schedule to execute the program at specific times (see *Using Schedules to Automate Regular Functions* in the ClearSCADA Guide to Core Configuration). If you execute a recipient ST program manually, you will be prompted to enter the input value. You need to enter the input value in the dialog box and select the OK button to proceed. You will only be prompted to enter a value if the recipient program has inputs defined, but the inputs are not associated with other programs.

## 3. The Method Block

If an ST program uses methods, the methods are defined in a `METHOD` block. The METHOD block has to follow the VAR block(s) and also come before the ST code for the program. If the ST program does not use methods, there is no METHOD block and the ST code for the program follows the last VAR block.

The METHOD block begins with a `METHOD` keyword. The methods that the program uses are listed and use this format:

```
<name> <instruction> (<item>.<method>) : <argument types>;
```

For example:

```
METHOD
  OVR AT %M(AIs.AnalogInp.Override) : LREAL;
END_METHOD
```

The METHOD block is ended by an `END_METHOD` keyword.

## 4. The ST Code

The ST code for the program follows the METHOD block (or the last VAR block if there is no METHOD block). This can include statements, expressions, and operators.

## 5. The End of the Program

Each ST program is ended with the `END_PROGRAM` keyword.

## Full Example

In the following basic example, the ST program contains 3 variables and 3 methods. ST programs can contain as many variables and methods as required.

Entries in angle brackets `< >` indicate a name or type that you have to enter for the program. These will vary depending on the items you want to reference and the names you want to use. You should not enter the angle brackets in your ST programs.

```
PROGRAM <program name>

VAR
  <name> : <type>;
  <name> : <type>;
  <name> : <type>;
END_VAR

METHOD
  <name> AT %M(<location and name of item>.<method>) : <argument types>;
  <name> AT %M(<location and name of item>.<method>) : <argument types>;
  <name> AT %M(<location and name of item>.<method>) : <argument types>;
END_METHOD

<ST code>;
<ST code>;
<ST code>;

END_PROGRAM
```

### Structure Summary

1. `PROGRAM` definition and program name
2. `VAR` block(s) — variable names and types, ended by `END_VAR`
3. `METHOD` block (optional) — method definitions, ended by `END_METHOD`
4. ST code — the program logic (statements, expressions, operators)
5. `END_PROGRAM` — closes the program
