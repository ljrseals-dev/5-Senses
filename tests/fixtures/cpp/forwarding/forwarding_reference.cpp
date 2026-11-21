// SPDX-License-Identifier: MIT
// Origin: independently authored BODY OF SECRETS verification fixture.
#include <utility>

int category(int&) { return 1; }
int category(int&&) { return 2; }

template <typename T>
int relay(T&& value) {
    return category(std::forward<T>(value));
}

int main() {
    int lvalue = 0;
    if (relay(lvalue) != 1) return 1;
    if (relay(0) != 2) return 2;
    return 0;
}
