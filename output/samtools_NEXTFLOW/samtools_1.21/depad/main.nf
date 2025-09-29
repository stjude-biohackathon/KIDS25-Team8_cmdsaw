process samtools_depad {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools depad ${ params.file } $input_file > result.out
    """
}