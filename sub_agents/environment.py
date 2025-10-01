"""1. If version data captured, attempt to collect conda, Docker, and Singularity (Apptainer) environment info via the Biocontainers API. 
    Biocontainers automatically makes images for all software in bioconda. 
    These images/environments being specified in the WDL task or Nextflow process means the user doesn't have to worry about 
    installing them - they'll be downloaded (and cached) automatically and used to run the process.
    1. For samtools version 1.21, a proper response (response code 200) looks like this (a 404 will be returned if the tool isn't found). 
    This is mildly confusing, as there may be multiple options in the output, but we will just take the last set.
    2. Output for this example will just be JSON like:

{
  "containers":
    {
      "bioconda": "samtools==1.21--h96c455f_1",
      "docker": "biocontainers/samtools:1.21--h96c455f_1",
      "singularity": "https://depot.galaxyproject.org/singularity/samtools:1.21--h96c455f_1"
    }
}

"""

# Take input the tool name and version (if available),
# Return structured JSON output with conda, docker, and singularity environment info if found