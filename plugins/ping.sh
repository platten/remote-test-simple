#/usr/bin/env bash

# Plugin Defaults
readonly DEFAULT_PING_COUNT=1

# Load Environmetal Variables if present
HOSTNAME=${HOSTNAME-""}
PING_COUNT=${PING_COUNT-${DEFAULT_PING_COUNT}}
PLUGIN_NAME=$0

# CONFIG FLAGS
readonly NON_HTTPS=true
readonly INSECURE_HTTPS=true

# Plugin required parameters
declare -A PREREQ_ARRAY=( [yq]="mikefarah/yq"
                          [ping]="platten/go-ping" )
declare -A HTTP_FALLBACK_URLS=( [yq]="https://github.com/mikefarah/yq/releases/download/2.4.1/yq_linux_amd64"
                                [ping]="https://github.com/platten/go-ping/releases/download/v1.29.2020/ping_linux_amd64" )

#
# EXIT codes
#
readonly SUCCESS=0
readonly TEST_FAILED=1
readonly MISSING_ARGUMENTS=2
readonly EXECUTABLE_NOT_FOUND=3
readonly DOWNLOAD_FAILURE=4

# Temporary variables
tmp_dir=""

#
# Main Script
#

main () {
    if [ -z "$1" ]; then
        if [ -z ${HOSTNAME} ]; then
            usage
        fi
    else
        HOSTNAME=$1
    fi
    check_and_download_prereqs
    ping_host "${HOSTNAME}"
}

#
# Plugin specific function(s)
#
ping_host() {
    # $1 hostname
    ping -c ${PING_COUNT} $1
    if [ $? != 0 ]; then
        error "Ping to $1 failed" ${TEST_FAILED}
    fi
    echo "Ping to $1 succeded"
    cleanup_tmp
    exit ${SUCCESS}
}

usage() {
    usage_msg="Usage: ${PLUGIN_NAME} <hostname> or HOSTNAME=<hostname> ${PLUGIN_NAME}"
    error usage_msg ${MISSING_ARGUMENTS}
}



#
# Generic Function library, could be loa
#

download_program ()

get_download_url() {
    # $1 name of executable
    
    if [ ${NON_HTTPS} == true ]; then
        #Fallback to hardcoded URLs since GitHub API requires HTTPS
        echo "${HTTP_FALLBACK_URLS[$1]}"
    else
        github_location=${PREREQ_ARRAY[$1]}
        response=$(curl -s https://api.github.com/repos/${github_location}/releases/latest)
        if [[ $? != ${SUCCESS} ]]; then
            error "Problem downloading $1 using curl" ${DOWNLOAD_FAILURE}
        fi
        	wget -q -nv -O- https://api.github.com/repos/$1/$2/releases/latest 2>/dev/null |  jq -r '.assets[] | select(.browser_download_url | contains("linux-amd64")) | .browser_download_url'

        echo ${response} | grep "linux_amd64" \
                         | cut -d : -f 2,3 \
                         | tr -d \"
    fi
}

error() {
    # $1 is error message to be sent to STDERR
    # $2 is optional exit code
    echo "$1" 1>&2;

    # If exit code is specified then attempt to delete temporary directory and exit
    cleanup_tmp
    exit $2
}


cleanup_tmp() {
    if [[ ${tmp_dir} != "" ]]
        rm -rf $tmp_dir
    fi
}

download () {
    # $1 binary name
    # $2 URL to download from
    # $3 target download directory
    
    #TODO(platten): Add curl and wget error handling
    #TODO(platten): Add support for self-signed certs
    #TODO(platten): Add support for proxy
    
    if [[ ${NON_HTTPS} == true ]]; then
        url=$( echo $2 | sed s/https/http/ )
    else
        url=$2
    
    additional_args=""
    path_to_curl="$(which curl)"
    if [ -x "$(which curl)" ] ; then
        echo "Downloading $1 with curl from ${url}"
        if [[ ${INSECURE_HTTPS} == true ]]; then
            additional_args="-k"
        fi
        ${path_to_curl} -s -L ${additional_args} -o "$3/$1" "${url}"
        if [[ $? != ${SUCCESS} ]]; then
            error "Problem downloading $1 using curl" ${DOWNLOAD_FAILURE}
        fi
        chmod a+x "$3/$1"
    else
        path_to_wget="$(which wget)"
        if [ -x "$(which wget)" ] ; then
            echo "Downloading $1 with wget from: ${url}"
            if [[ ${INSECURE_HTTPS} == true ]]; then
                additional_args="--no-check-certificate"
            fi
            ${path_to_wget} -q -O ${additional_args} "$3/$1" "${url}"
            if [[ $? != ${SUCCESS} ]]; then
                error "Problem downloading $1 using wget" ${DOWNLOAD_FAILURE}
            fi
        else
            error "FATAL: curl or wget not found, exiting" 1
        fi
    fi
}

check_and_download_prereqs() {
    for executable_name in "${!PREREQ_ARRAY[@]}"
    do
        echo -n "Checking for ${executable_name}: "
        local path_to_executable="$(which ${executable_name})"
        if [ -x "$path_to_executable" ] ; then
            echo "found!"
        else
            echo "not found.\n Downloading..."
            if [ -z ${tmp_dir} ]; then 
                tmp_dir=$(mktemp -d -t ci-XXXXXXXXXX)
                echo "Creating temporary directory ${tmp_dir}"
                export $PATH=$PATH:${tmp_dir}
            fi
            local download_url=$( get_download_url "${executable_name}")
            download "${executable_name}" "${download_url}" "${tmp_dir}"
        fi
    done
}

# TODO(platten): modify go ping executable to error when there not able to ping successfully (outside of the scope of this repo)
# TODO(platten): curl or wget detection should be done if need to download
# TODO(platten): support wget for getting latest GitHub URL
# TODO(platten): allow for non-https support when querying github URL or downloading
# TODO(platten): support 

main "$@"