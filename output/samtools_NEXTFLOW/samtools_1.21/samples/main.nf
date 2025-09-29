process samtools_samples {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools samples ${ params.b ? '-b ' + params.b : '' } ${ params.h ? '-h ' + params.h : '' } $input_file > result.out
    """
}