// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored test fixture
// Fixture-ID: cpp.asan.heap-use-after-free.v1
// Purpose: Trigger a deterministic AddressSanitizer heap-use-after-free.
// Expected: Compile succeeds; execution fails under ASan.
// Not production code. Never use as a remediation example.

#include <cstdlib>
#include <cstring>

int main() {
    // Allocate a small heap buffer
    char* buf = static_cast<char*>(std::malloc(16));
    if (!buf) {
        return 1;
    }

    // Write something into it so the allocation is "used"
    std::memset(buf, 'A', 16);

    // Free the buffer
    std::free(buf);

    // Use-after-free: write to the already-freed memory
    // This is the intentional bug that ASan should catch.
    buf[0] = 'X';

    return 0;
}
