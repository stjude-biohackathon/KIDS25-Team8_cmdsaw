"""1. Nextflow Process Agent - Have another agent create Nextflow (nf-core) module as shown below. 
    This agent will only create the main.nf files, no tests.
   2. Nextflow Metadata Agent - Create meta.yml files.
   3. Nextflow Test Agent - Generate minimal tests assuming proper inputs files are provided. Keep it basic. 
    Skip by default, must be enabled with --add-tests. Maybe skip this for now, might need deeper thought."""


# Take input the structured JSON output from previous agent,
# Return Nextflow module as main.nf file, meta.yml, and optional test files if enabled