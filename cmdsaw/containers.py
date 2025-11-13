import requests

def request_biocontainers(executable: str, version: str) -> dict:
    """Make request to BioContainers given an executable (tool name) and version."""
    url = f"https://api.biocontainers.pro/ga4gh/trs/v2/tools/{executable}/versions/{executable}-{version}"
    # Example: https://api.biocontainers.pro/ga4gh/trs/v2/tools/samtools/versions/samtools-1.19
    print(f"Running request for {executable}-{version}")
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()

            bioconda = docker = singularity = None
            images = data.get("images", [])
            # Loop through images and assign image name based on type
            for x in images:
                if x.get("image_type", "").lower() == "conda":
                    bioconda = x.get("image_name")
                elif x.get("image_type", "").lower() == "docker":
                    docker = x.get("image_name")
                elif x.get("image_type", "").lower() == "singularity":
                    singularity = x.get("image_name")
            return {
                "bioconda": bioconda,
                "docker": docker,
                "singularity": singularity
            }
        else:
            # In the case of a non-success HTTP status code
            return {"error": r.status_code, "message": r.text}
    except requests.Timeout:
        # Handle timeout specifically
        return {"error": "timeout", "message": "Request timed out"}
    except Exception as e:
        # For any other exceptions
        return {"error": "exception", "message": str(e)}