version 1.2

task samtools_view {
  input {
    Boolean help = false
    Boolean version = false
    File input_file
    File output_file
  }

  command <<<
    samtools view ~{if (help) "--help" else ""} ~{if (version) "--version" else ""} ~{input_file} ~{output_file}
  >>>

  output {
    File string = "string"
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}