process samtools_view {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools view ${ params.b ? '-b ' + params.b : '' } ${ params.h ? '-h ' + params.h : '' } $input_file > result.out
    """
}