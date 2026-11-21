// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored
// Fixture-ID: cpp.asan.heap-use-after-free.v1
// Expected: ASAN_FINDING
// Failure class: heap use-after-free. Deliberately invalid test code.

int main() {
    int* value = new int(73);
    volatile int* stale = value;
    delete value;
    volatile int observed = *stale;
    (void)observed;
    return 0;
}
