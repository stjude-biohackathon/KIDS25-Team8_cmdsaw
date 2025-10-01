version 1.2

task samtools_flags {
  input {
    # No inputs
  }

  command <<<
    samtools flags
  >>>

  output {
    File stdout_file = stdout()
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}