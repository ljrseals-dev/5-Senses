// SPDX-License-Identifier: MIT
// Fixture-Origin: BODY-OF-SECRETS independently authored
// Fixture-ID: cpp.link.pure-virtual-dtor.v1
// Expected: LINK_FAIL under C++98
// Failure class: pure virtual destructor declared but not defined.
// Deliberately uses C++98 syntax so the failure occurs at link time.

struct Interface {
    virtual ~Interface() = 0;
};

struct Implementation : Interface {
    virtual ~Implementation() {}
};

int main() {
    Implementation instance;
    return 0;
}
