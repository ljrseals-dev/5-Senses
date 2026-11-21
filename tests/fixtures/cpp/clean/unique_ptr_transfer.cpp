// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored
// Fixture-ID: cpp.clean.unique-ptr-transfer.v1
// Expected: CLEAN
// Control: valid exclusive-ownership transfer.

#include <memory>
#include <utility>

int main() {
    std::unique_ptr<int> original(new int(73));
    std::unique_ptr<int> recipient(std::move(original));
    if (original) {
        return 1;
    }
    return recipient && *recipient == 73 ? 0 : 2;
}
