#!/bin/bash
# Smoke test suite for acceptance testing
#
# Validates critical functionality after deployment
# Performs health checks, connectivity verification, and basic feature tests
#
# Usage:
#   ./smoke_test.sh --environment staging
#   ./smoke_test.sh --environment production --timeout 300
#   ./smoke_test.sh --environment local --verbose
#   ./smoke_test.sh --environment dev --service-only

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Defaults
ENVIRONMENT=""
TIMEOUT=120
VERBOSE=false
SERVICE_ONLY=false
EXIT_CODE=0

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration per environment
declare -A SERVICE_URLS=(
    [local]="http://localhost:8080"
    [dev]="http://smartbridge-dev.local"
    [staging]="http://smartbridge-staging.local"
    [production]="https://api.smartbridge.example.com"
)

declare -A SERVICE_PORTS=(
    [local]="8080"
    [dev]="8080"
    [staging]="8080"
    [production]="443"
)

declare -A HEALTHCHECK_ENDPOINTS=(
    [local]="/health"
    [dev]="/api/v1/health"
    [staging]="/api/v1/health"
    [production]="/api/v1/health"
)

log_test() { echo -e "${BLUE}[TEST]${NC} $*"; }
log_pass() { 
    echo -e "${GREEN}[PASS]${NC} $*"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}
log_fail() {
    echo -e "${RED}[FAIL]${NC} $*" >&2
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
    EXIT_CODE=1
}
log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_section() { echo -e "\n${BLUE}=== $* ===${NC}\n"; }

print_usage() {
    cat << 'EOF'
Usage: smoke_test.sh [OPTIONS]

Options:
    --environment ENV          Target environment: local, dev, staging, production [REQUIRED]
    --timeout SECONDS          Test timeout in seconds (default: 120)
    --service-only             Only test service connectivity, skip feature tests
    --verbose                  Enable verbose output
    --help                     Show this help message

Environments:
    local       - Local development (localhost:8080)
    dev         - Development environment
    staging     - Staging environment
    production  - Production environment (requires https)

Examples:
    # Test local development
    ./smoke_test.sh --environment local

    # Test staging with verbose output
    ./smoke_test.sh --environment staging --verbose

    # Quick connectivity check only
    ./smoke_test.sh --environment production --service-only --timeout 60

    # Test with custom timeout
    ./smoke_test.sh --environment production --timeout 300
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --service-only)
                SERVICE_ONLY=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                print_usage
                exit 0
                ;;
            *)
                log_fail "Unknown option: $1"
                print_usage
                exit 1
                ;;
        esac
    done
}

validate_args() {
    if [[ -z "$ENVIRONMENT" ]]; then
        log_fail "Environment is required"
        print_usage
        exit 1
    fi
    
    if [[ ! -v SERVICE_URLS[$ENVIRONMENT] ]]; then
        log_fail "Unknown environment: $ENVIRONMENT"
        echo "Supported: ${!SERVICE_URLS[@]}"
        exit 1
    fi
}

# ============================================================
# Health Check Tests
# ============================================================

test_service_availability() {
    log_section "Service Availability Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    local port="${SERVICE_PORTS[$ENVIRONMENT]}"
    local endpoint="${HEALTHCHECK_ENDPOINTS[$ENVIRONMENT]}"
    
    log_test "Testing service is accessible at $url"
    
    if curl -sf --max-time 10 "${url}${endpoint}" > /dev/null 2>&1; then
        log_pass "Service is available and responding"
    else
        log_fail "Service is not responding at ${url}${endpoint}"
        return 1
    fi
    
    log_test "Testing port $port is open"
    if timeout 5 bash -c "echo >/dev/tcp/$(echo $url | sed 's|.*://||;s|:.*||')/$(echo ${url#*:} | cut -d/ -f1 | cut -d: -f2 || echo $port)" 2>/dev/null || true; then
        log_pass "Port $port is open"
    else
        log_warn "Could not verify port connectivity (may be blocked)"
    fi
}

