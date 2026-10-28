#!/usr/bin/env bash

set -o pipefail
umask 077

usage() {
    echo "Usage: $0 [target] [report_name]"
    echo
    echo "Arguments:"
    echo "  target        IPv4 address or hostname"
    echo "  report_name   Optional Nmap report filename (no extension required)"
    echo
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo
    echo "Examples:"
    echo "  $0 192.168.1.10"
    echo "  $0 example.com"
    echo "  $0 192.168.1.10 lab_scan"
    echo "  $0 example.com Reports/webserver"
}

error_exit() {
    echo "[!] Error: $1" >&2
    echo >&2
    usage >&2
    exit 1
}

# Check arguments.
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    "")
        error_exit "Target is required."
        ;;
    -*)
        error_exit "Invalid option '$1'."
        ;;
esac

[[ $# -le 2 ]] || error_exit "Provide a target and optional report name."

TARGET="$1"
REPORT="${2:-}"

# Validate IPv4 address.
is_valid_ipv4() {
    local ip="$1"
    local octet
    local -a octets

    [[ "$ip" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || return 1
    IFS='.' read -r -a octets <<< "$ip"

    for octet in "${octets[@]}"; do
        [[ "$octet" =~ ^(0|[1-9][0-9]{0,2})$ ]] || return 1
        (( 10#$octet <= 255 )) || return 1
    done

    return 0
}

# Validate DNS-style hostname.
is_valid_hostname() {
    local host="$1"
    local label
    local -a labels

    [[ ${#host} -le 253 ]] || return 1
    [[ "$host" =~ ^[a-zA-Z0-9.-]+$ ]] || return 1
    [[ "$host" != .* && "$host" != *. ]] || return 1

    IFS='.' read -r -a labels <<< "$host"

    for label in "${labels[@]}"; do
        [[ -n "$label" && ${#label} -le 63 ]] || return 1
        [[ "$label" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$ ]] || return 1
    done

    return 0
}

# Reject invalid targets before scanning.
if ! is_valid_ipv4 "$TARGET" && ! is_valid_hostname "$TARGET"; then
    error_exit "Invalid IP address or hostname: '$TARGET'."
fi

# Check required tools.
for tool in naabu nmap awk sort paste mktemp mkdir dirname basename; do
    command -v "$tool" >/dev/null 2>&1 || error_exit "Required tool '$tool' is not installed."
done

# Choose report filename.
if [[ -z "$REPORT" ]]; then
    REPORT="nmap_result_${TARGET//:/_}"
fi

# Prevent an empty or unsafe report filename.
[[ -n "$REPORT" && "$REPORT" != */ && "$REPORT" != -* ]] || error_exit "Invalid report filename."

REPORT_DIR=$(dirname -- "$REPORT")
REPORT_NAME=$(basename -- "$REPORT")

if ! mkdir -p -- "$REPORT_DIR"; then
    error_exit "Cannot create report directory '$REPORT_DIR'."
fi

REPORT_PATH="$REPORT_DIR/$REPORT_NAME"

# Refuse to overwrite an existing report.
if [[ -e "$REPORT_PATH" ]]; then
    error_exit "Report already exists: '$REPORT_PATH'. Choose another filename."
fi

# Temporary file for Naabu output.
TMP_FILE=$(mktemp) || error_exit "Cannot create temporary file."
trap 'rm -f -- "$TMP_FILE"' EXIT

echo "[*] Target: $TARGET"
echo "[*] Report: $REPORT_PATH"
echo "[*] Starting Naabu full TCP port scan..."

if ! naabu -host "$TARGET" -p - -silent > "$TMP_FILE"; then
    error_exit "Naabu failed for '$TARGET'. Check the target and network."
fi

# Extract and validate discovered ports.
PORTS=$(awk -F: '$NF ~ /^[0-9]+$/ && $NF >= 1 && $NF <= 65535 {print $NF}' "$TMP_FILE" | sort -nu | paste -sd ',' -)

if [[ -z "$PORTS" ]]; then
    error_exit "No open TCP ports found for '$TARGET'."
fi

echo "[+] Open ports: $PORTS"
echo "[*] Starting Nmap service detection and default scripts..."

# Nmap command kept on a single line.
if nmap -vvv -sV -sC --webxml -T4 -p "$PORTS" -oX "$REPORT_PATH" "$TARGET"; then
    echo "[+] Nmap scan completed."
    echo "[+] Report saved to: $REPORT_PATH"
else
    error_exit "Nmap scan failed for '$TARGET'."
fi
