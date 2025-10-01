process samtools_flags {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools flags $input_file > result.out
    """
}