process samtools_tview {
    input:
        path input_file optional true

    output:
        path("*.out")

    script:
    """
    samtools tview ${ params.file } $input_file > result.out
    """
}