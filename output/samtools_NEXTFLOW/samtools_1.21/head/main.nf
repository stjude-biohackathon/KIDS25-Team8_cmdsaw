process samtools_head {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools head ${ params.file } $input_file > result.out
    """
}