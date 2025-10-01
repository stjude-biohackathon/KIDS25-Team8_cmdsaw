"""1. WDL Task Agent - Parse full JSON output to create WDL module with structure shown below. Must follow the WDL 1.2 Spec.
     1. This may require some thought to generate directories and output files in a way that makes sense.
     2. Or creating tools to allow an agent to make a directory and write to file.
   2. WDL README Agent - Create README file for the module.
   3. WDL Test Agent - Generate minimal tests assuming proper inputs files are provided. Keep it basic. 
     Skip by default, must be enabled with --add-tests. Maybe skip this for now, might need deeper thought."""


# Take input the structured JSON output from previous agent,
# Return WDL module as .wdl file, README.md, and optional test files if enabled