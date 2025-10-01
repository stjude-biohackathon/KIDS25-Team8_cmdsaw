version 1.2

task samtools_depad {
  input {
    # No inputs
  }

  command <<<
    samtools depad
  >>>

  output {
    File stdout_file = stdout()
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}