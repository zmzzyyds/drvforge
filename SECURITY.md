# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.1.x | yes |

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities. Instead,
use GitHub's private vulnerability reporting ("Report a vulnerability" under
the Security tab), or email the repository owner.

Include:

- drvforge version and Python version
- the template and command line involved
- for issues in **generated driver code**: the kernel version and, if
  possible, a description of how the generated code could be misused
  (missing bounds checks, unsafe copy_to_user usage, etc.)

Generated kernel code is security-sensitive: reports about missing
validation in templates are treated as high priority.

## What is in scope

- The drvforge generator and CLI
- Driver template code that runs in kernel space

## What is out of scope

- Bugs in the Linux kernel itself (report to kernel maintainers)
- User-modified generated code
