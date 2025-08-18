# Reserved CLI options that are used by 'prich run' command
# and are not allowed to be user/defined in the template variables cli_option
RESERVED_RUN_TEMPLATE_CLI_OPTIONS = [
    "-g", "--global", "-q", "--quiet", "-o", "--output", "-p", "--provider",
    "-f", "--only-final-output", "-s", "--skip-llm", "-v", "--verbose"
]
