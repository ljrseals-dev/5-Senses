// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored
// Fixture-ID: cpp.ubsan.signed-overflow.v1
// Expected: UBSAN_FINDING
// Failure class: signed integer overflow. Deliberately invalid test code.

#include <climits>

int main() {
    volatile int maximum = INT_MAX;
    volatile int result = maximum + 1;
    (void)result;
    return 0;
}
