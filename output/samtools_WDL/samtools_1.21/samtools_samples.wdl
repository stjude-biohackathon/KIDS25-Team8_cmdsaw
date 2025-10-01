version 1.2

task samtools_samples {
  input {
    Boolean help = false
    Boolean version = false
    File files
  }

  command <<<
    samtools samples ~{if (help) "--help" else ""} ~{if (version) "--version" else ""} ~{files}
  >>>

  output {
    File stdout_file = stdout()
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}