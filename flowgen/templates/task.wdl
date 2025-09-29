version 1.2

task {task_name} {{
  input {{
{inputs}
  }}

  command <<<
    {executable} {command_line}
  >>>

  output {{
{outputs}
  }}

  runtime {{
    docker: "ubuntu:20.04"
  }}
}}