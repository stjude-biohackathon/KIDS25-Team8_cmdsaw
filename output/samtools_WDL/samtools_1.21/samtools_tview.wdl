version 1.2

task samtools_tview {
  input {
    Boolean help = false
    Boolean version = false
  }

  command <<<
    samtools tview ~{if (help) "--help" else ""} ~{if (version) "--version" else ""}
  >>>

  output {
    File stdout_file = stdout()
  }

  runtime {
    docker: "ubuntu:20.04"
  }
}