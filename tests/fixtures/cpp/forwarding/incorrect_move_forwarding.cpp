// SPDX-License-Identifier: MIT
// Origin: independently authored BODY OF SECRETS negative-control fixture.
#include <utility>

int category(int&) { return 1; }
int category(int&&) { return 2; }

template <typename T>
int broken_forward(T&& value) {
    // Deliberate bug: std::move discards the caller's lvalue/rvalue category.
    return category(std::move(value));
}

int main() {
    int lvalue = 0;
    // The fixture succeeds only when the bug is reproduced: lvalue is misrouted as rvalue.
    return broken_forward(lvalue) == 2 ? 0 : 1;
}
