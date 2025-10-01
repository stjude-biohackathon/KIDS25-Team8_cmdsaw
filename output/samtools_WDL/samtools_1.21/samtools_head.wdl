version 1.2

task samtools_head {
  input {
    Boolean help = false
    Boolean version = false
  }

  command <<<
    samtools head ~{if (help) "--help" else ""} ~{if (version) "--version" else ""}
  >>>

  output {
    File stdout_file = stdout()
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}