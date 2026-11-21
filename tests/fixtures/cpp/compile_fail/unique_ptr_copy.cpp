// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored
// Fixture-ID: cpp.compile.unique-ptr-copy.v1
// Expected: COMPILE_FAIL
// Failure class: copying exclusive ownership (deleted copy constructor).
// Test-only source. Never use as a remediation example.

#include <memory>

int main() {
    std::unique_ptr<int> owner(new int(42));
    std::unique_ptr<int> duplicate(owner);
    return duplicate ? 0 : 1;
}