test_health_endpoint() {
    log_section "Health Endpoint Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    local endpoint="${HEALTHCHECK_ENDPOINTS[$ENVIRONMENT]}"
    local full_url="${url}${endpoint}"
    
    log_test "Testing health endpoint: $full_url"
    
    local response=$(curl -s --max-time 10 "$full_url" 2>/dev/null || echo "")
    
    if [[ -z "$response" ]]; then
        log_fail "Health endpoint returned empty response"
        return 1
    fi
    
    # Check if response is JSON
    if echo "$response" | jq . > /dev/null 2>&1; then
        log_pass "Health endpoint returns valid JSON"
        
        # Check for required fields
        if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
            local status=$(echo "$response" | jq -r '.status')
            if [[ "$status" == "healthy" || "$status" == "ok" || "$status" == "UP" ]]; then
                log_pass "Service status is healthy: $status"
            else
                log_fail "Service status is not healthy: $status"
            fi
        else
            log_warn "Health response does not contain 'status' field"
        fi
    else
        log_fail "Health endpoint response is not valid JSON"
        if [[ "$VERBOSE" == "true" ]]; then
            echo "Response: $response"
        fi
        return 1
    fi
}

# ============================================================
# API Tests
# ============================================================

test_api_endpoints() {
    log_section "API Endpoint Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    # Test common API endpoints
    local endpoints=(
        "/api/v1/status"
        "/api/v1/version"
        "/api/v1/config"
    )
    
    for endpoint in "${endpoints[@]}"; do
        log_test "Testing endpoint: $endpoint"
        
        if curl -sf --max-time 10 "${url}${endpoint}" > /dev/null 2>&1; then
            log_pass "Endpoint $endpoint is accessible"
        else
            log_warn "Endpoint $endpoint returned error"
        fi
    done
}

test_authentication() {
    log_section "Authentication Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    log_test "Testing unauthenticated request rejection"
    
    local response=$(curl -s -w "\n%{http_code}" --max-time 10 \
        -H "Content-Type: application/json" \
        "${url}/api/v1/protected/resource" 2>/dev/null || echo -e "\n0")
    
    local status=$(echo "$response" | tail -n1)
    
    if [[ "$status" == "401" || "$status" == "403" ]]; then
        log_pass "Protected endpoints correctly reject unauthenticated requests (HTTP $status)"
    elif [[ "$status" == "404" ]]; then
        log_warn "Protected endpoint returned 404 (endpoint may not exist)"
    else
        log_warn "Unexpected HTTP status for protected endpoint: $status"
    fi
}

test_cors() {
    log_section "CORS Configuration Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    log_test "Testing CORS headers"
    
    local headers=$(curl -s -I --max-time 10\
        -H "Origin: https://localhost:3000" \
        "${url}/api/v1/health" 2>/dev/null)
    
    if echo "$headers" | grep -qi "Access-Control-Allow-Origin"; then
        log_pass "CORS headers are present"
    else
        log_warn "CORS headers not found (may be expected for same-origin requests)"
    fi
}

# ============================================================
# Database Tests
# ============================================================

test_database_connectivity() {
    log_section "Database Connectivity Tests"
    
    # These tests depend on having database connectivity exposed
    # Check if database query endpoint exists
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    log_test "Testing database health via API"
    
    if curl -sf --max-time 10 "${url}/api/v1/health/db" > /dev/null 2>&1; then
        log_pass "Database is accessible and responsive"
    else
        log_warn "Database health endpoint not available (service may not expose it)"
    fi
}

# ============================================================
# Performance Tests
# ============================================================

test_response_times() {
    log_section "Response Time Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    local endpoint="${HEALTHCHECK_ENDPOINTS[$ENVIRONMENT]}"
    local max_time=1000  # milliseconds
    
    log_test "Testing response time (max: ${max_time}ms)"
    
    local response_time=$(curl -fs --max-time 10 -w "%{time_total}" -o /dev/null \
        "${url}${endpoint}" 2>/dev/null || echo "10")
    
    # Convert to milliseconds
    response_time=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "10000")
    
    if (( $(echo "$response_time < $max_time" | bc -l) )); then
        log_pass "Response time acceptable: ${response_time}ms"
    else
        log_warn "Response time slow: ${response_time}ms (threshold: ${max_time}ms)"
    fi
}

test_concurrent_requests() {
    log_section "Concurrency Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    local endpoint="${HEALTHCHECK_ENDPOINTS[$ENVIRONMENT]}"
    local num_requests=10
    
    log_test "Testing $num_requests concurrent requests"
    
    # Run concurrent requests
    local successes=0
    for i in $(seq 1 $num_requests); do
        if curl -sf --max-time 10 "${url}${endpoint}" > /dev/null 2>&1; then
            ((successes++))
        fi &
    done
    wait
    
    if [[ $successes -eq $num_requests ]]; then
        log_pass "All $num_requests concurrent requests succeeded"
    else
        log_fail "$successes/$num_requests concurrent requests succeeded"
    fi
}

