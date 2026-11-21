// SPDX-License-Identifier: MIT
// Origin: independently authored BODY OF SECRETS verification fixture.
#include <type_traits>
#include <utility>

template <typename T>
auto forward_probe(T&& value) noexcept -> decltype(std::forward<T>(value)) {
    return std::forward<T>(value);
}

static_assert(std::is_same<decltype(forward_probe(std::declval<int&>())), int&>::value,
              "lvalues must remain lvalue references");
static_assert(std::is_same<decltype(forward_probe(std::declval<int&&>())), int&&>::value,
              "rvalues must remain rvalue references");
static_assert(std::is_same<decltype(forward_probe(std::declval<const int&>())), const int&>::value,
              "const lvalues must retain const lvalue references");
static_assert(std::is_same<decltype(forward_probe(std::declval<const int&&>())), const int&&>::value,
              "const rvalues must retain const rvalue references");

int main() { return 0; }
