#!/usr/bin/env bash

# Styles
declare -r style_red="\033[0;91m"
declare -r style_green="\033[0;92m"
declare -r style_cyan="\033[0;96m"
declare -r style_reset="\033[0m"

function script_dir {
    echo "$(dirname -- "$(readlink -f -- "$0")")"
}

function project_root_dir {
    echo "$(dirname -- "$(script_dir)")"
}

##
# Print the message with a style.
# $1 The escape code for the style.
# $2 The message.
#
function print_style {
    local style="$1"
    local message="$2"
    echo -e "${style}${message}${style_reset}"
}

##
# Print the message in red.
# $1 The message.
#
function print_red {
    print_style "${style_red}" "$1"
}

##
# Print the message in green.
# $1 The message.
#
function print_green {
    print_style "${style_green}" "$1"
}

##
# Print the message in cyan.
# $1 The message.
#
function print_cyan {
    print_style "${style_cyan}" "$1"
}

##
# Print the heading.
# $1 The heading.
#
function print_heading {
    local heading="$1"
    print_cyan "##############################################"
    print_cyan "### ${heading}"
    print_cyan "##############################################"
    echo
}

function install_python_modules {
    print_heading "Install Python Modules"
    pip3 install --upgrade pip setuptools wheel
    pip3 install -r "requirements.txt"
    exit_with_message_on_error $? "Failed to install Python modules"
}

function install_on_github_hosted_runner {
    install_python_modules
}

function help
{
    echo "Usage:"
    echo
    echo "setenv.sh"
    echo
    echo "Options:"
    echo
    echo "-h    Display the help message"
    echo
}

function main
{
    OPTIND=1         # Reset in case getopts has been used previously in the shell.
    while getopts ":hg" OPT_NAME; do
        case "${OPT_NAME}" in
        h)
            help
            return 0
            ;;
        \?)
            log "Unknown option ${OPTARG}"
            return 1
            ;;
        :)
            log "No argument value for option ${OPTARG}"
            return 1
            ;;    
        *)
            log "Unknown error occured when parsing options"
            return 1
            ;;
        esac
    done
    shift $((OPTIND -1))

    pushd "$(project_root_dir)" >/dev/null 2>&1    # Switch to project root directory
    echo "$0"
    echo "Working dir: $(pwd)"
    install_on_github_hosted_runner
    popd >/dev/null 2>&1
}

main "$@"