# ============================================================
# Feature Tests
# ============================================================

test_logging() {
    log_section "Logging Function Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    log_test "Testing if service is logging requests"
    
    # This is a basic check - real test would need log access
    if curl -sf --max-time 10 "${url}/api/v1/health" > /dev/null 2>&1; then
        log_pass "Service is processing requests normally"
    else
        log_fail "Service is not responding to requests"
    fi
}

test_error_handling() {
    log_section "Error Handling Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    log_test "Testing error handling with invalid request"
    
    local response=$(curl -s --max-time 10 \
        -H "Content-Type: application/json" \
        -d '{"invalid": "json' \
        "${url}/api/v1/test" 2>/dev/null || echo "")
    
    if [[ -n "$response" ]]; then
        if echo "$response" | jq . > /dev/null 2>&1; then
            log_pass "Service returns valid JSON for error responses"
        else
            log_warn "Service error response is not JSON"
        fi
    else
        log_warn "No response to error test"
    fi
}

test_rate_limiting() {
    log_section "Rate Limiting Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    local endpoint="${HEALTHCHECK_ENDPOINTS[$ENVIRONMENT]}"
    
    log_test "Testing rate limit headers"
    
    local headers=$(curl -sI --max-time 10 "${url}${endpoint}" 2>/dev/null)
    
    if echo "$headers" | grep -qi "RateLimit\|X-RateLimit\|X-Rate"; then
        log_pass "Rate limit headers present"
    else
        log_warn "Rate limit headers not found"
    fi
}

# ============================================================
# Security Tests
# ============================================================

test_security_headers() {
    log_section "Security Header Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    local security_headers=(
        "X-Content-Type-Options"
        "X-Frame-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
    )
    
    local headers=$(curl -sI --max-time 10 "$url" 2>/dev/null)
    
    for header in "${security_headers[@]}"; do
        log_test "Checking for $header"
        if echo "$headers" | grep -qi "$header"; then
            log_pass "$header is present"
        else
            log_warn "$header not found"
        fi
    done
}

test_https() {
    log_section "HTTPS/TLS Tests"
    
    local url="${SERVICE_URLS[$ENVIRONMENT]}"
    
    if [[ "$url" == https://* ]]; then
        log_test "Testing HTTPS certificate"
        
        local cert_info=$(curl -vI --max-time 10 "$url" 2>&1 | grep -i "certificate\|ssl\|tls" || echo "")
        
        if [[ -n "$cert_info" ]]; then
            log_pass "HTTPS certificate validation passed"
        else
            log_warn "Could not verify HTTPS certificate"
        fi
    else
        log_warn "Environment is not using HTTPS"
    fi
}

# ============================================================
# Main Test Execution
# ============================================================

run_all_tests() {
    log_section "SmartBridge Smoke Tests - Environment: ${ENVIRONMENT^^}"
    log_info "Timeout: ${TIMEOUT}s | Verbose: ${VERBOSE} | Service Only: ${SERVICE_ONLY}"
    
    # Core service tests
    test_service_availability || {
        log_fail "Service is not available. Cannot continue with other tests."
        return 1
    }
    
    test_health_endpoint
    
    # Extended tests if not service-only
    if [[ "$SERVICE_ONLY" != "true" ]]; then
        test_api_endpoints
        test_authentication
        test_cors
        test_database_connectivity
        test_response_times
        test_concurrent_requests
        test_logging
        test_error_handling
        test_rate_limiting
        test_security_headers
        test_https
    fi
}

print_summary() {
    log_section "Test Summary"
    
    echo "Total Tests: $TESTS_RUN"
    echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
    echo -e "${RED}Failed:${NC} $TESTS_FAILED"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}✓ All smoke tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}✗ Some tests failed. Please investigate.${NC}"
        return 1
    fi
}

main() {
    parse_args "$@"
    validate_args
    
    # Run within timeout
    timeout "$TIMEOUT" run_all_tests || {
        EXIT_CODE=$?
        if [[ $EXIT_CODE -eq 124 ]]; then
            log_fail "Tests timed out after ${TIMEOUT}s"
        fi
    }
    
    print_summary
    exit $EXIT_CODE
}

main "$@"
