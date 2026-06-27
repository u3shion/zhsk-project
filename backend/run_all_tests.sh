#!/bin/bash

SERVICES=("users" "meters" "announcements" "chat" "notifications")
FAILED_SERVICES=0
PASSED_SERVICES=0
TOTAL_TESTS_PASSED=0
TOTAL_TESTS_FAILED=0

GREEN='\033[92m'
RED='\033[91m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
END='\033[0m'

echo -e "${BLUE}${BOLD}=========================================${END}"
echo -e "${BOLD}Running all backend tests...${END}"
echo -e "${BLUE}${BOLD}=========================================${END}"
echo ""

for service in "${SERVICES[@]}"; do
    echo -e "${BLUE}${BOLD}=========================================${END}"
    echo -e "${BOLD}Testing ${service} service...${END}"
    echo -e "${BLUE}${BOLD}=========================================${END}"
    echo ""

    if [ ! -d "$service" ]; then
        echo -e "${RED}❌ Directory $service not found, skipping...${END}"
        continue
    fi

    cd "$service" || exit 1

    if [ ! -d "tests" ]; then
        echo -e "${YELLOW}⚠️  No tests directory found in $service, skipping...${END}"
        cd ..
        continue
    fi

    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}⚠️  No venv found in $service. Run ./install_test_deps.sh first${END}"
        cd ..
        FAILED_SERVICES=$((FAILED_SERVICES + 1))
        continue
    fi

    source venv/bin/activate

    TEMP_OUTPUT=$(mktemp)

    pytest -v --tb=line 2>&1 | tee "$TEMP_OUTPUT"

    pytest_exit=${PIPESTATUS[0]}

    service_passed=0
    service_failed=0

    while IFS= read -r line; do
        if [[ $line =~ tests/.+::.+::.+[[:space:]]PASSED ]]; then
            test_method=$(echo "$line" | sed -E 's/.*::([^[:space:]]+)[[:space:]]+PASSED.*/\1/')
            readable_name=$(echo "$test_method" | sed 's/test_//' | sed 's/_/ /g')
            echo -e "  ${GREEN}✅ [PASSED]${END} ${readable_name}"
            service_passed=$((service_passed + 1))

        elif [[ $line =~ tests/.+::.+::.+[[:space:]]FAILED ]]; then
            test_method=$(echo "$line" | sed -E 's/.*::([^[:space:]]+)[[:space:]]+FAILED.*/\1/')
            readable_name=$(echo "$test_method" | sed 's/test_//' | sed 's/_/ /g')
            echo -e "  ${RED}❌ [FAILED]${END} ${readable_name}"
            service_failed=$((service_failed + 1))

            in_error_section=false
            while IFS= read -r error_line; do
                if [[ $error_line =~ ^FAILED.+$test_method ]]; then
                    in_error_section=true
                    continue
                fi

                if [[ $in_error_section == true ]]; then
                    if [[ $error_line =~ (assert|AssertionError|AssertionError:) ]]; then
                        cleaned=$(echo "$error_line" | sed 's/^[[:space:]]*//')
                        echo -e "    ${RED}→ ${cleaned}${END}"
                    fi

                    if [[ $error_line =~ ^(PASSED|FAILED|=====) ]]; then
                        break
                    fi
                fi
            done < "$TEMP_OUTPUT"
        fi
    done < "$TEMP_OUTPUT"

    TOTAL_TESTS_PASSED=$((TOTAL_TESTS_PASSED + service_passed))
    TOTAL_TESTS_FAILED=$((TOTAL_TESTS_FAILED + service_failed))

    rm -f "$TEMP_OUTPUT"
    deactivate

    echo ""
    if [ $pytest_exit -eq 0 ]; then
        echo -e "${GREEN}✅ ${service}: ${service_passed} tests passed${END}"
        PASSED_SERVICES=$((PASSED_SERVICES + 1))
    else
        echo -e "${RED}❌ ${service}: ${service_passed} passed, ${service_failed} failed${END}"
        FAILED_SERVICES=$((FAILED_SERVICES + 1))
    fi

    cd ..
    echo ""
done

echo -e "${BLUE}${BOLD}=========================================${END}"
echo -e "${BOLD}Test Summary${END}"
echo -e "${BLUE}${BOLD}=========================================${END}"
echo -e "Services tested: ${#SERVICES[@]}"
echo -e "${GREEN}Services passed: $PASSED_SERVICES${END}"
echo -e "${RED}Services failed: $FAILED_SERVICES${END}"
echo ""
echo -e "${GREEN}Total tests passed: $TOTAL_TESTS_PASSED${END}"
echo -e "${RED}Total tests failed: $TOTAL_TESTS_FAILED${END}"
echo -e "${BLUE}${BOLD}=========================================${END}"

if [ $FAILED_SERVICES -gt 0 ] || [ $TOTAL_TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Some tests failed${END}"
    exit 1
else
    echo -e "${GREEN}✅ All tests passed${END}"
    exit 0
fi
